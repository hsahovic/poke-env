# -*- coding: utf-8 -*-
import numpy as np

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


def test_random_gym_player():
    env_player = RandomEnvPlayer(
        player_configuration=PlayerConfiguration("EnvPlayer", None),
        battle_format="gen7randombattle",
        server_configuration=LocalhostServerConfiguration,
    )
    random_player = RandomPlayer(
        player_configuration=PlayerConfiguration("RandomPlayer", None),
        battle_format="gen7randombattle",
        server_configuration=LocalhostServerConfiguration,
    )

    env_player.play_against(
        env_algorithm=play_function,
        opponent=random_player,
        env_algorithm_kwargs={"n_battles": 10},
    )
