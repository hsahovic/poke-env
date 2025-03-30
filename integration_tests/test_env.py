import numpy as np
import pytest
from gymnasium.spaces import Box
from pettingzoo.test.parallel_test import parallel_api_test

from poke_env.player import DoublesEnv, SinglesEnv


class SinglesTestEnv(SinglesEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {
            agent: Box(np.array([0]), np.array([1]), dtype=np.int64)
            for agent in self.possible_agents
        }

    def calc_reward(self, battle) -> float:
        return 0.0

    def embed_battle(self, battle):
        return np.array([0])


class DoublesTestEnv(DoublesEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_spaces = {
            agent: Box(np.array([0]), np.array([1]), dtype=np.int64)
            for agent in self.possible_agents
        }

    def calc_reward(self, battle) -> float:
        return 0.0

    def embed_battle(self, battle):
        return np.array([0])


def play_function(env, n_battles):
    for _ in range(n_battles):
        done = False
        env.reset()
        while not done:
            actions = {name: env.action_space(name).sample() for name in env.agents}
            _, _, terminated, truncated, _ = env.step(actions)
            done = any(terminated.values()) or any(truncated.values())


@pytest.mark.timeout(120)
def test_env_run():
    for gen in range(4, 10):
        env = SinglesTestEnv(
            battle_format=f"gen{gen}randombattle",
            log_level=25,
            start_challenging=False,
            strict=False,
        )
        env.start_challenging(3)
        play_function(env, 3)
        env.close()
    for gen in range(8, 10):
        env = DoublesTestEnv(
            battle_format=f"gen{gen}randomdoublesbattle",
            log_level=25,
            start_challenging=False,
            strict=False,
        )
        env.start_challenging(3)
        play_function(env, 3)
        env.close()


@pytest.mark.timeout(60)
def test_repeated_runs():
    env = SinglesTestEnv(
        battle_format="gen8randombattle",
        log_level=25,
        start_challenging=False,
        strict=False,
    )
    env.start_challenging(2)
    play_function(env, 2)
    env.start_challenging(2)
    play_function(env, 2)
    env.close()
    env = SinglesTestEnv(
        battle_format="gen9randombattle",
        log_level=25,
        start_challenging=False,
        strict=False,
    )
    env.start_challenging(2)
    play_function(env, 2)
    env.start_challenging(2)
    play_function(env, 2)
    env.close()


def test_env_with_teams(showdown_format_teams):
    for format_, teams in showdown_format_teams.items():
        for team in teams:
            env_type = (
                DoublesTestEnv
                if "doubles" in format_ or "vgc" in format_
                else SinglesTestEnv
            )
            env = env_type(
                battle_format=format_,
                log_level=25,
                team=team,
                start_challenging=True,
                strict=False,
            )
            play_function(env, 10)
            env.close()


@pytest.mark.timeout(120)
def test_env_api():
    for gen in range(4, 10):
        env = SinglesTestEnv(
            battle_format=f"gen{gen}randombattle",
            log_level=25,
            start_challenging=True,
            strict=False,
        )
        parallel_api_test(env)
        env.close()
    for gen in range(8, 10):
        env = DoublesTestEnv(
            battle_format=f"gen{gen}randomdoublesbattle",
            log_level=25,
            start_challenging=True,
            strict=False,
        )
        parallel_api_test(env)
        env.close()
