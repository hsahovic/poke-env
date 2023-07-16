"""poke_env module init.
"""
import logging

import poke_env.environment as environment
import poke_env.exceptions as exceptions
import poke_env.player as player
import poke_env.player_configuration as player_configuration
import poke_env.server_configuration as server_configuration
import poke_env.stats as stats
import poke_env.teambuilder as teambuilder
from poke_env.data import gen_data, to_id_str
from poke_env.exceptions import ShowdownException
from poke_env.player_configuration import AccountConfiguration
from poke_env.server_configuration import (
    LocalhostServerConfiguration,
    ServerConfiguration,
    ShowdownServerConfiguration,
)
from poke_env.stats import compute_raw_stats

__logger = logging.getLogger("poke-env")
__stream_handler = logging.StreamHandler()
__formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
__stream_handler.setFormatter(__formatter)
__logger.addHandler(__stream_handler)
logging.addLevelName(25, "PS_ERROR")

__all__ = [
    "AccountConfiguration",
    "LocalhostServerConfiguration",
    "MOVES",
    "NATURES",
    "POKEDEX",
    "ServerConfiguration",
    "ShowdownException",
    "ShowdownServerConfiguration",
    "UNKNOWN_ITEM",
    "compute_raw_stats",
    "environment",
    "exceptions",
    "gen_data",
    "player",
    "player_configuration",
    "ps_client",
    "server_configuration",
    "stats",
    "teambuilder",
    "to_id_str",
]
