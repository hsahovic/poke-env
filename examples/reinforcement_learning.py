import asyncio
from typing import Any, Awaitable

import numpy as np
import numpy.typing as npt
import torch
from gymnasium.spaces import Box, Space
from stable_baselines3 import PPO
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
)
from poke_env.ps_client import ServerConfiguration

N_FEATURES = 12
ACT_LEN = 26


class MaskedActorCriticPolicy(ActorCriticPolicy):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            net_arch=[64, 64],
            features_extractor_class=FeaturesExtractor,
        )

    def forward(self, obs: torch.Tensor, deterministic: bool = False):
        self._current_obs = obs
        return super().forward(obs, deterministic)

    def evaluate_actions(self, obs: PyTorchObs, actions: torch.Tensor):
        assert isinstance(obs, torch.Tensor)
        self._current_obs = obs
        return super().evaluate_actions(obs, actions)

    def _get_action_dist_from_latent(self, latent_pi: torch.Tensor):
        action_logits = self.action_net(latent_pi)
        mask = self._current_obs[:, :ACT_LEN]
        mask = torch.where(mask == 1, 0, float("-inf"))
        return self.action_dist.proba_distribution(action_logits + mask)


class FeaturesExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space: Space[Any]):
        super().__init__(observation_space, features_dim=N_FEATURES)

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
        if battle.wait:
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
        moves_base_power = -np.ones(4)
        moves_dmg_multiplier = np.ones(4)
        for i, move in enumerate(battle.available_moves):
            moves_base_power[i] = move.base_power / 100
            if battle.opponent_active_pokemon is not None:
                moves_dmg_multiplier[i] = move.type.damage_multiplier(
                    battle.opponent_active_pokemon.type_1,
                    battle.opponent_active_pokemon.type_2,
                    type_chart=GenData.from_gen(battle.gen).type_chart,
                )
        fainted_mon_team = len([mon for mon in battle.team.values() if mon.fainted]) / 6
        fainted_mon_opponent = (
            len([mon for mon in battle.opponent_team.values() if mon.fainted]) / 6
        )
        our_hp = (
            battle.active_pokemon.current_hp_fraction if battle.active_pokemon else 0.0
        )
        opp_hp = (
            battle.opponent_active_pokemon.current_hp_fraction
            if battle.opponent_active_pokemon
            else 0.0
        )
        return np.concatenate(
            [
                mask,
                moves_base_power,
                moves_dmg_multiplier,
                [fainted_mon_team, fainted_mon_opponent],
                [our_hp, opp_hp],
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
        if battle.wait:
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
            agent: Box(-1, 4, shape=(N_FEATURES + ACT_LEN,), dtype=np.float32)
            for agent in self.possible_agents
        }

    @classmethod
    def create_env(cls, battle_format: str, log_level: int, port: int) -> Monitor:
        env = cls(
            server_configuration=ServerConfiguration(
                f"ws://localhost:{port}/showdown/websocket",
                "https://play.pokemonshowdown.com/action.php?",
            ),
            battle_format=battle_format,
            log_level=log_level,
            open_timeout=None,
        )
        opponent = SimpleHeuristicsPlayer(start_listening=False)
        return Monitor(SingleAgentWrapper(env, opponent))

    def calc_reward(self, battle) -> float:
        return self.reward_computing_helper(
            battle,
            fainted_value=2.0,
            hp_value=1.0,
            status_value=0.5,
            victory_value=30.0,
        )

    def embed_battle(self, battle: AbstractBattle):
        return PolicyPlayer.embed_battle(battle)


def train(
    battle_format: str = "gen9randombattle",
    num_envs: int = 2,
    log_level: int = 40,
    port: int = 8000,
    device: str = "cpu",
):
    # setup
    env = SubprocVecEnv(
        [
            lambda: ExampleEnv.create_env(battle_format, log_level, port)
            for _ in range(num_envs)
        ]
    )
    ppo = PPO(
        MaskedActorCriticPolicy,
        env,
        learning_rate=3e-4,
        n_steps=3072 // num_envs,
        batch_size=128,
        gamma=0.99,
        ent_coef=0.01,
        device=device,
    )

    # train
    ppo.learn(98_304)
    env.close()

    # evaluate
    agent = PolicyPlayer(
        policy=ppo.policy,
        battle_format=battle_format,
        server_configuration=ServerConfiguration(
            f"ws://localhost:{port}/showdown/websocket",
            "https://play.pokemonshowdown.com/action.php?",
        ),
        max_concurrent_battles=10,
    )
    opponents: list[Player] = [
        RandomPlayer(
            battle_format=battle_format,
            server_configuration=ServerConfiguration(
                f"ws://localhost:{port}/showdown/websocket",
                "https://play.pokemonshowdown.com/action.php?",
            ),
            max_concurrent_battles=10,
        ),
        MaxBasePowerPlayer(
            battle_format=battle_format,
            server_configuration=ServerConfiguration(
                f"ws://localhost:{port}/showdown/websocket",
                "https://play.pokemonshowdown.com/action.php?",
            ),
            max_concurrent_battles=10,
        ),
        SimpleHeuristicsPlayer(
            battle_format=battle_format,
            server_configuration=ServerConfiguration(
                f"ws://localhost:{port}/showdown/websocket",
                "https://play.pokemonshowdown.com/action.php?",
            ),
            max_concurrent_battles=10,
        ),
    ]
    asyncio.run(agent.battle_against(*opponents, n_battles=100))
    print("--- Win rates vs bots ---")
    for opp in opponents:
        win_rate = round(100 * opp.n_lost_battles / opp.n_finished_battles)
        print(f"{opp.username}: {win_rate}%")


if __name__ == "__main__":
    train()
