# -*- coding: utf-8 -*-
import numpy as np
import pytest

from poke_env.player.env_player import (
    Gen4EnvSinglePlayer,
    Gen5EnvSinglePlayer,
    Gen6EnvSinglePlayer,
    Gen7EnvSinglePlayer,
    Gen8EnvSinglePlayer,
)
from poke_env.player.random_player import RandomPlayer


class RandomGen4EnvPlayer(Gen4EnvSinglePlayer):
    MAX_BATTLE_SWITCH_RETRY = 500

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen5EnvPlayer(Gen5EnvSinglePlayer):
    MAX_BATTLE_SWITCH_RETRY = 500

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen6EnvPlayer(Gen6EnvSinglePlayer):
    MAX_BATTLE_SWITCH_RETRY = 500

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen7EnvPlayer(Gen7EnvSinglePlayer):
    MAX_BATTLE_SWITCH_RETRY = 500

    def embed_battle(self, battle):
        return np.array([0])


class RandomGen8EnvPlayer(Gen8EnvSinglePlayer):
    MAX_BATTLE_SWITCH_RETRY = 500

    def embed_battle(self, battle):
        return np.array([0])


def play_function(player, n_battles):
    for _ in range(n_battles):
        done = False
        player.reset()
        while not done:
            _, _, done, _ = player.step(np.random.choice(player.action_space))


@pytest.mark.flaky(reruns=3, reruns_delay=1)
@pytest.mark.timeout(30)
def test_random_gym_players_gen4():
    env_player = RandomGen4EnvPlayer(log_level=20)
    random_player = RandomPlayer(battle_format="gen4randombattle", log_level=20)
    env_player.play_against(
        env_algorithm=play_function,
        opponent=random_player,
        env_algorithm_kwargs={"n_battles": 3},
    )


@pytest.mark.flaky(reruns=3, reruns_delay=1)
@pytest.mark.timeout(30)
def test_random_gym_players_gen5():
    env_player = RandomGen5EnvPlayer(log_level=20)
    random_player = RandomPlayer(battle_format="gen5randombattle", log_level=20)
    env_player.play_against(
        env_algorithm=play_function,
        opponent=random_player,
        env_algorithm_kwargs={"n_battles": 3},
    )


@pytest.mark.flaky(reruns=3, reruns_delay=1)
@pytest.mark.timeout(30)
def test_random_gym_players_gen6():
    env_player = RandomGen6EnvPlayer(log_level=20)
    random_player = RandomPlayer(battle_format="gen6randombattle", log_level=20)
    env_player.play_against(
        env_algorithm=play_function,
        opponent=random_player,
        env_algorithm_kwargs={"n_battles": 3},
    )


@pytest.mark.flaky(reruns=3, reruns_delay=1)
@pytest.mark.timeout(30)
def test_random_gym_players_gen7():
    env_player = RandomGen7EnvPlayer(log_level=20)
    random_player = RandomPlayer(battle_format="gen7randombattle", log_level=20)
    env_player.play_against(
        env_algorithm=play_function,
        opponent=random_player,
        env_algorithm_kwargs={"n_battles": 3},
    )


@pytest.mark.flaky(reruns=3, reruns_delay=1)
@pytest.mark.timeout(30)
def test_random_gym_players_gen8():
    env_player = RandomGen8EnvPlayer(log_level=20)
    random_player = RandomPlayer(battle_format="gen8randombattle", log_level=20)
    env_player.play_against(
        env_algorithm=play_function,
        opponent=random_player,
        env_algorithm_kwargs={"n_battles": 3},
    )


@pytest.mark.flaky(reruns=3, reruns_delay=1)
@pytest.mark.timeout(60)
def test_two_successive_calls_gen8():
    env_player = RandomGen8EnvPlayer(battle_format="gen8randombattle", log_level=20)
    random_player = RandomPlayer(battle_format="gen8randombattle", log_level=20)
    env_player.play_against(
        env_algorithm=play_function,
        opponent=random_player,
        env_algorithm_kwargs={"n_battles": 2},
    )
    env_player.play_against(
        env_algorithm=play_function,
        opponent=random_player,
        env_algorithm_kwargs={"n_battles": 2},
    )
