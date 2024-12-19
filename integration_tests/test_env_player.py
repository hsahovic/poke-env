from copy import deepcopy

import numpy as np
import pytest
from gymnasium.spaces import Box, Space
from pettingzoo.test import parallel_api_test

from poke_env.environment import AbstractBattle
from poke_env.player import BattleOrder, Player, PokeEnv


class RandomEnv(PokeEnv):
    _ACTION_SPACE = list(range(10))

    def calc_reward(self, battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return Box(np.array([0]), np.array([1]), dtype=np.int32)

    def embed_battle(self, battle):
        return battle

    def action_to_move(self, action, battle):
        return action


def play_function(env: PokeEnv[AbstractBattle, BattleOrder], n_battles):
    for _ in range(n_battles):
        done = False
        obs, _ = env.reset()
        while not done:
            battle1, battle2 = obs.values()
            if battle1.maybe_trapped:
                battle1 = deepcopy(battle1)
                battle1._trapped = True
            if battle2.maybe_trapped:
                battle2 = deepcopy(battle2)
                battle2._trapped = True
            actions = {
                env.agents[0]: Player.choose_random_move(battle1),
                env.agents[1]: Player.choose_random_move(battle2),
            }
            obs, _, terminated, truncated, _ = env.step(actions)
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
