"""This module contains objects related to server configuration.
"""
from typing import NamedTuple


class ServerConfiguration(NamedTuple):
    """Server configuration object. Represented with a tuple with two entries: server url
    and authentication endpoint url."""

    server_url: str
    authentication_url: str


LocalhostServerConfiguration = ServerConfiguration(
    "localhost:8000", "https://play.pokemonshowdown.com/action.php?"
)
"""Server configuration with localhost and smogon's authentication endpoint."""

ShowdownServerConfiguration = ServerConfiguration(
    "sim.smogon.com:8000", "https://play.pokemonshowdown.com/action.php?"
)
"""Server configuration with smogon's server and authentication endpoint."""
