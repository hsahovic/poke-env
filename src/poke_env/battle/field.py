"""This module defines the Field class, which represents a battle field."""

from __future__ import annotations

import logging
from enum import Enum, auto, unique


@unique
class Field(Enum):
    """Enumeration, represent a non null field in a battle."""

    UNKNOWN = auto()
    ELECTRIC_TERRAIN = auto()
    FAIRY_LOCK = auto()
    GRASSY_TERRAIN = auto()
    GRAVITY = auto()
    HEAL_BLOCK = auto()
    MAGIC_ROOM = auto()
    MISTY_TERRAIN = auto()
    MUD_SPORT = auto()
    MUD_SPOT = auto()
    PSYCHIC_TERRAIN = auto()
    TRICK_ROOM = auto()
    WATER_SPORT = auto()
    WONDER_ROOM = auto()

    def __str__(self) -> str:
        return f"{self.name} (field) object"

    @staticmethod
    def from_showdown_message(message: str) -> Field:
        """Returns the Field object corresponding to the message.

        :param message: The message to convert.
        :type message: str
        :return: The corresponding Field object.
        :rtype: Field
        """
        message = message.replace("move: ", "")
        message = message.replace(" ", "_")

        if message.endswith("terrain") and not message.endswith("_terrain"):
            message = message.replace("terrain", "_terrain")

        try:
            return Field[message.upper()]
        except KeyError:
            logging.getLogger("poke-env").warning(
                "Unexpected field '%s' received. Field.UNKNOWN will be used instead. "
                "If this is unexpected, please open an issue at "
                "https://github.com/hsahovic/poke-env/issues/ along with this error "
                "message and a description of your program.",
                message,
            )
            return Field.UNKNOWN

    @property
    def is_terrain(self) -> bool:
        """Wheter this field is a terrain."""
        return self.name.endswith("_TERRAIN")
