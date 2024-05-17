"""This module defines the Target class, which represents the types of
targets a move can have
"""

import logging
import re
from enum import Enum, auto, unique


# This is an enum for all the targets you can have
@unique
class Target(Enum):
    """Enumeration, representing targets for each move
    in a battle."""

    ADJACENT_ALLY = auto()
    ADJACENT_ALLY_OR_SELF = auto()
    ADJACENT_FOE = auto()
    ALL = auto()
    ALL_ADJACENT = auto()
    ALL_ADJACENT_FOES = auto()
    ALLIES = auto()
    ALLY_SIDE = auto()
    ALLY_TEAM = auto()
    ANY = auto()
    FOE_SIDE = auto()
    NORMAL = auto()
    RANDOM_NORMAL = auto()
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
            # Converts Camel Case targets to readable targets above
            tokens = re.sub("([A-Z]+)", r" \1", message).split()
            return Target["_".join(tokens).upper()]
        except KeyError:
            logging.getLogger("poke-env").error(
                "Unexpected Target '%s' received. If this is unexpected, please"
                "open an issue at https://github.com/hsahovic/poke-env/issues/"
                "along with this error message and a description of your "
                "program.",
                message,
            )
            raise KeyError
