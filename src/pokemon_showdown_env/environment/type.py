# -*- coding: utf-8 -*-
"""Type class

This file defines the Type class, which represents a Pokemon type. Types are mainly
associated with Pokemons and moves.

Classes:
    Type: A Pokemon type.
"""
from enum import Enum, unique, auto
from typing import Optional
from ..utils import TYPE_CHART


@unique
class Type(Enum):
    """A Pokemon type

    This enumeration represents pokemon types. Each type is an instance of this class,
    whose name corresponds to the upper case spelling of its english name (ie. FIRE).

    Attributes:

        name: The type name.
    """

    NORMAL = auto()
    FIRE = auto()
    FIGHTING = auto()
    WATER = auto()
    FLYING = auto()
    GRASS = auto()
    POISON = auto()
    ELECTRIC = auto()
    GROUND = auto()
    PSYCHIC = auto()
    ROCK = auto()
    ICE = auto()
    BUG = auto()
    DRAGON = auto()
    GHOST = auto()
    DARK = auto()
    STEEL = auto()
    FAIRY = auto()

    def __str__(self) -> str:
        return f"{self.name} (pokemon type) object"

    def damage_multiplier(
        self, type_1: "Type", type_2: Optional["Type"] = None
    ) -> float:
        """Computes the damage multiplier from this type on a pokemon with types type_1
        and, optionally, type_2.

        Args:

            type_1 (Type): The first type of the target.

            type_2(Optional[Type]): The second type of the target. Defaults to None.

        Return:

            damage_multiplier(float): The damage multiplier from this type on a pokemon
                with types type_1 and, optionally, type_2.
        """
        damage_multiplier = TYPE_CHART[self.name][type_1.name]
        if type_2 is not None:
            return damage_multiplier * TYPE_CHART[self.name][type_2.name]
        return damage_multiplier
