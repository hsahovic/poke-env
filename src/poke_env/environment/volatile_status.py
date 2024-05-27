# -*- coding: utf-8 -*-
"""This module defines the VolatileStatus class, which represents a field a Move
can have.
"""
from __future__ import annotations

# pyre-ignore-all-errors[45]
from enum import Enum, auto, unique


# This is an enum for all the Volatile Statuses a move can have
@unique
class VolatileStatus(Enum):
    """Enumeration, represent a volatilestatus a move can have."""

    FORESIGHT = auto()
    DISABLE = auto()
    SMACKDOWN = auto()
    CURSE = auto()
    NIGHTMARE = auto()
    TARSHOT = auto()
    LOCKEDMOVE = auto()
    BIDE = auto()
    SNATCH = auto()
    ENCORE = auto()
    SPOTLIGHT = auto()
    LASERFOCUS = auto()
    ELECTRIFY = auto()
    SILKTRAP = auto()
    HEALBLOCK = auto()
    MIRACLEEYE = auto()
    ATTRACT = auto()
    DESTINYBOND = auto()
    RAGE = auto()
    AQUARING = auto()
    TAUNT = auto()
    TELEKINESIS = auto()
    GRUDGE = auto()
    SYRUPBOMB = auto()
    YAWN = auto()
    IMPRISON = auto()
    MAGICCOAT = auto()
    STOCKPILE = auto()
    DEFENSECURL = auto()
    EMBARGO = auto()
    FOLLOWME = auto()
    GLAIVERUSH = auto()
    CONFUSION = auto()
    INGRAIN = auto()
    BANEFULBUNKER = auto()
    PROTECT = auto()
    GASTROACID = auto()
    POWERTRICK = auto()
    TORMENT = auto()
    BURNINGBULWARK = auto()
    DRAGONCHEER = auto()
    SPARKLINGARIA = auto()
    HELPINGHAND = auto()
    FLINCH = auto()
    OCTOLOCK = auto()
    PARTIALLYTRAPPED = auto()
    KINGSSHIELD = auto()
    MINIMIZE = auto()
    NORETREAT = auto()
    CHARGE = auto()
    MUSTRECHARGE = auto()
    MAGNETRISE = auto()
    MAXGUARD = auto()
    POWERSHIFT = auto()
    SUBSTITUTE = auto()
    RAGEPOWDER = auto()
    ROOST = auto()
    FOCUSENERGY = auto()
    SALTCURE = auto()
    LEECHSEED = auto()
    POWDER = auto()
    SPIKYSHIELD = auto()
    ENDURE = auto()
    UPROAR = auto()
    OBSTRUCT = auto()

    def __str__(self) -> str:
        return f"{self.name} (volatile status) object"

    @staticmethod
    def from_name(name: str) -> VolatileStatus:
        """Returns a volatile status based on its name.

        :param name: The name of the volatile status.
        :type name: str
        :return: The corresponding type object.
        :rtype: VolatileStatus
        """
        return VolatileStatus[name.upper()]
