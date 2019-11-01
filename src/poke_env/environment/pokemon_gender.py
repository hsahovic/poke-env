# -*- coding: utf-8 -*-
"""This module defines the PokemonGender class, which represents the gender of a
Pokemon.
"""
from enum import Enum, unique, auto
from poke_env.exceptions import ShowdownException


@unique
class PokemonGender(Enum):
    """Enumeration, represent a pokemon's gender."""

    FEMALE = auto()
    MALE = auto()
    NEUTRAL = auto()

    def __str__(self) -> str:
        return f"{self.name} (pokemon gender) object"

    @staticmethod
    def from_request_details(gender: str) -> "PokemonGender":
        """Returns the PokemonGenre object corresponding to the gender received in a message.

        :param gender: The received gender to convert.
        :type gender: str
        :return: The corresponding PokemonGenre object.
        :rtype: PokemonGenre
        """
        if gender == "M":
            return PokemonGender.MALE
        elif gender == "F":
            return PokemonGender.FEMALE
        raise ShowdownException("Unmanaged request gender: '%s'", gender)
