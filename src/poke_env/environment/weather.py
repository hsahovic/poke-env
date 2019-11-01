# -*- coding: utf-8 -*-
"""This module defines the Weather class, which represents a in-battle weather.
"""
from enum import Enum, unique, auto


@unique
class Weather(Enum):
    """Enumeration, represent a non null weather in a battle."""

    DESOLATELAND = auto()
    HAIL = auto()
    PRIMORDIALSEA = auto()
    RAINDANCE = auto()
    SANDSTORM = auto()
    SUNNYDAY = auto()

    def __str__(self) -> str:
        return f"{self.name} (weather) object"
