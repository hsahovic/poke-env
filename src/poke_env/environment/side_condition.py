# -*- coding: utf-8 -*-
"""This module defines the SideCondition class, which represents a in-battle side
condition.
"""
from enum import Enum, unique, auto


@unique
class SideCondition(Enum):
    """Enumeration, represent a in-battle side condition."""

    AURORA_VEIL = auto()
    LIGHT_SCREEN = auto()
    REFLECT = auto()
    SAFEGUARD = auto()
    SPIKES = auto()
    STEALTH_ROCK = auto()
    STICKY_WEB = auto()
    TAILWIND = auto()
    TOXIC_SPIKES = auto()

    def __str__(self) -> str:
        return f"{self.name} (side condition) object"

    @staticmethod
    def from_showdown_message(message):
        """Returns the SideCondition object corresponding to the message.

        :param message: The message to convert.
        :type message: str
        :return: The corresponding SideCondition object.
        :rtype: SideCondition
        """
        message = message.replace("move: ", "")
        message = message.replace(" ", "_")
        return SideCondition[message.upper()]
