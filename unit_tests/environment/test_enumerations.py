from poke_env.environment import (
    Effect,
    Field,
    MoveCategory,
    PokemonGender,
    SideCondition,
    Status,
    Weather,
)
from poke_env import ShowdownException

import pytest


def test_effect_str():
    assert str(Effect["TRICK"])


def test_effect_build():
    assert Effect["TRICK"] == Effect.from_showdown_message("move: trick")
    assert Effect["MUMMY"] == Effect.from_showdown_message("ability: mummy")
    assert Effect["CUSTAP_BERRY"] == Effect.from_showdown_message("item: custap berry")
    assert Effect["_UNKNOWN"] == Effect.from_showdown_message("i don't know")


def test_field_str():
    assert str(Field["ELECTRIC_TERRAIN"])


def test_field_is_terrain():
    terrains = {
        Field.ELECTRIC_TERRAIN,
        Field.MISTY_TERRAIN,
        Field.PSYCHIC_TERRAIN,
        Field.GRASSY_TERRAIN,
    }

    for field in Field:
        assert field.is_terrain == (field in terrains)


def test_field_build():
    assert Field["ELECTRIC_TERRAIN"] == Field.from_showdown_message("electric terrain")
    assert Field["ELECTRIC_TERRAIN"] == Field.from_showdown_message(
        "move: electric terrain"
    )
    assert Field["_UNKNOWN"] == Field.from_showdown_message("weird thing")


def test_move_category_str():
    assert str(MoveCategory["PHYSICAL"])


def test_pokemon_gender_str():
    assert str(PokemonGender["MALE"])


def test_pokemon_gender_build():
    assert PokemonGender.from_request_details("F") == PokemonGender["FEMALE"]
    assert PokemonGender.from_request_details("M") == PokemonGender["MALE"]

    with pytest.raises(ShowdownException):
        PokemonGender.from_request_details("dsfdsfd")


def test_status_str():
    assert str(Status["BRN"])


def test_side_condition_str():
    assert str(SideCondition["SPIKES"])


def test_side_condition_build():
    assert SideCondition["SPIKES"] == SideCondition.from_showdown_message("spikes")
    assert SideCondition["_UNKNOWN"] == SideCondition.from_showdown_message("whatever")


def test_weather_str():
    assert str(Weather["HAIL"])
    assert Weather["_UNKNOWN"] == Weather.from_showdown_message("hehehe")
