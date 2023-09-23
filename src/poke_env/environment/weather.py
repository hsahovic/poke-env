"""This module defines the Weather class, which represents a in-battle weather.
"""
import logging
from enum import Enum, auto, unique


@unique
class Weather(Enum):
    """Enumeration, represent a non null weather in a battle."""

    UNKNOWN = auto()
    DESOLATELAND = auto()
    DELTASTREAM = auto()
    HAIL = auto()
    PRIMORDIALSEA = auto()
    RAINDANCE = auto()
    SANDSTORM = auto()
    SNOW = auto()
    SUNNYDAY = auto()

    def __str__(self) -> str:
        return f"{self.name} (weather) object"

    @staticmethod
    def from_showdown_message(message: str):
        """Returns the Weather object corresponding to the message.

        :param message: The message to convert.
        :type message: str
        :return: The corresponding Weather object.
        :rtype: Weather
        """
        message = message.replace("move: ", "")
        message = message.replace(" ", "_")
        message = message.replace("-", "_")

        try:
            return Weather[message.upper()]
        except KeyError:
            logging.getLogger("poke-env").warning(
                "Unexpected weather '%s' received. Weather.UNKNOWN will be used "
                "instead. If this is unexpected, please open an issue at "
                "https://github.com/hsahovic/poke-env/issues/ along with this error "
                "message and a description of your program.",
                message,
            )
            return Weather.UNKNOWN
