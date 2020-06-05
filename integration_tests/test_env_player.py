# -*- coding: utf-8 -*-
import numpy as np
import pytest

from poke_env.player.env_player import Gen7EnvSinglePlayer
from poke_env.player.random_player import RandomPlayer
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import LocalhostServerConfiguration


class RandomEnvPlayer(Gen7EnvSinglePlayer):
    def embed_battle(self, battle):
        return np.array([0])


def play_function(player, n_battles):
    for _ in range(n_battles):
        done = False
        player.reset()
        while not done:
            _, _, done, _ = player.step(np.random.choice(player.action_space))


@pytest.mark.timeout(60)
def test_random_gym_player_gen7():
    env_player = RandomEnvPlayer(
        player_configuration=PlayerConfiguration("EnvPlayerGen7", None),
        battle_format="gen7randombattle",
        server_configuration=LocalhostServerConfiguration,
    )
    random_player = RandomPlayer(
        player_configuration=PlayerConfiguration("RandomPlayerGen7", None),
        battle_format="gen7randombattle",
        server_configuration=LocalhostServerConfiguration,
    )

    env_player.play_against(
        env_algorithm=play_function,
        opponent=random_player,
        env_algorithm_kwargs={"n_battles": 5},
    )


@pytest.mark.timeout(60)
def test_random_gym_player_gen8():
    env_player = RandomEnvPlayer(
        player_configuration=PlayerConfiguration("EnvPlayerGen8", None),
        battle_format="gen8randombattle",
        server_configuration=LocalhostServerConfiguration,
    )
    random_player = RandomPlayer(
        player_configuration=PlayerConfiguration("RandomPlayerGen8", None),
        battle_format="gen8randombattle",
        server_configuration=LocalhostServerConfiguration,
    )

    env_player.play_against(
        env_algorithm=play_function,
        opponent=random_player,
        env_algorithm_kwargs={"n_battles": 5},
    )
