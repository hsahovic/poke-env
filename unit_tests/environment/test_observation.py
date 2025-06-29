from unittest.mock import MagicMock

from poke_env.battle import (
    Battle,
    Effect,
    Field,
    Observation,
    ObservedPokemon,
    SideCondition,
    Weather,
)


def test_observation(example_request):
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    # Check to see if we have no information
    assert battle._current_observation == Observation()

    battle.parse_request(example_request)
    mon = battle.active_pokemon
    battle._opponent_team = {mon.species: mon}

    # Observations encode each turn, and encode specifically the state of the
    # battle at the beginning of each turn, and the events that happened on that turn
    battle.parse_message(["", "turn", "1"])
    battle.parse_message(["", "-weather", "Sandstorm"])
    battle.parse_message(["", "-fieldstart", "move: Grassy Terrain"])
    battle.parse_message(["", "-fieldstart", "move: Magic Room"])
    battle.parse_message(["", "-sidestart", "p2: RandomPlayer 3", "move: Tailwind"])
    battle.parse_message(["", "-sidestart", "p1: EliteFurretAI", "move: Tailwind"])
    battle.parse_message(["", "-sidestart", "p1: EliteFurretAI", "move: Reflect"])
    battle.parse_message(["", "turn", "2"])
    battle.parse_message(["", "-weather", "RainyDay"])
    battle.parse_message(["", "turn", "3"])
    battle.parse_message(["", "-weather", "SunnyDay"])
    battle.parse_message(["", ""])
    battle.tied()

    # Check all attributes of Observation, as well as if it updates the battle states
    # correctly
    assert [
        "",
        "-sidestart",
        "p1: EliteFurretAI",
        "move: Reflect",
    ] in battle.observations[1].events
    assert len(battle.observations[1].team) == 6
    assert mon.species == battle.observations[1].active_pokemon.species
    assert mon.species == battle.observations[1].opponent_active_pokemon.species
    assert battle.observations[1].opponent_team[mon.species].species == mon.species
    assert Weather.SANDSTORM not in battle.observations[1].weather

    assert SideCondition.TAILWIND in battle.observations[2].opponent_side_conditions
    assert SideCondition.TAILWIND in battle.observations[2].side_conditions
    assert SideCondition.REFLECT in battle.observations[2].opponent_side_conditions
    assert Weather.SANDSTORM in battle.observations[2].weather
    assert Field.GRASSY_TERRAIN in battle.observations[2].fields
    assert Field.MAGIC_ROOM in battle.observations[2].fields
    assert mon.species == battle.observations[2].active_pokemon.species
    assert mon != battle.observations[2].active_pokemon

    assert ["", "-weather", "SunnyDay"] in battle.observations[3].events
    assert Weather.SANDSTORM not in battle.observations[3].weather

    assert battle.observations[3].team != battle.observations[2].team
    assert ["", ""] in battle.observations[3].events


def test_observed_pokemon(example_request):
    assert ObservedPokemon.from_pokemon(None) is None

    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.parse_request(example_request)
    mon = battle.active_pokemon
    observed_mon = ObservedPokemon.from_pokemon(mon)

    assert observed_mon.species == mon.species

    assert observed_mon.ability == mon.ability
    assert observed_mon.boosts["accuracy"] == mon.boosts["accuracy"]
    assert observed_mon.boosts["atk"] == mon.boosts["atk"]
    assert observed_mon.boosts["def"] == mon.boosts["def"]
    assert observed_mon.boosts["evasion"] == mon.boosts["evasion"]
    assert observed_mon.boosts["spa"] == mon.boosts["spa"]
    assert observed_mon.boosts["spd"] == mon.boosts["spd"]
    assert observed_mon.boosts["spe"] == mon.boosts["spe"]

    observed_mon.boosts["accuracy"] = 10
    assert mon.boosts["accuracy"] != 10

    assert observed_mon.current_hp_fraction == mon.current_hp_fraction

    for effect in observed_mon.effects:
        assert observed_mon.effects[effect] == mon.effects[effect]

    observed_mon.effects[Effect.ZERO_TO_HERO] = 1
    assert Effect.ZERO_TO_HERO not in mon.effects

    assert observed_mon.is_dynamaxed == mon.is_dynamaxed
    assert observed_mon.is_terastallized == mon.is_terastallized
    assert observed_mon.item == mon.item
    assert observed_mon.gender == mon.gender

    assert observed_mon.stats["atk"] == mon.stats["atk"]
    assert observed_mon.stats["def"] == mon.stats["def"]
    assert observed_mon.stats["spa"] == mon.stats["spa"]
    assert observed_mon.stats["spd"] == mon.stats["spd"]
    assert observed_mon.stats["spe"] == mon.stats["spe"]

    assert observed_mon.level == mon.level

    # Test that we're copying the moves correctly
    assert list(observed_mon.moves.keys())[0] == list(mon.moves.keys())[0]
    mon.moves["leechseed"].use()
    assert (
        observed_mon.moves["leechseed"].current_pp
        == mon.moves["leechseed"].current_pp + 1
    )

    assert observed_mon.tera_type == mon.tera_type
    assert observed_mon.shiny == mon.shiny
    assert observed_mon.status == mon.status
