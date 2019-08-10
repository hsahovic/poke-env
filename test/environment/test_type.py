# -*- coding: utf-8 -*-

from pokemon_showdown_env.environment.type import Type

import pytest


def test_number_of_types():
    assert len(list(Type)) == 18


def test_existence_of_some_types():
    assert Type.FIRE
    assert Type.DARK
    assert Type["WATER"]
    assert Type["DRAGON"]

    with pytest.raises(KeyError):
        assert Type["IMAGINARY_TYPE"]

    with pytest.raises(AttributeError):
        assert Type.IMAGINARY_TYPE


def test_damage_multiplier_immunity_simple_type():
    assert Type.NORMAL.damage_multiplier(Type.GHOST) == 0
    assert Type.ELECTRIC.damage_multiplier(Type.GROUND) == 0


def test_damage_multiplier_immunity_double_type():
    assert Type.NORMAL.damage_multiplier(Type.GHOST, Type.NORMAL) == 0
    assert Type.NORMAL.damage_multiplier(Type.NORMAL, Type.GHOST) == 0

    assert Type.ELECTRIC.damage_multiplier(Type.GROUND, Type.WATER) == 0
    assert Type.ELECTRIC.damage_multiplier(Type.WATER, Type.GROUND) == 0


def test_damage_multiplier_weakness_simple_type():
    assert Type.BUG.damage_multiplier(Type.FLYING) == 0.5


def test_damage_multiplier_weakness_double_type():
    assert Type.BUG.damage_multiplier(Type.FLYING, Type.FIGHTING) == 0.25
    assert Type.BUG.damage_multiplier(Type.FIGHTING, Type.FLYING) == 0.25


def test_damage_multiplier_strength_simple_type():
    assert Type.WATER.damage_multiplier(Type.FIRE) == 2


def test_damage_multiplier_strength_double_type():
    assert Type.WATER.damage_multiplier(Type.FIRE, Type.GROUND) == 4
    assert Type.WATER.damage_multiplier(Type.GROUND, Type.FIRE) == 4


def test_damage_multiplier_compensating_double_type():
    assert Type.WATER.damage_multiplier(Type.FIRE, Type.GRASS) == 1
    assert Type.WATER.damage_multiplier(Type.GRASS, Type.FIRE) == 1
