"""This module contains objects related to player configuration.
"""
from typing import Counter, NamedTuple, Optional

CONFIGURATION_FROM_PLAYER_COUNTER: Counter[str] = Counter()

class AccountConfiguration(NamedTuple):
    """Player configuration object. Represented with a tuple with two entries: username and
    password."""
    username: str
    password: Optional[str]


def _create_account_configuration_from_player(player) -> AccountConfiguration:
    key = type(player).__name__
    _CONFIGURATION_FROM_PLAYER_COUNTER.update([key])

    username = "%s %d" % (key, _CONFIGURATION_FROM_PLAYER_COUNTER[key])

    if len(username) > 18:
        username = "%s %d" % (
            key[: 18 - len(username)],
            _CONFIGURATION_FROM_PLAYER_COUNTER[key],
        )

    return AccountConfiguration(username, None)
