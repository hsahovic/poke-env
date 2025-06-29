import pytest

from poke_env.battle import PokemonType
from poke_env.data import GenData


def test_number_of_PokemonTypes():
    assert len(list(PokemonType)) == 20


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
    assert (
        PokemonType.NORMAL.damage_multiplier(
            PokemonType.GHOST, type_chart=GenData.from_gen(8).type_chart
        )
        == 0
    )
    assert (
        PokemonType.ELECTRIC.damage_multiplier(
            PokemonType.GROUND, type_chart=GenData.from_gen(8).type_chart
        )
        == 0
    )


def test_damage_multiplier_immunity_double_PokemonType():
    assert (
        PokemonType.NORMAL.damage_multiplier(
            PokemonType.GHOST,
            PokemonType.NORMAL,
            type_chart=GenData.from_gen(8).type_chart,
        )
        == 0
    )
    assert (
        PokemonType.NORMAL.damage_multiplier(
            PokemonType.NORMAL,
            PokemonType.GHOST,
            type_chart=GenData.from_gen(8).type_chart,
        )
        == 0
    )

    assert (
        PokemonType.ELECTRIC.damage_multiplier(
            PokemonType.GROUND,
            PokemonType.WATER,
            type_chart=GenData.from_gen(8).type_chart,
        )
        == 0
    )
    assert (
        PokemonType.ELECTRIC.damage_multiplier(
            PokemonType.WATER,
            PokemonType.GROUND,
            type_chart=GenData.from_gen(8).type_chart,
        )
        == 0
    )


def test_damage_multiplier_weakness_simple_PokemonType():
    assert (
        PokemonType.BUG.damage_multiplier(
            PokemonType.FLYING, type_chart=GenData.from_gen(8).type_chart
        )
        == 0.5
    )


def test_damage_multiplier_weakness_double_PokemonType():
    assert (
        PokemonType.BUG.damage_multiplier(
            PokemonType.FLYING,
            PokemonType.FIGHTING,
            type_chart=GenData.from_gen(8).type_chart,
        )
        == 0.25
    )
    assert (
        PokemonType.BUG.damage_multiplier(
            PokemonType.FIGHTING,
            PokemonType.FLYING,
            type_chart=GenData.from_gen(8).type_chart,
        )
        == 0.25
    )


def test_damage_multiplier_strength_simple_PokemonType():
    assert (
        PokemonType.WATER.damage_multiplier(
            PokemonType.FIRE, type_chart=GenData.from_gen(8).type_chart
        )
        == 2
    )


def test_damage_multiplier_strength_double_PokemonType():
    assert (
        PokemonType.WATER.damage_multiplier(
            PokemonType.FIRE,
            PokemonType.GROUND,
            type_chart=GenData.from_gen(8).type_chart,
        )
        == 4
    )
    assert (
        PokemonType.WATER.damage_multiplier(
            PokemonType.GROUND,
            PokemonType.FIRE,
            type_chart=GenData.from_gen(8).type_chart,
        )
        == 4
    )


def test_damage_multiplier_compensating_double_PokemonType():
    assert (
        PokemonType.WATER.damage_multiplier(
            PokemonType.FIRE,
            PokemonType.GRASS,
            type_chart=GenData.from_gen(8).type_chart,
        )
        == 1
    )
    assert (
        PokemonType.WATER.damage_multiplier(
            PokemonType.GRASS,
            PokemonType.FIRE,
            type_chart=GenData.from_gen(8).type_chart,
        )
        == 1
    )


def test_types_str():
    assert str(PokemonType.WATER) == "WATER (pokemon type) object"
    assert str(PokemonType.NORMAL) == "NORMAL (pokemon type) object"


def test_three_question_marks_damage_multiplier():
    for type in PokemonType:
        for gen in range(1, 5):
            assert (
                PokemonType.THREE_QUESTION_MARKS.damage_multiplier(
                    type, type_chart=GenData.from_gen(gen).type_chart
                )
                == 1
            )
            assert (
                type.damage_multiplier(
                    PokemonType.THREE_QUESTION_MARKS,
                    type_chart=GenData.from_gen(gen).type_chart,
                )
                == 1
            )
