"""This module contains objects related to player configuration."""

from __future__ import annotations

import random
import string
from typing import Counter, NamedTuple, Optional

CONFIGURATION_FROM_PLAYER_COUNTER: Counter[str] = Counter()


class AccountConfiguration(NamedTuple):
    """Player configuration object. Represented with a tuple with two entries: username and
    password."""

    username: str
    password: Optional[str]

    @classmethod
    def countgen(cls, key: str) -> AccountConfiguration:
        CONFIGURATION_FROM_PLAYER_COUNTER.update([key])
        username = "%s %d" % (key, CONFIGURATION_FROM_PLAYER_COUNTER[key])
        if len(username) > 18:
            username = "%s %d" % (
                key[: 18 - len(username)],
                CONFIGURATION_FROM_PLAYER_COUNTER[key],
            )
        return cls(username, None)

    @classmethod
    def randgen(cls, length: int) -> AccountConfiguration:
        char_space = string.ascii_lowercase + string.digits
        username = "".join(random.choices(char_space, k=length))
        return cls(username, None)
