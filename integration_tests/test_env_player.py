import numpy as np
import pytest
from gymnasium.spaces import Box
from pettingzoo.test.parallel_test import parallel_api_test

from poke_env.player import DoublesEnv, PokeEnv, SinglesEnv


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


def play_function(env: PokeEnv, n_battles: int):
    for _ in range(n_battles):
        done = False
        env.reset()
        while not done:
            actions = {name: env.action_space(name).sample() for name in env.agents}
            _, _, terminated, truncated, _ = env.step(actions)
            done = any(terminated.values()) or any(truncated.values())


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen4():
    env = SinglesTestEnv(
        battle_format="gen4randombattle", log_level=25, start_challenging=False
    )
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen5():
    env = SinglesTestEnv(
        battle_format="gen5randombattle", log_level=25, start_challenging=False
    )
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen6():
    env = SinglesTestEnv(
        battle_format="gen6randombattle", log_level=25, start_challenging=False
    )
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen7():
    env = SinglesTestEnv(
        battle_format="gen7randombattle", log_level=25, start_challenging=False
    )
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen8():
    env = SinglesTestEnv(
        battle_format="gen8randombattle", log_level=25, start_challenging=False
    )
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_player_doubles_gen8():
    env = DoublesTestEnv(
        battle_format="gen8randomdoublesbattle", log_level=25, start_challenging=False
    )
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_players_gen9():
    env = SinglesTestEnv(
        battle_format="gen9randombattle", log_level=25, start_challenging=False
    )
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(30)
def test_random_gymnasium_player_doubles_gen9():
    env = DoublesTestEnv(
        battle_format="gen9randomdoublesbattle", log_level=25, start_challenging=False
    )
    env.start_challenging(3)
    play_function(env, 3)


@pytest.mark.timeout(60)
def test_two_successive_calls_gen8():
    env = SinglesTestEnv(
        battle_format="gen8randombattle", log_level=25, start_challenging=False
    )
    env.start_challenging(2)
    play_function(env, 2)
    env.start_challenging(2)
    play_function(env, 2)


@pytest.mark.timeout(60)
def test_two_successive_calls_gen9():
    env = SinglesTestEnv(
        battle_format="gen9randombattle", log_level=25, start_challenging=False
    )
    env.start_challenging(2)
    play_function(env, 2)
    env.start_challenging(2)
    play_function(env, 2)


@pytest.mark.timeout(60)
def test_check_envs():
    for gen in range(4, 10):
        env = SinglesTestEnv(
            battle_format=f"gen{gen}randombattle", log_level=25, start_challenging=True
        )
        parallel_api_test(env)
        env.close()
    for gen in range(8, 10):
        env = DoublesTestEnv(
            battle_format=f"gen{gen}randomdoublesbattle",
            log_level=25,
            start_challenging=True,
        )
        parallel_api_test(env)
        env.close()
