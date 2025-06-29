import pytest

from poke_env import ShowdownException
from poke_env.battle import (
    Effect,
    Field,
    Move,
    MoveCategory,
    Pokemon,
    PokemonGender,
    SideCondition,
    Status,
    Target,
    Weather,
)
from poke_env.data import GenData


def move_generator():
    for move in GenData.from_gen(9).moves:
        yield Move(move, gen=9)
        yield Move("z" + move, gen=9)


def test_effect_str():
    assert str(Effect["TRICK"])


def test_effect_build():
    assert Effect["TRICK"] == Effect.from_showdown_message("move: trick")
    assert Effect["MUMMY"] == Effect.from_showdown_message("ability: mummy")
    assert Effect["CUSTAP_BERRY"] == Effect.from_showdown_message("item: custap berry")
    assert Effect["UNKNOWN"] == Effect.from_showdown_message("i don't know")

    assert Effect["HEAL_BLOCK"] == Effect.from_data("healblock")

    assert Effect["FEINT"].breaks_protect
    assert not Effect["HEAL_BLOCK"].breaks_protect

    assert Effect["HEAL_BLOCK"].is_turn_countable
    assert not Effect["FEINT"].is_turn_countable

    assert Effect["RAGE"].is_action_countable
    assert not Effect["HEAL_BLOCK"].is_action_countable

    assert Effect["FLINCH"].is_volatile_status
    assert not Effect["TERA_SHELL"].is_volatile_status

    assert Effect["TERA_SHELL"].is_from_ability
    assert not Effect["HEAL_BLOCK"].is_from_ability

    assert Effect["CUSTAP_BERRY"].is_from_item
    assert not Effect["HEAL_BLOCK"].is_from_item

    assert Effect["OCTOLOCK"].is_from_move
    assert not Effect["TERA_SHELL"].is_from_move

    assert Effect["DESTINY_BOND"].ends_on_move
    assert not Effect["HEAL_BLOCK"].ends_on_move

    assert Effect.from_data("i dont know") == Effect.UNKNOWN

    # By going through all moves, we know we have an Effect for every Volatile Status
    # Simultaneously, store all Volatile Statuses we see to ensure we have one for each
    volatile_statuses = set()
    for move in move_generator():
        if move.volatile_status:
            volatile_statuses.add(move.volatile_status)

    assert volatile_statuses == set(
        filter(lambda x: x.is_volatile_status, list(Effect))
    )

    # These Effects aren't directly from moves, items or abilities
    no_effects = [
        Effect.FALLEN,
        Effect.FALLEN1,
        Effect.FALLEN2,
        Effect.FALLEN3,
        Effect.FALLEN4,
        Effect.FALLEN5,
        Effect.UNKNOWN,
        Effect.DYNAMAX,
    ]

    # Test we have good coverage of Effects
    for effect in list(Effect):
        if effect not in no_effects:
            assert (
                effect.is_volatile_status
                or effect.is_from_ability
                or effect.is_from_item
                or effect.is_from_move
            )


def test_effect_end():
    furret = Pokemon(gen=9, species="furret")
    furret._effects = {
        Effect.GLAIVE_RUSH: 1,
        Effect.CHARGE: 1,
        Effect.QUASH: 1,
        Effect.MUMMY: 1,
    }
    furret.moved("followme")

    assert Effect.GLAIVE_RUSH not in furret.effects
    assert Effect.CHARGE in furret.effects

    furret.moved("zapcannon")
    assert Effect.CHARGE not in furret.effects

    # Test end on turn
    furret.end_turn()
    assert Effect.QUASH not in furret.effects

    # Test end on switch
    furret.switch_out()
    assert Effect.MUMMY not in furret.effects

    # Test the definition of Volatile Status
    for effect in list(Effect):
        if effect.is_volatile_status:
            assert effect.ends_on_switch

    furret.switch_in()
    furret.start_effect("feint")
    furret.faint()
    assert furret.effects == {}


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
    assert Field["UNKNOWN"] == Field.from_showdown_message("weird thing")


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
    assert SideCondition["UNKNOWN"] == SideCondition.from_showdown_message("whatever")


def test_weather_str():
    assert str(Weather["HAIL"])
    assert Weather.SNOW == Weather.SNOWSCAPE
    assert Weather["UNKNOWN"] == Weather.from_showdown_message("hehehe")


def test_target_str():
    assert str(Target["ALL"])


def test_target_build():
    assert Target["ALLIES"] == Target.from_showdown_message("allies")
