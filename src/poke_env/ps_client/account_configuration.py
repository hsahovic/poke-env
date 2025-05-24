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
    def generate(cls, key: str) -> AccountConfiguration:
        """
        Generates an AccountConfiguration instance using a provided key.
        The same key can be used multiple times to create multiple usernames.

        For example, using key=MyName, the first username will be MyName 1,
        the second will be MyName 2, etc.

        The key will be truncated to be a maximum of 18 characters long.
        """
        CONFIGURATION_FROM_PLAYER_COUNTER.update([key])
        username = "%s %d" % (key, CONFIGURATION_FROM_PLAYER_COUNTER[key])
        if len(username) > 18:
            username = "%s %d" % (
                key[: 18 - len(username)],
                CONFIGURATION_FROM_PLAYER_COUNTER[key],
            )
        return cls(username, None)

    @classmethod
    def randgen(cls, length: int = 10) -> AccountConfiguration:
        """
        Generates an AccountConfiguration instance with a randomly-generated username.

        The username will be generated with lowercase letters and numbers.

        :param length: determines the length of the randomly-generated username.
        """
        char_space = string.ascii_lowercase + string.digits
        username = "".join(random.choices(char_space, k=length))
        return cls(username, None)
