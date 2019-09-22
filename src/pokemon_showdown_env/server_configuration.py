# -*- coding: utf-8 -*-
from collections import namedtuple


ServerConfiguration = namedtuple(
    "ServerConfiguration", ["server_url", "authentication_url"]
)

LocalhostServerConfiguration = ServerConfiguration(
    "localhost:8000", "https://play.pokemonshowdown.com/action.php?"
)
ShowdownServerConfiguration = ServerConfiguration(
    "https://play.pokemonshowdown.com/", "https://play.pokemonshowdown.com/action.php?"
)
