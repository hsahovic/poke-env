# -*- coding: utf-8 -*-
"""This module contains objects related to server configuration.
"""
from collections import namedtuple


ServerConfiguration = namedtuple(
    "ServerConfiguration", ["server_url", "authentication_url"]
)
"""Server configuration object. Represented with a tuple with two entries: server url
and authentication endpoint url."""

LocalhostServerConfiguration = ServerConfiguration(
    "localhost:8000", "https://play.pokemonshowdown.com/action.php?"
)
"""Server configuration with localhost and smogon's authentication endpoint."""

ShowdownServerConfiguration = ServerConfiguration(
    "https://play.pokemonshowdown.com/", "https://play.pokemonshowdown.com/action.php?"
)
"""Server configuration with smogon's server and authentication endpoint."""
