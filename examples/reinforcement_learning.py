from typing import Any, Dict, Optional

import numpy as np
import numpy.typing as npt
import torch
import torch.nn as nn
from gymnasium.spaces import Box, Discrete, Space
from ray.rllib.algorithms import PPOConfig
from ray.rllib.core import Columns
from ray.rllib.core.rl_module import RLModuleSpec
from ray.rllib.core.rl_module.apis.value_function_api import ValueFunctionAPI
from ray.rllib.core.rl_module.torch import TorchRLModule
from ray.rllib.env import ParallelPettingZooEnv
from ray.tune.registry import register_env

from poke_env.environment import AbstractBattle, Battle
from poke_env.player import RandomPlayer, SingleAgentWrapper, SinglesEnv


class ExampleEnv(SinglesEnv[npt.NDArray[np.float32]]):
    LOW = [-1, -1, -1, -1, 0, 0, 0, 0, 0, 0]
    HIGH = [3, 3, 3, 3, 4, 4, 4, 4, 1, 1]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {
            agent: Box(
                np.array(self.LOW, dtype=np.float32),
                np.array(self.HIGH, dtype=np.float32),
                dtype=np.float32,
            )
            for agent in self.possible_agents
        }

    @classmethod
    def create_multi_agent_env(cls, config: Dict[str, Any]) -> ParallelPettingZooEnv:
        env = cls(
            battle_format=config["battle_format"],
            log_level=25,
            open_timeout=None,
            strict=False,
        )
        return ParallelPettingZooEnv(env)

    @classmethod
    def create_single_agent_env(cls, config: Dict[str, Any]) -> SingleAgentWrapper:
        env = cls(
            battle_format=config["battle_format"],
            log_level=25,
            open_timeout=None,
            strict=False,
        )
        opponent = RandomPlayer()
        return SingleAgentWrapper(env, opponent)

    def calc_reward(self, battle) -> float:
        return self.reward_computing_helper(
            battle, fainted_value=2.0, hp_value=1.0, victory_value=30.0
        )

    def embed_battle(self, battle: AbstractBattle):
        assert isinstance(battle, Battle)
        # -1 indicates that the move does not have a base power
        # or is not available
        moves_base_power = -np.ones(4)
        moves_dmg_multiplier = np.ones(4)
        for i, move in enumerate(battle.available_moves):
            moves_base_power[i] = (
                move.base_power / 100
            )  # Simple rescaling to facilitate learning
            if battle.opponent_active_pokemon is not None:
                moves_dmg_multiplier[i] = move.type.damage_multiplier(
                    battle.opponent_active_pokemon.type_1,
                    battle.opponent_active_pokemon.type_2,
                    type_chart=battle.opponent_active_pokemon._data.type_chart,
                )

        # We count how many pokemons have fainted in each team
        fainted_mon_team = len([mon for mon in battle.team.values() if mon.fainted]) / 6
        fainted_mon_opponent = (
            len([mon for mon in battle.opponent_team.values() if mon.fainted]) / 6
        )

        # Final vector with 10 components
        final_vector = np.concatenate(
            [
                moves_base_power,
                moves_dmg_multiplier,
                [fainted_mon_team, fainted_mon_opponent],
            ]
        )
        return np.float32(final_vector)


class ActorCriticModule(TorchRLModule, ValueFunctionAPI):
    def __init__(
        self,
        observation_space: Space,
        action_space: Space,
        inference_only: bool,
        model_config: Dict[str, Any],
        catalog_class: Any,
    ):
        super().__init__(
            observation_space=observation_space,
            action_space=action_space,
            inference_only=inference_only,
            model_config=model_config,
            catalog_class=catalog_class,
        )
        self.model = nn.Linear(10, 100)
        self.actor = nn.Linear(100, 26)
        self.critic = nn.Linear(100, 1)

    def _forward(self, batch: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        obs = batch[Columns.OBS]
        embeddings = self.model(obs)
        logits = self.actor(embeddings)
        return {Columns.EMBEDDINGS: embeddings, Columns.ACTION_DIST_INPUTS: logits}

    def compute_values(
        self, batch: Dict[str, Any], embeddings: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        if embeddings is None:
            embeddings = self.model(batch[Columns.OBS])
        return self.critic(embeddings).squeeze(-1)


def single_agent_train():
    register_env("showdown", ExampleEnv.create_single_agent_env)
    config = PPOConfig()
    config = config.environment(
        "showdown",
        env_config={"battle_format": "gen9randombattle"},
        disable_env_checking=True,
    )
    config = config.learners(num_learners=1)
    config = config.rl_module(
        rl_module_spec=RLModuleSpec(
            module_class=ActorCriticModule,
            observation_space=Box(
                np.array(ExampleEnv.LOW, dtype=np.float32),
                np.array(ExampleEnv.HIGH, dtype=np.float32),
                dtype=np.float32,
            ),
            action_space=Discrete(26),
            model_config={},
        )
    )
    config = config.training(
        gamma=0.99, lr=1e-3, train_batch_size=1024, num_epochs=10, minibatch_size=64
    )
    algo = config.build_algo()
    algo.train()


def multi_agent_train():
    register_env("showdown", ExampleEnv.create_multi_agent_env)
    config = PPOConfig()
    config = config.environment(
        "showdown",
        env_config={"battle_format": "gen9randombattle"},
        disable_env_checking=True,
    )
    config = config.learners(num_learners=1)
    config = config.multi_agent(
        policies={"p1"},
        policy_mapping_fn=lambda agent_id, ep_type: "p1",
        policies_to_train=["p1"],
    )
    config = config.rl_module(
        rl_module_spec=RLModuleSpec(
            module_class=ActorCriticModule,
            observation_space=Box(
                np.array(ExampleEnv.LOW, dtype=np.float32),
                np.array(ExampleEnv.HIGH, dtype=np.float32),
                dtype=np.float32,
            ),
            action_space=Discrete(26),
            model_config={},
        )
    )
    config = config.training(
        gamma=0.99, lr=1e-3, train_batch_size=1024, num_epochs=10, minibatch_size=64
    )
    algo = config.build_algo()
    algo.train()


if __name__ == "__main__":
    single_agent_train()
    multi_agent_train()
