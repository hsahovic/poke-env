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


@pytest.mark.timeout(120)
def test_random_gym_players():
    for battle_format, EnvPlayerClass in zip(
        [
            "gen4randombattle",
            "gen5randombattle",
            "gen6randombattle",
            "gen7randombattle",
            "gen8randombattle",
        ],
        [
            RandomGen4EnvPlayer,
            RandomGen5EnvPlayer,
            RandomGen6EnvPlayer,
            RandomGen7EnvPlayer,
            RandomGen8EnvPlayer,
        ],
    ):
        env_player = EnvPlayerClass(log_level=20)
        random_player = RandomPlayer(battle_format=battle_format, log_level=20)
        env_player.play_against(
            env_algorithm=play_function,
            opponent=random_player,
            env_algorithm_kwargs={"n_battles": 3},
        )


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
