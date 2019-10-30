# -*- coding: utf-8 -*-
from poke_env.environment.pokemon_type import PokemonType

import pytest


def test_number_of_PokemonTypes():
    assert len(list(PokemonType)) == 18


def test_existence_of_some_PokemonTypes():
    assert PokemonType.FIRE
    assert PokemonType.DARK
    assert PokemonType["WATER"]
    assert PokemonType["DRAGON"]

    with pytest.raises(KeyError):
        assert PokemonType["IMAGINARY_PokemonType"]

    with pytest.raises(AttributeError):
        assert PokemonType.IMAGINARY_PokemonType


def test_damage_multiplier_immunity_simple_PokemonType():
    assert PokemonType.NORMAL.damage_multiplier(PokemonType.GHOST) == 0
    assert PokemonType.ELECTRIC.damage_multiplier(PokemonType.GROUND) == 0


def test_damage_multiplier_immunity_double_PokemonType():
    assert (
        PokemonType.NORMAL.damage_multiplier(PokemonType.GHOST, PokemonType.NORMAL) == 0
    )
    assert (
        PokemonType.NORMAL.damage_multiplier(PokemonType.NORMAL, PokemonType.GHOST) == 0
    )

    assert (
        PokemonType.ELECTRIC.damage_multiplier(PokemonType.GROUND, PokemonType.WATER)
        == 0
    )
    assert (
        PokemonType.ELECTRIC.damage_multiplier(PokemonType.WATER, PokemonType.GROUND)
        == 0
    )


def test_damage_multiplier_weakness_simple_PokemonType():
    assert PokemonType.BUG.damage_multiplier(PokemonType.FLYING) == 0.5


def test_damage_multiplier_weakness_double_PokemonType():
    assert (
        PokemonType.BUG.damage_multiplier(PokemonType.FLYING, PokemonType.FIGHTING)
        == 0.25
    )
    assert (
        PokemonType.BUG.damage_multiplier(PokemonType.FIGHTING, PokemonType.FLYING)
        == 0.25
    )


def test_damage_multiplier_strength_simple_PokemonType():
    assert PokemonType.WATER.damage_multiplier(PokemonType.FIRE) == 2


def test_damage_multiplier_strength_double_PokemonType():
    assert (
        PokemonType.WATER.damage_multiplier(PokemonType.FIRE, PokemonType.GROUND) == 4
    )
    assert (
        PokemonType.WATER.damage_multiplier(PokemonType.GROUND, PokemonType.FIRE) == 4
    )


def test_damage_multiplier_compensating_double_PokemonType():
    assert PokemonType.WATER.damage_multiplier(PokemonType.FIRE, PokemonType.GRASS) == 1
    assert PokemonType.WATER.damage_multiplier(PokemonType.GRASS, PokemonType.FIRE) == 1


def test_types_str():
    assert str(PokemonType.WATER) == "WATER (pokemon type) object"
    assert str(PokemonType.NORMAL) == "NORMAL (pokemon type) object"
