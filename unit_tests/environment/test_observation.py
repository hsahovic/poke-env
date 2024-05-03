from unittest.mock import MagicMock

from poke_env.environment import Battle, Field, Observation, SideCondition, Weather


def test_observation(example_request):
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.parse_request(example_request)
    mon = battle.active_pokemon
    battle._opponent_team = {mon.species: mon}

    # Finish a turn and record the observation
    battle.parse_message(["", "turn", "7"])
    assert 7 in battle.observations
    assert battle.observations[7].opponent_team[mon.species] == mon

    assert len(battle._current_observation.weather) == 0
    assert len(battle._current_observation.fields) == 0
    assert len(battle._current_observation.fields) == 0

    battle.parse_message(["", "-weather", "SunnyDay"])
    battle.parse_message(["", "-fieldstart", "move: Grassy Terrain"])
    battle.parse_message(["", "-sidestart", "p2: RandomPlayer 3", "move: Tailwind"])
    battle.parse_message(["", "-sidestart", "p1: EliteFurretAI", "move: Tailwind"])
    battle.parse_message(["", "-sidestart", "p1: EliteFurretAI", "move: Reflect"])

    # Observations only get populated and stored at the end of the turn
    # But events get captured as turns happen
    assert Weather.SUNNYDAY not in battle._current_observation.weather
    assert ["", "-weather", "SunnyDay"] in battle._current_observation.events

    # End turn and store Observation
    battle.parse_message(["", "turn", "8"])

    # Check Observations
    assert 7 in battle.observations
    assert 8 in battle.observations
    assert Weather.SUNNYDAY not in battle.observations[7].weather
    assert Weather.SUNNYDAY in battle.observations[8].weather
    assert Field.GRASSY_TERRAIN in battle.observations[8].fields
    assert SideCondition.TAILWIND in battle.observations[8].opponent_side_conditions
    assert SideCondition.REFLECT in battle.observations[8].opponent_side_conditions
    assert [
        "",
        "-sidestart",
        "p1: EliteFurretAI",
        "move: Reflect",
    ] in battle.observations[8].events

    # Check to see if we restarted the observation in the new turn
    assert battle._current_observation == Observation()
