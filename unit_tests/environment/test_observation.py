from unittest.mock import MagicMock

from poke_env.environment import Battle, Field, Observation, SideCondition, Weather


def test_observation(example_request):
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    # Check to see if we have no information
    assert battle._current_observation == Observation()

    battle.parse_request(example_request)
    mon = battle.active_pokemon
    battle._opponent_team = {mon.species: mon}

    # Observations encode each turn encode, and encode specifically the state of the
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
    battle.tied()

    # Check all attributes of Observation, as well as if it updates the battle states
    # correctly
    assert [
        "",
        "-sidestart",
        "p1: EliteFurretAI",
        "move: Reflect",
    ] in battle.observations[1].events
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

    assert ["", "-weather", "SunnyDay"] in battle.observations[3].events
    assert Weather.SANDSTORM not in battle.observations[3].weather
