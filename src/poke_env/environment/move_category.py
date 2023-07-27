"""This module defines the MoveCategory class, which represents a move category.
"""
from enum import Enum, auto, unique


@unique
class MoveCategory(Enum):
    """Enumeration, represent a move category."""

    PHYSICAL = auto()
    SPECIAL = auto()
    STATUS = auto()

    def __str__(self) -> str:
        return f"{self.name} (move category) object"
