# -*- coding: utf-8 -*-
import pytest

from unittest.mock import MagicMock

from poke_env.data import POKEDEX
from poke_env.environment.battle import Battle
from poke_env.environment.effect import Effect
from poke_env.environment.field import Field
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.side_condition import SideCondition
from poke_env.environment.status import Status
from poke_env.environment.weather import Weather


def test_battle_get_pokemon():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

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
        print(battle.get_pokemon("p2: pikachu"))

    assert "p2: pikachu" not in battle.team


def test_battle_side_start_end():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)
    battle._player_role = "p1"

    assert not battle.side_conditions

    condition = "safeguard"
    battle._parse_message(["", "-sidestart", "p1", condition])
    battle._parse_message(["", "-sidestart", "p2", condition])
    assert battle.side_conditions == {SideCondition.SAFEGUARD: 0}
    assert battle.opponent_side_conditions == {SideCondition.SAFEGUARD: 0}
    battle._parse_message(["", "-sidestart", "p1", condition])
    assert battle.side_conditions == {SideCondition.SAFEGUARD: 0}

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
    assert battle.fields == {Field.ELECTRIC_TERRAIN: 0}

    battle._parse_message(["", "-fieldstart", "Trick room"])
    assert battle.fields == {Field.ELECTRIC_TERRAIN: 0, Field.TRICK_ROOM: 0}

    battle._parse_message(["", "-fieldend", "Trick room"])
    assert battle.fields == {Field.ELECTRIC_TERRAIN: 0}

    battle._parse_message(["", "-fieldend", "Electric terrain"])
    assert not battle.fields

    with pytest.raises(Exception):
        battle._parse_message(["", "-fieldend", "Electric terrain"])

    with pytest.raises(Exception):
        battle._parse_message(["", "-fieldend", "non existent field"])


def test_battle_weather_interactions():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

    assert battle.weather == {}

    battle._parse_message(["", "-weather", "desolateland"])
    assert battle.weather == {Weather.DESOLATELAND: 0}

    battle._parse_message(["", "-weather", "hail"])
    assert battle.weather == {Weather.HAIL: 0}

    battle._parse_message(["", "-weather", "none"])
    assert battle.weather == {}


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

    assert mon.species == "venusaur"
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
        "venusaur",
        "morpeko",
        "unfezant",
        "giratina",
        "necrozma",
        "marshadow",
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
    assert mon.level == 82

    assert battle.active_pokemon.species == "necrozma"
    assert battle.active_pokemon.status == Status.TOX

    battle._parse_message(["", "-curestatus", "p2: Necrozma", "par"])
    assert battle.active_pokemon.status == Status.TOX

    battle._parse_message(["", "-curestatus", "p2: Necrozma", "tox"])
    assert not battle.active_pokemon.status

    battle._parse_message(["", "switch", "p1: Gabite", "Gabite, L99, F", "311/311"])
    assert battle.opponent_active_pokemon.species == "gabite"
    assert battle.opponent_active_pokemon.level == 99
    assert battle._parse_message(["", "-supereffective"]) is None

    battle._parse_message(["", "-activate", "p2: Necrozma", "leech seed"])
    leech_seed_effect = Effect.from_showdown_message("leech seed")
    assert leech_seed_effect in battle.active_pokemon.effects

    cleared_boosts = {
        "accuracy": 0,
        "atk": 0,
        "def": 0,
        "evasion": 0,
        "spa": 0,
        "spd": 0,
        "spe": 0,
    }
    some_boosts = {
        "accuracy": -6,
        "atk": 6,
        "def": -1,
        "evasion": 1,
        "spa": 4,
        "spd": -3,
        "spe": 2,
    }
    assert battle.active_pokemon.boosts == cleared_boosts

    battle._parse_message(["", "switch", "p1: Tyranitar", "Tyranitar, L82", "100/100"])
    battle.active_pokemon._boosts = some_boosts
    battle._parse_message(["", "-copyboost", "p2: Necrozma", "p1: Tyranitar"])
    assert battle.opponent_active_pokemon.boosts == some_boosts

    assert battle.active_pokemon.current_hp == 121
    battle._parse_message(["", "-damage", "p2: Necrozma", "10/293"])
    assert battle.active_pokemon.current_hp == 10
    battle._parse_message(["", "-damage", "p2: Necrozma", "10/293g"])
    assert battle.active_pokemon.current_hp == 10

    assert battle.active_pokemon.ability is not None
    battle._parse_message(["", "-endability", "p2: Necrozma"])
    assert battle.active_pokemon.ability is None

    battle.active_pokemon.item = "focussash"
    battle._parse_message(["", "-enditem", "p2: Necrozma", "focussash"])
    assert battle.active_pokemon.item is None

    assert battle.opponent_active_pokemon.base_stats["atk"] == 134
    battle._parse_message(["", "detailschange", "p1: Tyranitar", "Tyranitar-Mega, L82"])
    assert battle.opponent_active_pokemon.base_stats["atk"] == 164

    battle._parse_message(["", "-heal", "p2: Necrozma", "293/293"])
    assert battle.active_pokemon.current_hp == 293

    boosts_before_invertion = battle.opponent_active_pokemon.boosts.copy()
    battle._parse_message(["", "-invertboost", "p1: Tyranitar"])
    for stat, boost in battle.opponent_active_pokemon.boosts.items():
        assert boost == -boosts_before_invertion[stat]

    battle._parse_message(
        [
            "",
            "-item",
            "p1: Tyranitar",
            "Tyranitarite",
            "[from] ability: Frisk",
            "[of] p2: Necrozma",
            "[identify]",
        ]
    )
    assert battle.opponent_active_pokemon.item == "tyranitarite"

    battle._parse_message(["", "switch", "p1: Latias", "Latias, L82", "100/100"])
    assert battle.opponent_active_pokemon.base_stats["def"] == 90
    battle._parse_message(["", "-mega", "p1: Latias", "latiasite"])
    assert battle.opponent_active_pokemon.species == "latias"
    assert battle.opponent_active_pokemon.base_stats["def"] == 120

    battle._parse_message(["", "-mustrecharge", "p1: Latias"])
    assert battle.opponent_active_pokemon.must_recharge is True

    battle._parse_message(["", "-prepare", "p1: Latias", "Solar Beam", "p2: Necrozma"])
    move, target = battle.opponent_active_pokemon._preparing
    assert move == "Solar Beam"
    assert target.species == "necrozma"

    battle._parse_message(["", "switch", "p1: Groudon", "Groudon, L82", "100/100"])
    battle._parse_message(["", "-primal", "p1: Groudon"])
    assert battle.opponent_active_pokemon.species == "groudon"

    battle._parse_message(["", "-setboost", "p1: Groudon", "atk", "6"])
    assert battle.opponent_active_pokemon.boosts["atk"] == 6

    assert battle.opponent_active_pokemon.current_hp == 100
    battle._parse_message(["", "-sethp", "p1: Groudon", "99/100"])
    assert battle.opponent_active_pokemon.current_hp == 99

    battle._parse_message(["", "-status", "p1: Groudon", "tox"])
    assert battle.opponent_active_pokemon.status == Status.TOX

    battle.active_pokemon.boosts["atk"] = 0
    battle.active_pokemon.boosts["def"] = 3
    battle.active_pokemon.boosts["spe"] = -1
    battle.opponent_active_pokemon.boosts["atk"] = 6
    battle.opponent_active_pokemon.boosts["def"] = -2
    battle.opponent_active_pokemon.boosts["spe"] = 0
    battle._parse_message(["", "-swapboost", "p1: Groudon", "p2: Necrozma", "atk, def"])
    assert battle.active_pokemon.boosts["atk"] == 6
    assert battle.active_pokemon.boosts["def"] == -2
    assert battle.active_pokemon.boosts["spe"] == -1
    assert battle.opponent_active_pokemon.boosts["atk"] == 0
    assert battle.opponent_active_pokemon.boosts["def"] == 3
    assert battle.opponent_active_pokemon.boosts["spe"] == 0

    battle._parse_message(["", "-transform", "p1: Groudon", "p2: Necrozma"])
    assert battle.opponent_active_pokemon.species == "groudon"
    assert battle.opponent_active_pokemon.base_stats == POKEDEX["necrozma"]["baseStats"]
    assert battle.opponent_active_pokemon.boosts == battle.active_pokemon.boosts

    battle._parse_message(["", "switch", "p1: Sunflora", "Sunflora, L82", "100/100"])
    battle.opponent_active_pokemon._boosts = cleared_boosts.copy()
    battle.opponent_active_pokemon._boosts["atk"] = 4
    battle._parse_message(["", "-unboost", "p1: Sunflora", "atk", "5"])
    assert battle.opponent_active_pokemon._boosts["atk"] == -1

    battle.opponent_active_pokemon.item = "grassiumz"
    battle._parse_message(["", "-zpower", "p1: Sunflora"])
    assert battle.opponent_active_pokemon.item is None

    sunflora = battle.opponent_active_pokemon
    assert sunflora.fainted is False
    battle._parse_message(["", "faint", "p1: Sunflora"])
    assert sunflora.fainted is True

    battle._parse_message(["", "switch", "p1: Groudon", "Groudon, L82", "100/100"])
    battle._parse_message(
        ["", "move", "p1: Groudon", "Precipice Blades", "p2: Necrozma"]
    )
    assert "precipiceblades" in battle.opponent_active_pokemon.moves

    battle._player_username = "ray"
    battle._opponent_username = "wolfe"
    battle._parse_message(
        [
            "",
            "raw",
            "ray's rating: 1049 &rarr; <strong>1079</strong><br />(+30 for winning)",
        ]
    )
    assert battle.rating == 1049
    battle._parse_message(
        [
            "",
            "raw",
            "wolfe's rating: 1025 &rarr; <strong>1012</strong><br />(-13 for losing)",
        ]
    )
    assert battle.opponent_rating == 1025

    battle._in_team_preview = True
    battle._parse_message(["", "start"])
    assert battle._in_team_preview is False

    with pytest.raises(NotImplementedError) as excinfo:
        msg_type = "bad message type that should raise an exception"
        battle._parse_message(["", msg_type])
    assert msg_type in str(excinfo.value)


def test_end_illusion():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)
    empty_boosts = {
        "accuracy": 0,
        "atk": 0,
        "def": 0,
        "evasion": 0,
        "spa": 0,
        "spd": 0,
        "spe": 0,
    }
    non_empty_boosts = {
        "accuracy": 1,
        "atk": 0,
        "def": -2,
        "evasion": 3,
        "spa": 5,
        "spd": -6,
        "spe": 2,
    }

    battle._player_role = "p2"
    battle._switch("p2: Celebi", "Celebi", "100/100")
    battle._switch("p1: Kingdra", "Kingdra, F", "100/100")
    battle.active_pokemon._boosts = non_empty_boosts

    assert battle.active_pokemon.species == "celebi"

    battle._parse_message(["", "replace", "p2: Zoroark", "Zoroark, M"])

    assert battle.active_pokemon.species == "zoroark"
    assert battle.opponent_active_pokemon.species == "kingdra"
    assert battle.get_pokemon("p2: Zoroark").boosts == non_empty_boosts
    assert battle.get_pokemon("p2: Celebi").boosts == empty_boosts
