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
