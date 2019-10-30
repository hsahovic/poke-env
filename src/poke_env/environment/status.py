# -*- coding: utf-8 -*-
from enum import Enum, unique, auto


@unique
class Status(Enum):
    BRN = auto()
    FNT = auto()
    FRZ = auto()
    PAR = auto()
    PSN = auto()
    SLP = auto()
    TOX = auto()

    def __str__(self) -> str:
        return f"{self.name} (status) object"
