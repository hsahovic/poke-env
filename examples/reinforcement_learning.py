from typing import Any, Awaitable

import numpy as np
import numpy.typing as npt
import supersuit as ss
import torch
from gymnasium import Env
from gymnasium.spaces import Box, Space
from stable_baselines3 import PPO
from stable_baselines3.common.distributions import CategoricalDistribution
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3.common.type_aliases import PyTorchObs
from stable_baselines3.common.vec_env import SubprocVecEnv

from poke_env.battle import AbstractBattle, Battle
from poke_env.data import GenData
from poke_env.environment import SingleAgentWrapper, SinglesEnv
from poke_env.player import (
    BattleOrder,
    DefaultBattleOrder,
    MaxBasePowerPlayer,
    Player,
    RandomPlayer,
    SimpleHeuristicsPlayer,
    background_cross_evaluate,
)
from poke_env.ps_client import ServerConfiguration

ACT_LEN = 26


class MaskedActorCriticPolicy(ActorCriticPolicy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, features_extractor_class=FeaturesExtractor)

    def forward(
        self, obs: torch.Tensor, deterministic: bool = False
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        action_logits, value_logits = self.get_logits(obs)
        distribution = self.get_dist_from_logits(obs, action_logits)
        actions = distribution.get_actions(deterministic=deterministic)
        log_prob = distribution.log_prob(actions)
        actions = actions.reshape((-1, *self.action_space.shape))  # type: ignore[misc]
        return actions, value_logits, log_prob

    def evaluate_actions(
        self, obs: PyTorchObs, actions: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]:
        assert isinstance(obs, torch.Tensor)
        action_logits, value_logits = self.get_logits(obs)
        distribution = self.get_dist_from_logits(obs, action_logits)
        log_prob = distribution.log_prob(actions)
        entropy = distribution.entropy()
        return value_logits, log_prob, entropy

    def get_logits(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.extract_features(obs)
        if self.share_features_extractor:
            latent_pi, latent_vf = self.mlp_extractor(features)
        else:
            pi_features, vf_features = features
            latent_pi = self.mlp_extractor.forward_actor(pi_features)
            latent_vf = self.mlp_extractor.forward_critic(vf_features)
        action_logits = self.action_net(latent_pi)
        value_logits = self.value_net(latent_vf)
        return action_logits, value_logits

    def get_dist_from_logits(
        self, obs: torch.Tensor, action_logits: torch.Tensor
    ) -> CategoricalDistribution:
        mask = obs[:, :ACT_LEN]
        mask = torch.where(mask == 1, 0, float("-inf"))
        distribution = self.action_dist.proba_distribution(action_logits + mask)
        assert isinstance(distribution, CategoricalDistribution)
        return distribution


class FeaturesExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space: Space[Any]):
        super().__init__(observation_space, features_dim=10)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x[:, ACT_LEN:]


class PolicyPlayer(Player):
    policy: ActorCriticPolicy | None

    def __init__(
        self, policy: ActorCriticPolicy | None = None, *args: Any, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.policy = policy

    def choose_move(
        self, battle: AbstractBattle
    ) -> BattleOrder | Awaitable[BattleOrder]:
        assert isinstance(battle, Battle)
        assert self.policy is not None
        if battle._wait:
            return DefaultBattleOrder()
        obs = self.embed_battle(battle)
        with torch.no_grad():
            obs_tensor = torch.as_tensor(obs, device=self.policy.device).unsqueeze(0)
            action, _, _ = self.policy.forward(obs_tensor)
        action = action.cpu().numpy()[0]
        return SinglesEnv.action_to_order(action, battle)

    @staticmethod
    def embed_battle(battle: AbstractBattle) -> npt.NDArray[np.float32]:
        assert isinstance(battle, Battle)
        mask = PolicyPlayer.get_action_mask(battle)
        # -1 indicates that the move does not have a base power
        # or is not available
        moves_base_power = -np.ones(4)
        moves_dmg_multiplier = np.ones(4)
        for i, move in enumerate(battle.available_moves):
            # Simple rescaling to facilitate learning
            moves_base_power[i] = move.base_power / 100
            if battle.opponent_active_pokemon is not None:
                moves_dmg_multiplier[i] = move.type.damage_multiplier(
                    battle.opponent_active_pokemon.type_1,
                    battle.opponent_active_pokemon.type_2,
                    type_chart=GenData.from_gen(battle.gen).type_chart,
                )
        # We count how many pokemons have fainted in each team
        fainted_mon_team = len([mon for mon in battle.team.values() if mon.fainted]) / 6
        fainted_mon_opponent = (
            len([mon for mon in battle.opponent_team.values() if mon.fainted]) / 6
        )
        # Final vector with a mask and 10 feature components
        return np.concatenate(
            [
                mask,
                moves_base_power,
                moves_dmg_multiplier,
                [fainted_mon_team, fainted_mon_opponent],
            ]
        )

    @staticmethod
    def get_action_mask(battle: Battle) -> list[int]:
        switch_space = [
            i
            for i, pokemon in enumerate(battle.team.values())
            if not battle.trapped
            and pokemon.base_species
            in [p.base_species for p in battle.available_switches]
        ]
        if battle._wait:
            actions = [0]
        elif battle.active_pokemon is None:
            actions = switch_space
        else:
            move_space = [
                i + 6
                for i, move in enumerate(battle.active_pokemon.moves.values())
                if move.id in [m.id for m in battle.available_moves]
            ]
            mega_space = [i + 4 for i in move_space if battle.can_mega_evolve]
            zmove_space = [
                i + 6 + 8
                for i, move in enumerate(battle.active_pokemon.moves.values())
                if move.id in [m.id for m in battle.active_pokemon.available_z_moves]
                and battle.can_z_move
            ]
            dynamax_space = [i + 12 for i in move_space if battle.can_dynamax]
            tera_space = [i + 16 for i in move_space if battle.can_tera]
            if (
                not move_space
                and len(battle.available_moves) == 1
                and battle.available_moves[0].id in ["struggle", "recharge"]
            ):
                move_space = [6]
            actions = (
                switch_space
                + move_space
                + mega_space
                + zmove_space
                + dynamax_space
                + tera_space
            )
        action_mask = [int(i in actions) for i in range(ACT_LEN)]
        return action_mask


class ExampleEnv(SinglesEnv[npt.NDArray[np.float32]]):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metadata = {"name": "showdown_v1", "render_modes": ["human"]}
        self.render_mode: str | None = None
        self.observation_spaces = {
            agent: Box(-1, 4, shape=(10 + ACT_LEN,), dtype=np.float32)
            for agent in self.possible_agents
        }

    @classmethod
    def create_env(
        cls,
        battle_format: str,
        num_envs: int,
        log_level: int,
        port: int,
        is_single_agent: bool,
    ) -> Env:
        env = cls(
            server_configuration=ServerConfiguration(
                f"ws://localhost:{port}/showdown/websocket",
                "https://play.pokemonshowdown.com/action.php?",
            ),
            battle_format=battle_format,
            log_level=log_level,
            open_timeout=None,
        )
        if is_single_agent:
            opponent = SimpleHeuristicsPlayer(start_listening=False)
            env = SingleAgentWrapper(env, opponent)
            env = Monitor(env)
            return env
        else:
            env = ss.pettingzoo_env_to_vec_env_v1(env)
            env = ss.concat_vec_envs_v1(
                env,
                num_vec_envs=num_envs,
                num_cpus=num_envs,
                base_class="stable_baselines3",
            )
            return env

    def calc_reward(self, battle) -> float:
        return self.reward_computing_helper(
            battle, fainted_value=2.0, hp_value=1.0, victory_value=30.0
        )

    def embed_battle(self, battle: AbstractBattle):
        return PolicyPlayer.embed_battle(battle)


def train(is_single_agent: bool):
    battle_format = "gen9randombattle"
    num_envs = 2
    log_level = 40
    port = 8000
    device = "cpu"
    env = (
        SubprocVecEnv(
            [
                lambda: ExampleEnv.create_env(
                    battle_format, num_envs, log_level, port, is_single_agent
                )
                for _ in range(num_envs)
            ]
        )
        if is_single_agent
        else ExampleEnv.create_env(
            battle_format, num_envs, log_level, port, is_single_agent
        )
    )
    ppo = PPO(
        MaskedActorCriticPolicy,
        env,
        learning_rate=1e-5,
        n_steps=(3072 // num_envs if is_single_agent else 3072 // (2 * num_envs)),
        batch_size=64,
        gamma=1,
        ent_coef=0.01,
        device=device,
    )
    ppo.learn(100_000)
    env.close()


def evaluate(ppo: PPO):
    battle_format = "gen9randombattle"
    n_challenges = 100
    server_configuration = ServerConfiguration(
        "ws://localhost:8000/showdown/websocket",
        "https://play.pokemonshowdown.com/action.php?",
    )

    players = [
        PolicyPlayer(
            policy=ppo.policy,
            battle_format=battle_format,
            server_configuration=server_configuration,
            max_concurrent_battles=10,
        ),
        RandomPlayer(
            battle_format=battle_format,
            server_configuration=server_configuration,
            max_concurrent_battles=10,
        ),
        MaxBasePowerPlayer(
            battle_format=battle_format,
            server_configuration=server_configuration,
            max_concurrent_battles=10,
        ),
        SimpleHeuristicsPlayer(
            battle_format=battle_format,
            server_configuration=server_configuration,
            max_concurrent_battles=10,
        ),
    ]

    cross_evaluation = background_cross_evaluate(players, n_challenges).result()

    table = [["-"] + [p.username for p in players]]
    for p_1, results in cross_evaluation.items():
        table.append([p_1] + [str(cross_evaluation[p_1][p_2]) for p_2 in results])
    for row in table:
        print("\t".join(row))


if __name__ == "__main__":
    train(is_single_agent=False)
    train(is_single_agent=True)
