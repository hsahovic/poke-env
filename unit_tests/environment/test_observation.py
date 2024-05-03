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

    # Starting turn 1
    battle.parse_message(["", "turn", "1"])

    assert 0 in battle.observations

    assert len(battle._current_observation.weather) == 0
    assert len(battle._current_observation.fields) == 0
    assert len(battle._current_observation.fields) == 0

    battle.parse_message(["", "-weather", "Sandstorm"])
    battle.parse_message(["", "-fieldstart", "move: Grassy Terrain"])
    battle.parse_message(["", "-sidestart", "p2: RandomPlayer 3", "move: Tailwind"])
    battle.parse_message(["", "-sidestart", "p1: EliteFurretAI", "move: Tailwind"])
    battle.parse_message(["", "-sidestart", "p1: EliteFurretAI", "move: Reflect"])

    # Observation events get captured as they happen
    assert ["", "-weather", "Sandstorm"] in battle._current_observation.events

    # End turn 1 and store Observation of turn 1, going into turn 2
    battle.parse_message(["", "turn", "2"])

    assert battle.observations[1].opponent_team[mon.species] == mon
    assert [
        "",
        "-sidestart",
        "p1: EliteFurretAI",
        "move: Reflect",
    ] in battle.observations[1].events

    # End turn and stoere Observation for turn 2
    battle.parse_message(["", "turn", "3"])
    battle.parse_message(["", "-weather", "SunnyDay"])


    # Check Observations
    assert 2 in battle.observations
    assert 3 not in battle.observations
    assert Weather.SANDSTORM not in battle.observations[1].weather
    assert Weather.SANDSTORM in battle.observations[2].weather
    assert Field.GRASSY_TERRAIN in battle.observations[2].fields
    assert SideCondition.TAILWIND in battle.observations[2].opponent_side_conditions
    assert SideCondition.REFLECT in battle.observations[2].opponent_side_conditions

    # Test whether we store the last turn
    battle.tied()
    assert ["", "-weather", "SunnyDay"] in battle.observations[3].events
