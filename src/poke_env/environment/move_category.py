# -*- coding: utf-8 -*-
"""This module defines the MoveCategory class, which represents a move category.
"""
# pyre-ignore-all-errors[45]
from enum import Enum, unique, auto


@unique
class MoveCategory(Enum):
    """Enumeration, represent a move category."""

    PHYSICAL = auto()
    SPECIAL = auto()
    STATUS = auto()

    def __str__(self) -> str:
        return f"{self.name} (move category) object"
