# -*- coding: utf-8 -*-
import numpy as np
import pytest
from gym import Space

from poke_env.player.env_player import (
    Gen4EnvSinglePlayer,
    Gen5EnvSinglePlayer,
    Gen6EnvSinglePlayer,
    Gen7EnvSinglePlayer,
    Gen8EnvSinglePlayer,
)
from poke_env.player.openai_api import EnvLoop
from poke_env.player.random_player import RandomPlayer


class RandomGen4EnvPlayer(Gen4EnvSinglePlayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return None

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen5EnvPlayer(Gen5EnvSinglePlayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return None

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen6EnvPlayer(Gen6EnvSinglePlayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return None

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen7EnvPlayer(Gen7EnvSinglePlayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return None

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen8EnvPlayer(Gen8EnvSinglePlayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def calc_reward(self, last_battle, current_battle) -> float:
        return 0.0

    def describe_embedding(self) -> Space:
        return None

    def embed_battle(self, battle):
        return np.array([0])


def play_function(player, n_battles):
    for _ in range(n_battles):
        done = False
        player.reset()
        while not done:
            _, _, done, _ = player.step(player.action_space.sample())


@pytest.mark.timeout(30)
def test_random_gym_players_gen4():
    with EnvLoop():
        random_player = RandomPlayer(battle_format="gen4randombattle", log_level=20)
        env_player = RandomGen4EnvPlayer(
            log_level=20, opponent=random_player, start_challenging=False
        )
        env_player.start_challenging(3)
        play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen5():
    with EnvLoop():
        random_player = RandomPlayer(battle_format="gen5randombattle", log_level=20)
        env_player = RandomGen5EnvPlayer(
            log_level=20, opponent=random_player, start_challenging=False
        )
        env_player.start_challenging(3)
        play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen6():
    with EnvLoop():
        random_player = RandomPlayer(battle_format="gen5randombattle", log_level=20)
        env_player = RandomGen5EnvPlayer(
            log_level=20, opponent=random_player, start_challenging=False
        )
        env_player.start_challenging(3)
        play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen7():
    with EnvLoop():
        random_player = RandomPlayer(battle_format="gen6randombattle", log_level=20)
        env_player = RandomGen6EnvPlayer(
            log_level=20, opponent=random_player, start_challenging=False
        )
        env_player.start_challenging(3)
        play_function(env_player, 3)


@pytest.mark.timeout(30)
def test_random_gym_players_gen8():
    with EnvLoop():
        random_player = RandomPlayer(battle_format="gen8randombattle", log_level=20)
        env_player = RandomGen8EnvPlayer(
            log_level=20, opponent=random_player, start_challenging=False
        )
        env_player.start_challenging(3)
        play_function(env_player, 3)


@pytest.mark.timeout(60)
def test_two_successive_calls_gen8():
    with EnvLoop():
        random_player = RandomPlayer(battle_format="gen4randombattle", log_level=20)
        env_player = RandomGen4EnvPlayer(
            log_level=20, opponent=random_player, start_challenging=False
        )
        env_player.start_challenging(2)
        play_function(env_player, 2)
        env_player.start_challenging(2)
        play_function(env_player, 2)
