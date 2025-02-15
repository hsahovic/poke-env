"""This module contains objects related to player configuration."""

from __future__ import annotations

import random
import string
from typing import NamedTuple, Optional


class AccountConfiguration(NamedTuple):
    """Player configuration object. Represented with a tuple with two entries: username and
    password."""

    username: str
    password: Optional[str]

    @classmethod
    def generate_config(cls, length: int) -> AccountConfiguration:
        char_space = string.ascii_lowercase + string.digits
        username = "".join(random.choices(char_space, k=length))
        return AccountConfiguration(username, None)
