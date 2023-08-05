"""This module contains objects related to player configuration.
"""
from typing import Any, Counter, NamedTuple, Optional

_CONFIGURATION_FROM_PLAYER_COUNTER: Counter[Any] = Counter()

"""Player configuration object. Represented with a tuple with two entries: username and
password."""


class PlayerConfiguration(NamedTuple):
    username: str
    password: Optional[str]
