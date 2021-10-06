# -*- coding: utf-8 -*-
"""poke_env module init.
"""
import poke_env.data as data
import poke_env.environment as environment
import poke_env.exceptions as exceptions
import poke_env.player as player
import poke_env.player_configuration as player_configuration
import poke_env.server_configuration as server_configuration
import poke_env.teambuilder as teambuilder
import poke_env.utils as utils


import gym
import logging

__logger = logging.getLogger("poke-env")
__stream_handler = logging.StreamHandler()
__formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
__stream_handler.setFormatter(__formatter)
__logger.addHandler(__stream_handler)
logging.addLevelName(25, "PS_ERROR")

__all__ = [
    "data",
    "environment",
    "exceptions",
    "player",
    "player_configuration",
    "server_configuration",
    "teambuilder",
    "utils",
]

from poke_env.player.env_player import (
    GEN4_BATTLE_FORMAT,
    GEN5_BATTLE_FORMAT,
    GEN6_BATTLE_FORMAT,
    GEN7_BATTLE_FORMAT,
    GEN8_BATTLE_FORMAT,
    #GEN8_DOUBLE_BATTLE_FORMAT,
    GEN6_ACTION_SPACE,
    GEN7_ACTION_SPACE,
    GEN8_ACTION_SPACE,
    gen4_action_to_move,
    gen7_action_to_move,
    gen8_action_to_move,
)
for version, format, action_space, action_to_move in [
        ("8", GEN8_BATTLE_FORMAT, GEN8_ACTION_SPACE, gen8_action_to_move),
    ]:
    gym.register(
        id=f"PokemonRandomSingles-v{version}",
        entry_point="poke_env.player.env_player:EnvPlayer",
        kwargs = dict(
            action_to_move=action_to_move,
            action_space=action_space,
            battle_format=format,
        )
    )