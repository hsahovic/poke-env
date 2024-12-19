import random

import numpy as np
import pytest
from pettingzoo.test import parallel_api_test

from poke_env.player import PokeEnv


class RandomEnv(PokeEnv):
    _ACTION_SPACE = list(range(10))

    def calc_reward(self, battle) -> float:
        return 0.0

    def embed_battle(self, battle):
        return np.array([0])


def play_function(env: PokeEnv, n_battles):
    for _ in range(n_battles):
        done = False
        _, info = env.reset()
        while not done:
            actions = {
                name: random.choice(info[name]["action_space"]) for name in env.agents
            }
            _, _, terminated, truncated, info = env.step(actions)
            done = any(terminated.values()) or any(truncated.values())


@pytest.mark.timeout(30)
def test_random_gym_players_gen4():
    env_player = RandomEnv(
        battle_format="gen4randombattle", log_level=25, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen5():
    env_player = RandomEnv(
        battle_format="gen5randombattle", log_level=25, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen6():
    env_player = RandomEnv(
        battle_format="gen6randombattle", log_level=25, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen7():
    env_player = RandomEnv(
        battle_format="gen7randombattle", log_level=25, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen8():
    env_player = RandomEnv(
        battle_format="gen8randombattle", log_level=25, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen9():
    env_player = RandomEnv(
        battle_format="gen9randombattle", log_level=25, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(60)
def test_two_successive_calls_gen8():
    env_player = RandomEnv(
        battle_format="gen8randombattle", log_level=25, start_challenging=False
    )
    env_player.start_challenging(2)
    play_function(env_player, 2)
    env_player.start_challenging(2)
    play_function(env_player, 2)


@pytest.mark.timeout(60)
def test_two_successive_calls_gen9():
    env_player = RandomEnv(
        battle_format="gen9randombattle", log_level=25, start_challenging=False
    )
    env_player.start_challenging(2)
    play_function(env_player, 2)
    env_player.start_challenging(2)
    play_function(env_player, 2)


@pytest.mark.timeout(60)
def test_parallel_api_tests():
    env_player_gen4 = RandomEnv(
        battle_format="gen4randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_player_gen4, num_cycles=10)
    env_player_gen4.close()
    env_player_gen5 = RandomEnv(
        battle_format="gen5randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_player_gen5, num_cycles=10)
    env_player_gen5.close()
    env_player_gen6 = RandomEnv(
        battle_format="gen6randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_player_gen6, num_cycles=10)
    env_player_gen6.close()
    env_player_gen7 = RandomEnv(
        battle_format="gen7randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_player_gen7, num_cycles=10)
    env_player_gen7.close()
    env_player_gen8 = RandomEnv(
        battle_format="gen8randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_player_gen8, num_cycles=10)
    env_player_gen8.close()
    env_player_gen9 = RandomEnv(
        battle_format="gen9randombattle", log_level=25, start_challenging=True
    )
    parallel_api_test(env_player_gen9, num_cycles=10)
    env_player_gen9.close()
