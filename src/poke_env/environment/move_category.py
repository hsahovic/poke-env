# -*- coding: utf-8 -*-
from enum import Enum, unique, auto


@unique
class MoveCategory(Enum):
    """Represent a move category."""

    PHYSICAL = auto()
    SPECIAL = auto()
    STATUS = auto()

    def __str__(self) -> str:
        return f"{self.name} (move category) object"
