import numpy as np
import pytest
from gymnasium.spaces import Box, Space
from gymnasium.utils.env_checker import check_env

from poke_env.player import (
    Gen4EnvSinglePlayer,
    Gen5EnvSinglePlayer,
    Gen6EnvSinglePlayer,
    Gen7EnvSinglePlayer,
    Gen8EnvSinglePlayer,
    Gen9EnvSinglePlayer,
    RandomPlayer,
)


class RandomGen4EnvPlayer(Gen4EnvSinglePlayer):
    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return Box(np.array([0]), np.array([1]), dtype=int)

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen5EnvPlayer(Gen5EnvSinglePlayer):
    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return Box(np.array([0]), np.array([1]), dtype=int)

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen6EnvPlayer(Gen6EnvSinglePlayer):
    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return Box(np.array([0]), np.array([1]), dtype=int)

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen7EnvPlayer(Gen7EnvSinglePlayer):
    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return Box(np.array([0]), np.array([1]), dtype=int)

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen8EnvPlayer(Gen8EnvSinglePlayer):
    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return Box(np.array([0]), np.array([1]), dtype=int)

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen9EnvPlayer(Gen9EnvSinglePlayer):
    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return Box(np.array([0]), np.array([1]), dtype=int)

    def embed_battle(self, battle):
        return np.array([0])


def play_function(player, n_battles):
    for _ in range(n_battles):
        done = False
        player.reset()
        while not done:
            _, _, terminated, truncated, _ = player.step(player.action_space.sample())
            done = terminated or truncated


@pytest.mark.timeout(30)
def test_random_gym_players_gen4():
    random_player = RandomPlayer(battle_format="gen4randombattle", log_level=25)
    env_player = RandomGen4EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen5():
    random_player = RandomPlayer(battle_format="gen5randombattle", log_level=25)
    env_player = RandomGen5EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen6():
    random_player = RandomPlayer(battle_format="gen6randombattle", log_level=25)
    env_player = RandomGen6EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen7():
    random_player = RandomPlayer(battle_format="gen7randombattle", log_level=25)
    env_player = RandomGen7EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen8():
    random_player = RandomPlayer(battle_format="gen8randombattle", log_level=25)
    env_player = RandomGen8EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen9():
    random_player = RandomPlayer(battle_format="gen9randombattle", log_level=25)
    env_player = RandomGen9EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=False
    )
    env_player.start_challenging(3)
    play_function(env_player, 3)


@pytest.mark.timeout(60)
def test_two_successive_calls_gen8():
    random_player = RandomPlayer(battle_format="gen8randombattle", log_level=25)
    env_player = RandomGen8EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=False
    )
    env_player.start_challenging(2)
    play_function(env_player, 2)
    env_player.start_challenging(2)
    play_function(env_player, 2)


@pytest.mark.timeout(60)
def test_two_successive_calls_gen9():
    random_player = RandomPlayer(battle_format="gen9randombattle", log_level=25)
    env_player = RandomGen9EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=False
    )
    env_player.start_challenging(2)
    play_function(env_player, 2)
    env_player.start_challenging(2)
    play_function(env_player, 2)


@pytest.mark.timeout(60)
def test_check_envs():
    random_player = RandomPlayer(battle_format="gen4randombattle", log_level=25)
    env_player_gen4 = RandomGen4EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=True
    )
    check_env(env_player_gen4)
    env_player_gen4.close()
    random_player = RandomPlayer(battle_format="gen5randombattle", log_level=25)
    env_player_gen5 = RandomGen5EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=True
    )
    check_env(env_player_gen5)
    env_player_gen5.close()
    random_player = RandomPlayer(battle_format="gen6randombattle", log_level=25)
    env_player_gen6 = RandomGen6EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=True
    )
    check_env(env_player_gen6)
    env_player_gen6.close()
    random_player = RandomPlayer(battle_format="gen7randombattle", log_level=25)
    env_player_gen7 = RandomGen7EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=True
    )
    check_env(env_player_gen7)
    env_player_gen7.close()
    random_player = RandomPlayer(battle_format="gen8randombattle", log_level=25)
    env_player_gen8 = RandomGen8EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=True
    )
    check_env(env_player_gen8)
    env_player_gen8.close()
    random_player = RandomPlayer(battle_format="gen9randombattle", log_level=25)
    env_player_gen9 = RandomGen9EnvPlayer(
        log_level=25, opponent=random_player, start_challenging=True
    )
    check_env(env_player_gen9)
    env_player_gen9.close()
