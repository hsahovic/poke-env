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

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.player import RandomPlayer, SingleAgentWrapper, SinglesEnv


class TestEnv(SinglesEnv[npt.NDArray[np.float32]]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {
            agent: Box(0, 6, shape=(2,), dtype=np.float32)
            for agent in self.possible_agents
        }

    @classmethod
    def create_multi_agent_env(cls, config: Dict[str, Any]) -> ParallelPettingZooEnv:
        env = cls(
            battle_format=config["battle_format"],
            log_level=25,
            open_timeout=None,
            start_challenging=True,
            strict=False,
        )
        return ParallelPettingZooEnv(env)

    @classmethod
    def create_single_agent_env(cls, config: Dict[str, Any]) -> SingleAgentWrapper:
        env = cls(
            battle_format=config["battle_format"],
            log_level=25,
            open_timeout=None,
            start_challenging=True,
            strict=False,
        )
        opponent = RandomPlayer()
        return SingleAgentWrapper(env, opponent)

    def calc_reward(self, battle) -> float:
        return self.reward_computing_helper(battle)

    def embed_battle(self, battle: AbstractBattle):
        to_embed = []
        fainted_mons = 0
        for mon in battle.team.values():
            if mon.fainted:
                fainted_mons += 1
        to_embed.append(fainted_mons)
        fainted_enemy_mons = 0
        for mon in battle.opponent_team.values():
            if mon.fainted:
                fainted_enemy_mons += 1
        to_embed.append(fainted_enemy_mons)
        return np.array(to_embed, dtype=np.float32)


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
        self.model = nn.Linear(2, 10)
        self.actor = nn.Linear(10, 26)
        self.critic = nn.Linear(10, 1)

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
    register_env("showdown", TestEnv.create_single_agent_env)
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
            observation_space=Box(0, 6, shape=(2,), dtype=np.float32),
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
    register_env("showdown", TestEnv.create_multi_agent_env)
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
            observation_space=Box(0, 6, shape=(2,), dtype=np.float32),
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
