import random

import gymnasium.spaces as spaces
import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env
from pettingzoo.test.parallel_test import parallel_api_test

from poke_env.environment import SingleAgentWrapper, SinglesEnv
from poke_env.player import RandomPlayer


class SinglesTestEnv(SinglesEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {
            agent: spaces.Dict(
                {
                    "observation": spaces.Box(
                        np.array([0]), np.array([1]), dtype=np.int64
                    ),
                    "action_mask": spaces.Box(
                        0, 1, shape=(self.action_space_size,), dtype=np.int64
                    ),
                }
            )
            for agent in self.possible_agents
        }

    def calc_reward(self, battle) -> float:
        return 0.0

    def embed_battle(self, battle):
        return np.array([0])


def play_function(env, n_battles):
    for _ in range(n_battles):
        done = False
        obs, _ = env.reset()
        # TODO: when Zoroark isn't a problem anymore this can be removed
        if "illusion" in [
            p.ability
            for p in list(env.battle1.team.values()) + list(env.battle2.team.values())
        ]:
            continue
        while not done:
            actions = {
                name: (
                    sample_action(obs[name]["action_mask"])
                    if env.strict
                    else env.action_space(name).sample()
                )
                for name in env.agents
            }
            obs, _, terminated, truncated, _ = env.step(actions)
            done = any(terminated.values()) or any(truncated.values())


@pytest.mark.timeout(120)
def test_env_run():
    for gen in range(4, 10):
        env = SinglesTestEnv(battle_format=f"gen{gen}randombattle", log_level=25)
        play_function(env, 10)
        env.strict = False
        play_function(env, 10)
        env.close()


def single_agent_play_function(env: SingleAgentWrapper, n_battles: int):
    for _ in range(n_battles):
        done = False
        obs, _ = env.reset()
        # TODO: when Zoroark isn't a problem anymore this can be removed
        if "illusion" in [
            p.ability
            for p in list(env.env.battle1.team.values())
            + list(env.env.battle2.team.values())
        ]:
            continue
        while not done:
            action = (
                sample_action(obs["action_mask"])
                if env.env.strict
                else env.action_space.sample()
            )
            obs, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated


@pytest.mark.timeout(120)
def test_single_agent_env_run():
    for gen in range(4, 10):
        env = SinglesTestEnv(battle_format=f"gen{gen}randombattle", log_level=25)
        env = SingleAgentWrapper(env, RandomPlayer())
        single_agent_play_function(env, 10)
        env.env.strict = False
        single_agent_play_function(env, 10)
        env.close()


def sample_action(action_mask):
    available_actions = [i for i, m in enumerate(action_mask) if m == 1]
    action = random.choice(available_actions)
    return np.int64(action)


@pytest.mark.timeout(60)
def test_repeated_runs():
    env = SinglesTestEnv(
        battle_format="gen8randombattle",
        log_level=25,
        strict=False,
    )
    play_function(env, 2)
    play_function(env, 2)
    env.close()
    env = SinglesTestEnv(
        battle_format="gen9randombattle",
        log_level=25,
        strict=False,
    )
    play_function(env, 2)
    play_function(env, 2)
    env.close()


@pytest.mark.timeout(60)
def test_env_api():
    for gen in range(4, 10):
        env = SinglesTestEnv(
            battle_format=f"gen{gen}randombattle",
            log_level=25,
            strict=False,
        )
        parallel_api_test(env)
        env.close()


@pytest.mark.timeout(60)
def test_single_agent_env_api():
    for gen in range(4, 10):
        env = SinglesTestEnv(
            battle_format=f"gen{gen}randombattle",
            log_level=25,
            strict=False,
        )
        env = SingleAgentWrapper(env, RandomPlayer())
        check_env(env)
        env.close()
