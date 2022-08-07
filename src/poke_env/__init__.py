# -*- coding: utf-8 -*-
"""poke_env module init.
"""
import logging

import poke_env.data as data
import poke_env.environment as environment
import poke_env.exceptions as exceptions
import poke_env.player as player
import poke_env.player_configuration as player_configuration
import poke_env.server_configuration as server_configuration
import poke_env.teambuilder as teambuilder
import poke_env.utils as utils
from poke_env.data import (
    GEN4_MOVES,
    GEN4_POKEDEX,
    GEN5_MOVES,
    GEN5_POKEDEX,
    GEN6_MOVES,
    GEN6_POKEDEX,
    GEN7_MOVES,
    GEN7_POKEDEX,
    GEN8_MOVES,
    GEN8_POKEDEX,
    GEN_TO_MOVES,
    GEN_TO_POKEDEX,
    MOVES,
    NATURES,
    POKEDEX,
    TYPE_CHART,
    UNKNOWN_ITEM,
    to_id_str,
)
from poke_env.exceptions import ShowdownException
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import (
    LocalhostServerConfiguration,
    ServerConfiguration,
    ShowdownServerConfiguration,
)
from poke_env.utils import (
    compute_raw_stats,
)

__logger = logging.getLogger("poke-env")
__stream_handler = logging.StreamHandler()
__formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
__stream_handler.setFormatter(__formatter)
__logger.addHandler(__stream_handler)
logging.addLevelName(25, "PS_ERROR")

__all__ = [
    "GEN4_MOVES",
    "GEN4_POKEDEX",
    "GEN5_MOVES",
    "GEN5_POKEDEX",
    "GEN6_MOVES",
    "GEN6_POKEDEX",
    "GEN7_MOVES",
    "GEN7_POKEDEX",
    "GEN8_MOVES",
    "GEN8_POKEDEX",
    "GEN_TO_MOVES",
    "GEN_TO_POKEDEX",
    "LocalhostServerConfiguration",
    "MOVES",
    "NATURES",
    "POKEDEX",
    "PlayerConfiguration",
    "ServerConfiguration",
    "ShowdownException",
    "ShowdownServerConfiguration",
    "TYPE_CHART",
    "UNKNOWN_ITEM",
    "compute_raw_stats",
    "data",
    "environment",
    "exceptions",
    "player",
    "player_configuration",
    "server_configuration",
    "teambuilder",
    "to_id_str",
    "utils",
]
