# -*- coding: utf-8 -*-
"""This module defines the Type class, which represents a Pokemon type. Types are mainly
associated with Pokemons and moves.
"""
from enum import auto
from enum import Enum
from enum import unique
from typing import Optional
from ..utils import TYPE_CHART


@unique
class PokemonType(Enum):
    """A Pokemon type

    This enumeration represents pokemon types. Each type is an instance of this class,
    whose name corresponds to the upper case spelling of its english name (ie. FIRE).

    :param name: The type name.
    :type name: str
    """

    BUG = auto()
    DARK = auto()
    DRAGON = auto()
    ELECTRIC = auto()
    FAIRY = auto()
    FIGHTING = auto()
    FIRE = auto()
    FLYING = auto()
    GHOST = auto()
    GRASS = auto()
    GROUND = auto()
    ICE = auto()
    NORMAL = auto()
    POISON = auto()
    PSYCHIC = auto()
    ROCK = auto()
    STEEL = auto()
    WATER = auto()

    def __str__(self) -> str:
        return f"{self.name} (pokemon type) object"

    def damage_multiplier(  # pyre-ignore
        self, type_1: "PokemonType", type_2: Optional["PokemonType"] = None
    ) -> float:
        """Computes the damage multiplier from this type on a pokemon with types `type_1`
        and, optionally, `type_2`.

        :param type_1: The first type of the target.
        :type type_1: PokemonType
        :param type_2: The second type of the target. Defaults to None.
        :type type_2: PokemonType, optional
        :return: The damage multiplier from this type on a pokemon with types `type_1`
            and, optionally, `type_2`.
        :rtype: float
        """
        damage_multiplier = TYPE_CHART[self.name][type_1.name]
        if type_2 is not None:
            return damage_multiplier * TYPE_CHART[self.name][type_2.name]
        return damage_multiplier

    @staticmethod
    def from_name(name: str) -> "PokemonType":
        return PokemonType[name.upper()]
