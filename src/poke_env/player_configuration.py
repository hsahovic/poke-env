# -*- coding: utf-8 -*-
"""This module contains objects related to player configuration.
"""
from collections import namedtuple
import uuid

PlayerConfiguration = namedtuple("PlayerConfiguration", ["username", "password"])
"""Player configuration object. Represented with a tuple with two entries: username and
password."""

MAX_USERNAME_LENGTH = 18
MAX_PLAYER_NAME_LENGTH = 14


def _create_player_configuration_from_player(player) -> PlayerConfiguration:

    player_name = type(player).__name__

    # Leave some space for unique identifiers
    player_name = player_name[:MAX_USERNAME_LENGTH]

    # Make sure the total is equal to max player name length
    id = str(uuid.uuid4())
    id_length = MAX_USERNAME_LENGTH - len(player_name)
    id = id[:id_length]

    username = f"{player_name}{id}"

    return PlayerConfiguration(username, None)
