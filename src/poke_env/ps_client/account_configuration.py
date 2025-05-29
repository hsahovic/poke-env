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
    def generate(cls, key: str, rand: bool = False) -> AccountConfiguration:
        """
        Generates an AccountConfiguration instance using a provided key.
        The same key can be used multiple times to create multiple usernames.

        :param key: The base of the username. Will be truncated to be a maximum
            of 18 characters long.
        :param rand: If true, the unique identifier appended to the end will be a
            randomized 5-length alphanumeric string instead of an increment for every
            identical key.
        """
        if rand:
            char_space = string.ascii_lowercase + string.digits
            unique_ident = "".join(random.choices(char_space, k=5))
        else:
            CONFIGURATION_FROM_PLAYER_COUNTER.update([key])
            unique_ident = str(CONFIGURATION_FROM_PLAYER_COUNTER[key])
        username = f"{key} {unique_ident}"
        if len(username) > 18:
            username = f"{key[: 18 - len(username)]} {unique_ident}"
        return cls(username, None)
