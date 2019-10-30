# -*- coding: utf-8 -*-
from enum import Enum, unique, auto


@unique
class Weather(Enum):
    """Represent a non null weather in a battle."""

    DESOLATELAND = auto()
    HAIL = auto()
    PRIMORDIALSEA = auto()
    RAINDANCE = auto()
    SANDSTORM = auto()
    SUNNYDAY = auto()

    def __str__(self) -> str:
        return f"{self.name} (weather) object"
