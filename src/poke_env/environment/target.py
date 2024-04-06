"""This module defines the Target class, which represents the types of
targets a move can have
"""

import logging
from enum import Enum, unique, auto

# This is an enum for all the targets you can have
@unique
class Target(Enum):
    """Enumeration, representing targets for each move
    in a battle."""

    UNKNOWN = auto()
    ADJACENTALLY = auto()
    ADJACENTALLYORSELF = auto()
    ADJACENTFOE = auto()
    ALL = auto()
    ALLADJACENT = auto()
    ALLADJACENTFOES = auto()
    ALLIES = auto()
    ALLYSIDE = auto()
    ALLYTEAM = auto()
    ANY = auto()
    FOESIDE = auto()
    NORMAL = auto()
    RANDOMNORMAL = auto()
    SCRIPTED = auto()
    SELF = auto()

    def __str__(self) -> str:
        return f"{self.name} (target) object"

    @staticmethod
    def from_showdown_message(message: str):
        """Returns the Target object corresponding to the message.

        :param message: The message to convert.
        :type message: str
        :return: The corresponding Target object.
        :rtype: Target
        """
        message = message.replace("move: ", "")
        message = message.replace(" ", "_")
        message = message.replace("-", "_")

        try:
            return Target[message.upper()]
        except KeyError:
            logging.getLogger("poke-env").warning(
                "Unexpected Target '%s' received. Target.UNKNOWN will be used "
                "instead. If this is unexpected, please open an issue at "
                "https://github.com/hsahovic/poke-env/issues/ along with this error "
                "message and a description of your program.",
                message,
            )
            return Target.UNKNOWN
