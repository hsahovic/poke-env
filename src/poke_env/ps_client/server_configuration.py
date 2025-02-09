"""This module contains objects related to server configuration."""

from typing import NamedTuple


class ServerConfiguration(NamedTuple):
    """Server configuration object. Represented with a tuple with two entries: server url
    and authentication endpoint url."""

    websocket_url: str
    authentication_url: str


LocalhostServerConfiguration = ServerConfiguration(
    "ws://localhost:8000/showdown/websocket",
    "https://play.pokemonshowdown.com/action.php?",
)
"""Server configuration with localhost and smogon's authentication endpoint."""

ShowdownServerConfiguration = ServerConfiguration(
    "wss://sim3.psim.us/showdown/websocket",
    "https://play.pokemonshowdown.com/action.php?",
)
"""Server configuration with smogon's server and authentication endpoint."""
