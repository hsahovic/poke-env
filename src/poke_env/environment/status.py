# -*- coding: utf-8 -*-
"""This module defines the Status class, which represents statuses a pokemon can be
afflicted with.
"""
from enum import Enum, unique, auto


@unique
class Status(Enum):
    """Enumeration, represent a status a pokemon can be afflicted with."""

    BRN = auto()
    FNT = auto()
    FRZ = auto()
    PAR = auto()
    PSN = auto()
    SLP = auto()
    TOX = auto()

    def __str__(self) -> str:
        return f"{self.name} (status) object"
