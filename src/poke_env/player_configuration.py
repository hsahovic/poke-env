# -*- coding: utf-8 -*-
"""This module contains objects related to player configuration.
"""
from collections import namedtuple
from collections import Counter

PlayerConfiguration = namedtuple("PlayerConfiguration", ["username", "password"])
"""Player configuration object. Represented with a tuple with two entries: username and
password."""

_CONFIGURATION_FROM_PLAYER_COUNTER = Counter()


def _create_player_configuration_from_player(player) -> PlayerConfiguration:
    key = type(player).__name__
    _CONFIGURATION_FROM_PLAYER_COUNTER.update([key])

    username = "%s %d" % (key, _CONFIGURATION_FROM_PLAYER_COUNTER[key])

    if len(username) > 18:
        username = "%s %d" % (
            key[: 18 - len(username)],
            _CONFIGURATION_FROM_PLAYER_COUNTER[key],
        )

    return PlayerConfiguration(username, None)
