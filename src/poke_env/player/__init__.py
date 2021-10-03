# -*- coding: utf-8 -*-
"""poke_env.player module init.
"""
from poke_env.player import env_player
from poke_env.player import player
from poke_env.player import player_network_interface
from poke_env.player import random_player
from poke_env.player import trainable_player
from poke_env.player import utils

__all__ = [
    "env_player",
    "player",
    "player_network_interface",
    "random_player",
    "trainable_player",
    "utils",
]

import gym
names = [
    "SinglePlayer-v7",
    "SinglePlayer-v8",
]
for name in names:
    gym.register(
        id=f"Pokemon{name}",
        entry_point='poke_env.player.env_player:Gen8EnvSinglePlayer',
        max_episode_steps=None,
        nondeterministic=True,
    )
import icecream
icecream.install()