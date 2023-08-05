"""This module contains objects related to player configuration.
"""
from collections import Counter
from typing import Any, NamedTuple, Optional

from poke_env.player import Player


class PlayerConfiguration(NamedTuple):
    username: str
    password: Optional[str]


"""Player configuration object. Represented with a tuple with two entries: username and
password."""

_CONFIGURATION_FROM_PLAYER_COUNTER: "Counter[Any]" = Counter()


def create_player_configuration_from_player(player: Player) -> PlayerConfiguration:
    key = type(player).__name__
    _CONFIGURATION_FROM_PLAYER_COUNTER.update([key])

    username = "%s %d" % (key, _CONFIGURATION_FROM_PLAYER_COUNTER[key])

    if len(username) > 18:
        username = "%s %d" % (
            key[: 18 - len(username)],
            _CONFIGURATION_FROM_PLAYER_COUNTER[key],
        )

    return PlayerConfiguration(username, None)
