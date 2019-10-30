# -*- coding: utf-8 -*-
from enum import Enum, unique, auto


@unique
class SideCondition(Enum):
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
        message = message.replace("move: ", "")
        message = message.replace(" ", "_")
        return SideCondition[message.upper()]
