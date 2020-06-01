# -*- coding: utf-8 -*-
import pytest

from unittest.mock import MagicMock

from poke_env.environment.battle import Battle
from poke_env.environment.field import Field
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.side_condition import SideCondition
from poke_env.environment.status import Status
from poke_env.environment.weather import Weather


def test_battle_get_pokemon():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

    #  identifier: str, force_self_team: bool = False, details: str = ""

    battle.get_pokemon("p2: azumarill", force_self_team=True)
    assert "p2: azumarill" in battle.team

    battle._player_role = "p2"

    battle._parse_message(["", "teamsize", "p1", 6])
    battle._parse_message(["", "teamsize", "p2", 6])

    battle.get_pokemon("p2a: tapukoko")
    assert "p2: tapukoko" in battle.team

    battle.get_pokemon("p1: hydreigon", details="Hydreigon, F")
    assert "p1: hydreigon" in battle.opponent_team

    assert battle.get_pokemon("p2: tapufini").species == "tapufini"
    assert battle.get_pokemon("p2: tapubulu").types == (
        PokemonType.GRASS,
        PokemonType.FAIRY,
    )
    assert battle.get_pokemon("p2: tapulele").base_stats == {
        "atk": 85,
        "def": 75,
        "hp": 70,
        "spa": 130,
        "spd": 115,
        "spe": 95,
    }
    battle.get_pokemon("p2: yveltal")

    assert len(battle.team) == 6

    with pytest.raises(ValueError):
        battle.get_pokemon("p2: pikachu")

    assert "p2: pikachu" not in battle.team


def test_battle_side_start_end():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)
    battle._player_role = "p1"

    assert not battle.side_conditions

    condition = "safeguard"
    battle._parse_message(["", "-sidestart", "p1", condition])
    battle._parse_message(["", "-sidestart", "p2", condition])
    assert battle.side_conditions == {SideCondition.SAFEGUARD}
    assert battle.opponent_side_conditions == {SideCondition.SAFEGUARD}

    battle._parse_message(["", "-sideend", "p1", condition])
    battle._parse_message(["", "-sideend", "p2", condition])
    assert not battle.side_conditions
    assert not battle.opponent_side_conditions

    with pytest.raises(Exception):
        battle._side_end("p1", condition)

    with pytest.raises(Exception):
        battle._side_end("p2", condition)


def test_battle_field_interactions():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

    assert not battle.fields

    battle._parse_message(["", "-fieldstart", "Electric terrain"])
    assert battle.fields == {Field.ELECTRIC_TERRAIN}

    battle._parse_message(["", "-fieldstart", "Trick room"])
    assert battle.fields == {Field.ELECTRIC_TERRAIN, Field.TRICK_ROOM}

    battle._parse_message(["", "-fieldend", "Trick room"])
    assert battle.fields == {Field.ELECTRIC_TERRAIN}

    battle._parse_message(["", "-fieldend", "Electric terrain"])
    assert not battle.fields

    with pytest.raises(Exception):
        battle._parse_message(["", "-fieldend", "Electric terrain"])

    with pytest.raises(Exception):
        battle._parse_message(["", "-fieldend", "non existent field"])


def test_battle_weather_interactions():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

    assert battle.weather is None

    battle._parse_message(["", "-weather", "desolateland"])
    assert battle.weather == Weather.DESOLATELAND

    battle._parse_message(["", "-weather", "hail"])
    assert battle.weather == Weather.HAIL

    battle._parse_message(["", "-weather", "none"])
    assert battle.weather is None


def test_battle_player_role_interaction():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

    battle._parse_message(["", "player", "p4", "username", "", ""])
    assert battle._player_role == "p4"


def test_battle_tag():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

    assert battle.battle_tag == "tag"


def test_battle_request_parsing(example_request):
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

    battle._parse_request(example_request)

    mon = battle.active_pokemon

    assert mon.species == "Venusaur"
    assert mon.current_hp_fraction == 139 / 265
    assert mon.stats == {"atk": 139, "def": 183, "spa": 211, "spd": 211, "spe": 178}

    moves = mon.moves
    assert (
        len(moves) == 4
        and "leechseed" in moves
        and "sleeppowder" in moves
        and "substitute" in moves
        and "sludgebomb" in moves
    )
    assert mon.ability == "chlorophyll"

    team = battle.team

    species = {m.species for m in team.values()}
    assert species == {
        "Venusaur",
        "Morpeko",
        "Unfezant",
        "Giratina",
        "Necrozma",
        "Marshadow",
    }

    assert len(battle.available_switches) == 4
    assert len(battle.available_moves) == 4

    assert team["p2: Necrozma"].status == Status.TOX


def test_battle_request_and_interactions(example_request):
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

    battle._parse_request(example_request)
    mon = battle.active_pokemon

    battle._parse_message(["", "-boost", "p2: Venusaur", "atk", "4"])
    assert mon.boosts["atk"] == 4

    battle._parse_message(["", "-clearallboost"])
    assert mon.boosts["atk"] == 0

    battle._parse_message(["", "-boost", "p2: Venusaur", "atk", "4"])
    assert mon.boosts["atk"] == 4

    battle._parse_message(["", "-clearboost", "p2: Venusaur"])
    assert mon.boosts["atk"] == 0

    battle._parse_message(["", "-boost", "p2: Venusaur", "atk", "4"])
    assert mon.boosts["atk"] == 4

    battle._parse_message(["", "-clearpositiveboost", "p2: Venusaur"])
    assert mon.boosts["atk"] == 0

    battle._parse_message(["", "-boost", "p2: Venusaur", "atk", "4"])
    assert mon.boosts["atk"] == 4

    battle._parse_message(["", "-clearpositiveboost", "p2: Venusaur"])
    assert mon.boosts["atk"] == 0

    battle._parse_message(["", "-boost", "p2: Venusaur", "atk", "4"])
    assert mon.boosts["atk"] == 4

    battle._parse_message(["", "-clearnegativeboost", "p2: Venusaur"])
    assert mon.boosts["atk"] == 4

    battle._parse_message(
        ["", "switch", "p2: Necrozma", "Necrozma, L82", "121/293 tox"]
    )
    assert mon.boosts["atk"] == 0

    assert battle.active_pokemon.species == "Necrozma"
    assert battle.active_pokemon.status == Status.TOX

    battle._parse_message(["", "-curestatus", "p2: Necrozma", "par"])
    assert battle.active_pokemon.status == Status.TOX

    battle._parse_message(["", "-curestatus", "p2: Necrozma", "tox"])
    assert not battle.active_pokemon.status
