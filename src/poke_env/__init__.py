"""poke_env module init."""

import logging

from poke_env.data import gen_data, to_id_str
from poke_env.exceptions import ShowdownException
from poke_env.player import (
    MaxBasePowerPlayer,
    Player,
    RandomPlayer,
    SimpleHeuristicsPlayer,
    cross_evaluate,
)
from poke_env.ps_client import AccountConfiguration
from poke_env.ps_client.server_configuration import (
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
    "MaxBasePowerPlayer",
    "Player",
    "RandomPlayer",
    "ServerConfiguration",
    "ShowdownException",
    "ShowdownServerConfiguration",
    "SimpleHeuristicsPlayer",
    "compute_raw_stats",
    "cross_evaluate",
    "gen_data",
    "to_id_str",
]
