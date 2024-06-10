"""This module defines the SideCondition class, which represents a in-battle side
condition.
"""

import logging
from enum import Enum, auto, unique
from typing import Dict


@unique
class SideCondition(Enum):
    """Enumeration, represent a in-battle side condition."""

    UNKNOWN = auto()
    AURORA_VEIL = auto()
    CRAFTY_SHIELD = auto()
    FIRE_PLEDGE = auto()
    G_MAX_CANNONADE = auto()
    G_MAX_STEELSURGE = auto()
    G_MAX_VINE_LASH = auto()
    G_MAX_VOLCALITH = auto()
    G_MAX_WILDFIRE = auto()
    GRASS_PLEDGE = auto()
    LIGHT_SCREEN = auto()
    LUCKY_CHANT = auto()
    MATBLOCK = auto()
    MIST = auto()
    QUICK_GUARD = auto()
    REFLECT = auto()
    SAFEGUARD = auto()
    SPIKES = auto()
    STEALTH_ROCK = auto()
    STICKY_WEB = auto()
    TAILWIND = auto()
    TOXIC_SPIKES = auto()
    WATER_PLEDGE = auto()
    WIDE_GUARD = auto()

    def __str__(self) -> str:
        return f"{self.name} (side condition) object"

    @staticmethod
    def from_showdown_message(message: str):
        """Returns the SideCondition object corresponding to the message.

        :param message: The message to convert.
        :type message: str
        :return: The corresponding SideCondition object.
        :rtype: SideCondition
        """
        message = message.replace("move: ", "")
        message = message.replace(" ", "_")
        message = message.replace("-", "_")

        try:
            return SideCondition[message.upper()]
        except KeyError:
            logging.getLogger("poke-env").warning(
                "Unexpected side condition '%s' received. SideCondition.UNKNOWN will be"
                " used instead. If this is unexpected, please open an issue at "
                "https://github.com/hsahovic/poke-env/issues/ along with this error "
                "message and a description of your program.",
                message,
            )
            return SideCondition.UNKNOWN

    @staticmethod
    def from_data(message: str):
        """Returns the SideCondition object corresponding to the string in static data.

        :param message: The message to convert.
        :type message: str
        :return: The corresponding SideCondition object.
        :rtype: SideCondition
        """
        message = message.replace("_", "")
        message = message.replace(" ", "")
        message = message.replace("-", "")
        message = message.upper()

        try:
            return _FROM_DATA[message]
        except KeyError:
            logging.getLogger("poke-env").warning(
                "Unexpected SideCondition '%s' received. SideCondition.UNKNOWN will be used "
                "instead. If this is unexpected, please open an issue at "
                "https://github.com/hsahovic/poke-env/issues/ along with this error "
                "message and a description of your program.",
                message,
            )
            return SideCondition.UNKNOWN


# SideCondition -> Max useful stack level
STACKABLE_CONDITIONS = {SideCondition.SPIKES: 3, SideCondition.TOXIC_SPIKES: 2}

_FROM_DATA: Dict[str, SideCondition] = {
    "UNKNOWN": SideCondition.UNKNOWN,
    "AURORAVEIL": SideCondition.AURORA_VEIL,
    "CRAFTYSHIELD": SideCondition.CRAFTY_SHIELD,
    "FIREPLEDGE": SideCondition.FIRE_PLEDGE,
    "GMAXCANNONADE": SideCondition.G_MAX_CANNONADE,
    "GMAXSTEELSURGE": SideCondition.G_MAX_STEELSURGE,
    "GMAXVINELASH": SideCondition.G_MAX_VINE_LASH,
    "GMAXVOLCALITH": SideCondition.G_MAX_VOLCALITH,
    "GMAXWILDFIRE": SideCondition.G_MAX_WILDFIRE,
    "GRASSPLEDGE": SideCondition.GRASS_PLEDGE,
    "LIGHTSCREEN": SideCondition.LIGHT_SCREEN,
    "LUCKYCHANT": SideCondition.LUCKY_CHANT,
    "MATBLOCK": SideCondition.MATBLOCK,
    "MIST": SideCondition.MIST,
    "QUICKGUARD": SideCondition.QUICK_GUARD,
    "REFLECT": SideCondition.REFLECT,
    "SAFEGUARD": SideCondition.SAFEGUARD,
    "SPIKES": SideCondition.SPIKES,
    "STEALTHROCK": SideCondition.STEALTH_ROCK,
    "STICKYWEB": SideCondition.STICKY_WEB,
    "TAILWIND": SideCondition.TAILWIND,
    "TOXICSPIKES": SideCondition.TOXIC_SPIKES,
    "WATERPLEDGE": SideCondition.WATER_PLEDGE,
    "WIDEGUARD": SideCondition.WIDE_GUARD,
}
