import pickle
from unittest.mock import MagicMock

import pytest

from poke_env.battle import (
    Battle,
    Effect,
    Field,
    PokemonType,
    SideCondition,
    Status,
    Weather,
)
from poke_env.data import GenData


def test_battle_get_pokemon():
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.get_pokemon("p2: azumarill", force_self_team=True)
    assert "p2: azumarill" in battle.team

    battle.player_role = "p2"

    battle.parse_message(["", "teamsize", "p1", 6])
    battle.parse_message(["", "teamsize", "p2", 6])

    battle.get_pokemon("p2a: tapukoko")
    assert "p2: tapukoko" in battle.team

    battle.get_pokemon("p1: hydreigon", details="Hydreigon, F")
    assert "p1: hydreigon" in battle.opponent_team

    assert battle.get_pokemon("p2: tapufini").species == "tapufini"
    assert battle.get_pokemon("p2: tapubulu").types == [
        PokemonType.GRASS,
        PokemonType.FAIRY,
    ]
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
    battle = Battle("tag", "username", logger, gen=8)
    battle.player_role = "p1"

    assert not battle.side_conditions

    condition = "safeguard"
    battle.parse_message(["", "-sidestart", "p1", condition])
    battle.parse_message(["", "-sidestart", "p2", condition])
    assert battle.side_conditions == {SideCondition.SAFEGUARD: 0}
    assert battle.opponent_side_conditions == {SideCondition.SAFEGUARD: 0}
    battle.parse_message(["", "-sidestart", "p1", condition])
    assert battle.side_conditions == {SideCondition.SAFEGUARD: 0}

    battle.parse_message(["", "-sideend", "p1", condition])
    battle.parse_message(["", "-sideend", "p2", condition])
    assert not battle.side_conditions
    assert not battle.opponent_side_conditions

    with pytest.raises(Exception):
        battle.side_end("p1", condition)

    with pytest.raises(Exception):
        battle.side_end("p2", condition)


def test_battle_field_interactions():
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    assert not battle.fields

    battle.parse_message(["", "-fieldstart", "Electric terrain"])
    assert battle.fields == {Field.ELECTRIC_TERRAIN: 0}

    battle.parse_message(["", "-fieldstart", "Trick room"])
    assert battle.fields == {Field.ELECTRIC_TERRAIN: 0, Field.TRICK_ROOM: 0}

    battle.parse_message(["", "-fieldend", "Trick room"])
    assert battle.fields == {Field.ELECTRIC_TERRAIN: 0}

    battle.parse_message(["", "-fieldend", "Electric terrain"])
    assert not battle.fields

    with pytest.raises(Exception):
        battle.parse_message(["", "-fieldend", "Electric terrain"])


def test_battle_weather_interactions():
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    assert battle.weather == {}

    battle.parse_message(["", "-weather", "desolateland"])
    assert battle.weather == {Weather.DESOLATELAND: 0}

    battle.parse_message(["", "-weather", "hail"])
    assert battle.weather == {Weather.HAIL: 0}

    battle.parse_message(["", "-weather", "none"])
    assert battle.weather == {}


def test_battle_player_role_interaction():
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.parse_message(["", "player", "p4", "username", "", ""])
    assert battle.player_role == "p4"


def test_stackable_side_start():
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.parse_message(["", "player", "p1", "username", "", ""])
    battle.parse_message(["", "-sidestart", "p1: username", "move: Stealth Rock"])

    assert battle.side_conditions == {SideCondition.STEALTH_ROCK: 0}

    battle.parse_message(["", "-sidestart", "p1: username", "move: spikes"])

    assert battle.side_conditions == {
        SideCondition.STEALTH_ROCK: 0,
        SideCondition.SPIKES: 1,
    }
    battle.parse_message(["", "-sidestart", "p1: username", "move: spikes"])
    assert battle.side_conditions == {
        SideCondition.STEALTH_ROCK: 0,
        SideCondition.SPIKES: 2,
    }


def test_battle_tag():
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    assert battle.battle_tag == "tag"


def test_battle_request_parsing(example_request):
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.parse_request(example_request)
    assert battle.force_switch is False

    mon = battle.active_pokemon

    assert mon.species == "venusaur"
    assert mon.current_hp_fraction == 139 / 265
    assert mon.stats == {
        "hp": 265,
        "atk": 139,
        "def": 183,
        "spa": 211,
        "spd": 211,
        "spe": 178,
    }

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


def test_battle_request_parsing_with_force_switch(force_switch_example_request):
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.parse_request(force_switch_example_request)

    assert battle.force_switch is True


def test_battle_request_and_interactions(example_request):
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.parse_request(example_request)
    mon = battle.active_pokemon

    battle.parse_message(["", "-boost", "p2: Venusaur", "atk", "4"])
    assert mon.boosts["atk"] == 4

    battle.parse_message(["", "-clearallboost"])
    assert mon.boosts["atk"] == 0

    battle.parse_message(["", "-boost", "p2: Venusaur", "atk", "4"])
    assert mon.boosts["atk"] == 4

    battle.parse_message(["", "-clearboost", "p2: Venusaur"])
    assert mon.boosts["atk"] == 0

    battle.parse_message(["", "-boost", "p2: Venusaur", "atk", "4"])
    assert mon.boosts["atk"] == 4

    battle.parse_message(["", "-clearpositiveboost", "p2: Venusaur"])
    assert mon.boosts["atk"] == 0

    battle.parse_message(["", "-boost", "p2: Venusaur", "atk", "4"])
    assert mon.boosts["atk"] == 4

    battle.parse_message(["", "-clearpositiveboost", "p2: Venusaur"])
    assert mon.boosts["atk"] == 0

    battle.parse_message(["", "-boost", "p2: Venusaur", "atk", "4"])
    assert mon.boosts["atk"] == 4

    battle.parse_message(["", "-clearnegativeboost", "p2: Venusaur"])
    assert mon.boosts["atk"] == 4

    battle.parse_message(["", "switch", "p2: Necrozma", "Necrozma, L82", "121/293 tox"])
    assert mon.boosts["atk"] == 0
    assert mon.level == 82

    assert battle.active_pokemon.species == "necrozma"
    assert battle.active_pokemon.status == Status.TOX

    battle.parse_message(["", "-curestatus", "p2: Necrozma", "par"])
    assert battle.active_pokemon.status == Status.TOX

    battle.parse_message(["", "-curestatus", "p2: Necrozma", "tox"])
    assert not battle.active_pokemon.status

    battle.parse_message(["", "switch", "p1: Gabite", "Gabite, L99, F", "311/311"])
    assert battle.opponent_active_pokemon.species == "gabite"
    assert battle.opponent_active_pokemon.level == 99
    assert battle.parse_message(["", "-supereffective"]) is None

    battle.parse_message(["", "-activate", "p2: Necrozma", "leech seed"])
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

    battle.parse_message(["", "switch", "p1: Tyranitar", "Tyranitar, L82", "100/100"])
    battle.active_pokemon._boosts = some_boosts
    battle.parse_message(["", "-copyboost", "p2: Necrozma", "p1: Tyranitar"])
    assert battle.opponent_active_pokemon.boosts == some_boosts

    assert battle.active_pokemon.current_hp == 121
    battle.parse_message(["", "-damage", "p2: Necrozma", "10/293"])
    assert battle.active_pokemon.current_hp == 10
    battle.parse_message(["", "-damage", "p2: Necrozma", "10/293g"])
    assert battle.active_pokemon.current_hp == 10

    battle.active_pokemon.temporary_ability = "temporaryability"
    assert battle.active_pokemon.ability == "temporaryability"
    battle.parse_message(["", "-endability", "p2: Necrozma"])
    assert battle.active_pokemon.ability == "prismarmor"

    battle.active_pokemon.item = "focussash"
    battle.parse_message(["", "-enditem", "p2: Necrozma", "focussash"])
    assert battle.active_pokemon.item is None

    assert battle.opponent_active_pokemon.base_stats["atk"] == 134
    battle.parse_message(["", "detailschange", "p1: Tyranitar", "Tyranitar-Mega, L82"])
    assert battle.opponent_active_pokemon.base_stats["atk"] == 164

    battle.parse_message(["", "-heal", "p2: Necrozma", "293/293"])
    assert battle.active_pokemon.current_hp == 293

    boosts_before_invertion = battle.opponent_active_pokemon.boosts.copy()
    battle.parse_message(["", "-invertboost", "p1: Tyranitar"])
    for stat, boost in battle.opponent_active_pokemon.boosts.items():
        assert boost == -boosts_before_invertion[stat]

    battle.parse_message(["", "-singleturn", "p1: Tyranitar", "move: Rage Powder"])
    assert Effect.RAGE_POWDER in battle.opponent_active_pokemon.effects
    battle.end_turn(1)
    assert Effect.RAGE_POWDER not in battle.opponent_active_pokemon.effects

    battle.parse_message(
        ["", "-singlemove", "p1: Tyranitar", "Glaive Rush", "[silent]"]
    )
    assert Effect.GLAIVE_RUSH in battle.opponent_active_pokemon.effects

    battle.parse_message(
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

    battle.parse_message(["", "switch", "p1: Latias", "Latias, L82", "100/100"])
    assert battle.opponent_active_pokemon.base_stats["def"] == 90
    battle.parse_message(["", "-mega", "p1: Latias", "latiasite"])
    assert battle.opponent_active_pokemon.species == "latias"
    assert battle.opponent_active_pokemon.base_stats["def"] == 120

    battle.parse_message(["", "-mustrecharge", "p1: Latias"])
    assert battle.opponent_active_pokemon.must_recharge is True

    battle.parse_message(["", "-prepare", "p1: Latias", "Solar Beam", "p2: Necrozma"])
    assert (
        battle.opponent_active_pokemon.preparing_move
        == battle.opponent_active_pokemon.moves["solarbeam"]
    )
    assert battle.opponent_active_pokemon.preparing_target.species == "necrozma"

    assert (
        battle.opponent_active_pokemon.preparing_move
        == battle.opponent_active_pokemon.moves["solarbeam"]
    )
    assert battle.opponent_active_pokemon.preparing_target.species == "necrozma"

    battle.parse_message(["", "switch", "p1: Groudon", "Groudon, L82", "100/100"])
    battle.parse_message(["", "-primal", "p1: Groudon"])
    assert battle.opponent_active_pokemon.species == "groudon"

    battle.parse_message(["", "-setboost", "p1: Groudon", "atk", "6"])
    assert battle.opponent_active_pokemon.boosts["atk"] == 6

    assert battle.opponent_active_pokemon.current_hp == 100
    battle.parse_message(["", "-sethp", "p1: Groudon", "99/100"])
    assert battle.opponent_active_pokemon.current_hp == 99

    battle.parse_message(["", "-status", "p1: Groudon", "tox"])
    assert battle.opponent_active_pokemon.status == Status.TOX

    battle.active_pokemon.boosts["atk"] = 0
    battle.active_pokemon.boosts["def"] = 3
    battle.active_pokemon.boosts["spe"] = -1
    battle.opponent_active_pokemon.boosts["atk"] = 6
    battle.opponent_active_pokemon.boosts["def"] = -2
    battle.opponent_active_pokemon.boosts["spe"] = 0
    battle.parse_message(["", "-swapboost", "p1: Groudon", "p2: Necrozma", "atk, def"])
    assert battle.active_pokemon.boosts["atk"] == 6
    assert battle.active_pokemon.boosts["def"] == -2
    assert battle.active_pokemon.boosts["spe"] == -1
    assert battle.opponent_active_pokemon.boosts["atk"] == 0
    assert battle.opponent_active_pokemon.boosts["def"] == 3
    assert battle.opponent_active_pokemon.boosts["spe"] == 0

    battle.parse_message(["", "-transform", "p1: Groudon", "p2: Necrozma"])
    assert battle.opponent_active_pokemon.species == "groudon"
    assert (
        battle.opponent_active_pokemon.base_stats
        == GenData.from_gen(8).pokedex["necrozma"]["baseStats"]
    )
    assert battle.opponent_active_pokemon.boosts == battle.active_pokemon.boosts

    battle.parse_message(["", "switch", "p1: Sunflora", "Sunflora, L82", "100/100"])
    battle.opponent_active_pokemon._boosts = cleared_boosts.copy()
    battle.opponent_active_pokemon._boosts["atk"] = 4
    battle.parse_message(["", "-unboost", "p1: Sunflora", "atk", "5"])
    assert battle.opponent_active_pokemon._boosts["atk"] == -1

    battle.opponent_active_pokemon.item = "grassiumz"
    battle.parse_message(["", "-zpower", "p1: Sunflora"])

    sunflora = battle.opponent_active_pokemon
    assert sunflora.fainted is False
    battle.parse_message(["", "faint", "p1: Sunflora"])
    assert sunflora.fainted is True

    battle.parse_message(["", "switch", "p1: Groudon", "Groudon, L82", "100/100"])
    battle.parse_message(
        ["", "move", "p1: Groudon", "Precipice Blades", "p2: Necrozma"]
    )
    assert "precipiceblades" in battle.opponent_active_pokemon.moves

    event = ["", "move", "p1: Groudon", "Teeter Dance", "[from]ability: Dancer"]
    battle.parse_message(event)
    assert "teeterdance" not in battle.opponent_active_pokemon.moves
    assert event == ["", "move", "p1: Groudon", "Teeter Dance", "[from]ability: Dancer"]

    battle._player_username = "ray"
    battle._opponent_username = "wolfe"
    battle.parse_message(
        [
            "",
            "raw",
            "ray's rating: 1049 &rarr; <strong>1079</strong><br />(+30 for winning)",
        ]
    )
    assert battle.rating == 1049
    battle.parse_message(
        [
            "",
            "raw",
            "wolfe's rating: 1025 &rarr; <strong>1012</strong><br />(-13 for losing)",
        ]
    )
    assert battle.opponent_rating == 1025

    battle.in_team_preview = True
    battle.parse_message(["", "start"])
    assert battle.in_team_preview is False

    with pytest.raises(NotImplementedError) as excinfo:
        msg_type = "bad message type that should raise an exception"
        battle.parse_message(["", msg_type])
    assert msg_type in str(excinfo.value)

    assert not battle.maybe_trapped
    assert not battle.opponent_used_dynamax

    assert battle.grounded
    assert battle.is_grounded(battle.opponent_active_pokemon)

    # Items
    battle.parse_message(
        [
            "",
            "-damage",
            "p2a: Necrozma",
            "167/319",
            "[from] item: Rocky Helmet",
            "[of] p1a: Groudon",
        ]
    )
    assert battle.opponent_active_pokemon.item == "rockyhelmet"
    battle.opponent_active_pokemon._item = None

    battle.parse_message(
        [
            "",
            "-damage",
            "p1a: Groudon",
            "100/265",
            "[from] item: Rocky Helmet",
            "[of] p2a: Necrozma",
        ]
    )
    assert battle.active_pokemon.item == "rockyhelmet"
    battle.active_pokemon._item = None

    battle.parse_message(
        ["", "-damage", "p2a: Necrozma", "100/265", "[from] item: Life Orb"]
    )
    assert battle.active_pokemon.item == "lifeorb"
    battle.active_pokemon._item = None

    battle.parse_message(
        ["", "-damage", "p1a: Groudon", "100/265", "[from] item: Life Orb"]
    )
    assert battle.opponent_active_pokemon.item == "lifeorb"
    battle.opponent_active_pokemon._item = None

    # Abilities
    battle.parse_message(
        [
            "",
            "-damage",
            "p2a: Necrozma",
            "167/319",
            "[from] ability: Iron Barbs",
            "[of] p1a: Groudon",
        ]
    )
    assert battle.opponent_active_pokemon.ability == "ironbarbs"
    battle.opponent_active_pokemon.temporary_ability = None

    battle.parse_message(
        [
            "",
            "-damage",
            "p2a: Necrozma",
            "100/265",
            "[from] ability: Iron Barbs",
            "[of] p1a: Groudon",
        ]
    )
    assert battle.opponent_active_pokemon.ability == "ironbarbs"
    battle.opponent_active_pokemon.temporary_ability = None

    battle.parse_message(
        [
            "",
            "-heal",
            "p1a: Groudon",
            "200/265",
            "[from] ability: Water Absorb",
            "[of] p2a: Necrozma",
        ]
    )
    assert battle.opponent_active_pokemon.ability == "waterabsorb"
    necrozma = battle.active_pokemon
    groudon = battle.opponent_active_pokemon

    necrozma.switch_out(battle.fields)
    groudon.switch_in()
    groudon.temporary_ability = None

    battle.parse_message(
        [
            "",
            "-heal",
            "p2a: Necrozma",
            "200/265",
            "[from] ability: Water Absorb",
            "[of] p1a: Groudon",
        ]
    )
    assert necrozma.ability == "waterabsorb"

    necrozma.item = GenData.UNKNOWN_ITEM
    battle.parse_message(
        ["", "-heal", "p2a: Necrozma", "200/265", "[from] item: Leftovers"]
    )
    assert necrozma.item == "leftovers"
    necrozma.item = None

    groudon.item = GenData.UNKNOWN_ITEM
    battle.parse_message(
        ["", "-heal", "p1a: Groudon", "200/265", "[from] item: Leftovers"]
    )
    assert groudon.item == "leftovers"
    groudon.item = None

    groudon.item = None
    battle.parse_message(
        ["", "-heal", "p1a: Groudon", "200/265", "[from] item: Sitrus Berry"]
    )
    assert groudon.item is None

    # Test temporary types and abilities

    necrozma._ability = "prismarmor"
    groudon._ability = "desolateland"
    battle.parse_message(["", "move", "p2a: Necrozma", "Worry Seed", "p1a: Groudon"])
    assert groudon.ability == "desolateland"
    battle.parse_message(
        ["", "-endability", "p1a: Groudon", "Desolate Land", "[from] move: Worry Seed"]
    )
    battle.parse_message(
        ["", "-ability", "p1a: Groudon", "Insomnia", "[from] move: Worry Seed"]
    )
    assert groudon.ability == "insomnia"
    groudon.switch_out(battle.fields)
    groudon.switch_in()
    assert groudon.ability == "desolateland"

    battle.parse_message(["", "move", "p1a: Groudon", "Skill Swap", "p2a: Necrozma"])
    battle.parse_message(
        [
            "",
            "-activate",
            "p1a: Groudon",
            "move: Skill Swap",
            "Prism Armor",
            "Desolate Land",
            "[of] p2a: Necrozma",
        ]
    )
    assert groudon.ability == "prismarmor"
    assert necrozma.ability == "desolateland"
    groudon.switch_in()
    groudon.switch_out(battle.fields)
    assert groudon.ability == "desolateland"

    battle.parse_message(["", "switch", "p1a: Ho-oh", "Ho-oh, L82", "100/100"])
    hooh = battle.opponent_active_pokemon
    assert hooh.type_1 == PokemonType.FIRE
    assert hooh.type_2 == PokemonType.FLYING
    assert hooh.types == [PokemonType.FIRE, PokemonType.FLYING]

    battle.parse_message(["", "move", "p1a: Ho-oh", "Burn Up", "p2a: Necrozma"])
    battle.parse_message(
        ["", "-start", "p1a: Ho-oh", "typechange", "???/Flying", "[from] move: Burn Up"]
    )

    assert hooh.type_1 == PokemonType.THREE_QUESTION_MARKS
    assert hooh.type_2 == PokemonType.FLYING
    assert hooh.types == [PokemonType.THREE_QUESTION_MARKS, PokemonType.FLYING]
    hooh.switch_out(battle.fields)
    hooh.switch_in()
    assert hooh.type_1 == PokemonType.FIRE
    assert hooh.type_2 == PokemonType.FLYING
    assert hooh.types == [PokemonType.FIRE, PokemonType.FLYING]

    battle.parse_message(["", "move", "p2a: Necrozma", "Soak", "p1a: Ho-oh"])
    battle.parse_message(["", "-start", "p1a: Ho-oh", "typechange", "Water"])
    assert hooh.type_1 == PokemonType.WATER
    assert hooh.type_2 is None
    assert hooh.types == [PokemonType.WATER]
    hooh.switch_out(battle.fields)
    hooh.switch_in()
    assert hooh.type_1 == PokemonType.FIRE
    assert hooh.type_2 == PokemonType.FLYING
    assert hooh.types == [PokemonType.FIRE, PokemonType.FLYING]

    battle.logger = None
    pickle.loads(pickle.dumps(battle))


def test_end_illusion():
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)
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

    battle.player_role = "p2"
    battle.switch("p2: Celebi", "Celebi", "100/100")
    battle.switch("p1: Kingdra", "Kingdra, F", "100/100")
    battle.active_pokemon._boosts = non_empty_boosts

    assert battle.active_pokemon.species == "celebi"

    battle.parse_message(["", "replace", "p2: Zoroark", "Zoroark, M"])

    assert battle.active_pokemon.species == "zoroark"
    assert battle.opponent_active_pokemon.species == "kingdra"
    assert battle.get_pokemon("p2: Zoroark").boosts == non_empty_boosts
    assert battle.get_pokemon("p2: Celebi").boosts == empty_boosts


def test_toxic_counter(example_request):
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.parse_request(example_request)
    battle.parse_message(["", "-status", "p2a: Venusaur", "tox"])
    assert battle.active_pokemon.status == Status.TOX
    assert battle.active_pokemon.status_counter == 0

    battle.end_turn(2)
    assert battle.active_pokemon.status == Status.TOX
    assert battle.active_pokemon.status_counter == 1

    battle.end_turn(3)
    assert battle.active_pokemon.status == Status.TOX
    assert battle.active_pokemon.status_counter == 2

    battle.switch("p2a: Unfezant", "Unfezant, L86, M", "100/100")
    assert battle.active_pokemon.status is None
    assert battle.active_pokemon.status_counter == 0

    battle.end_turn(4)
    assert battle.active_pokemon.status is None
    assert battle.active_pokemon.status_counter == 0

    battle.switch("p2a: Venusaur", "Venusaur, L82, M", "100/100 tox")
    assert battle.active_pokemon.status == Status.TOX
    assert battle.active_pokemon.status_counter == 0

    battle.end_turn(5)
    assert battle.active_pokemon.status == Status.TOX
    assert battle.active_pokemon.status_counter == 1

    battle.end_turn(6)
    assert battle.active_pokemon.status == Status.TOX
    assert battle.active_pokemon.status_counter == 2


def test_sleep_counter(example_request):
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.parse_request(example_request)
    battle.parse_message(["", "-status", "p2a: Venusaur", "slp"])
    assert battle.active_pokemon.status == Status.SLP
    assert battle.active_pokemon.status_counter == 0

    battle.end_turn(2)
    battle.parse_message(["", "cant", "p2a: Venusaur", ""])
    assert battle.active_pokemon.status == Status.SLP
    assert battle.active_pokemon.status_counter == 1

    battle.end_turn(3)
    assert battle.active_pokemon.status == Status.SLP
    assert battle.active_pokemon.status_counter == 1

    battle.switch("p2a: Unfezant", "Unfezant, L86, M", "100/100")
    assert battle.active_pokemon.status is None
    assert battle.active_pokemon.status_counter == 0

    battle.end_turn(4)
    assert battle.active_pokemon.status is None
    assert battle.active_pokemon.status_counter == 0

    battle.switch("p2a: Venusaur", "Venusaur, L82, M", "100/100 slp")
    assert battle.active_pokemon.status == Status.SLP
    assert battle.active_pokemon.status_counter == 1

    battle.end_turn(5)
    battle.parse_message(["", "cant", "p2a: Venusaur", ""])
    assert battle.active_pokemon.status == Status.SLP
    assert battle.active_pokemon.status_counter == 2

    battle.end_turn(6)
    battle.parse_message(["", "cant", "p2a: Venusaur", ""])
    assert battle.active_pokemon.status == Status.SLP
    assert battle.active_pokemon.status_counter == 3


def test_rules_are_tracked():
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.parse_message(["", "rule", "hello"])
    battle.parse_message(["", "rule", "hi"])
    battle.parse_message(["", "rule", "this is a rule!"])

    assert battle.rules == ["hello", "hi", "this is a rule!"]


def test_field_terrain_interactions():
    logger = MagicMock()
    battle = Battle("tag", "username", logger, gen=8)

    battle.field_start("electricterrain")
    assert battle.fields == {Field.ELECTRIC_TERRAIN: 0}
    battle.turn = battle.turn + 1

    battle.field_start("mistyterrain")
    assert battle.fields == {Field.MISTY_TERRAIN: 1}
    battle.turn = battle.turn + 1

    battle.field_start("gravity")
    assert battle.fields == {Field.MISTY_TERRAIN: 1, Field.GRAVITY: 2}
    battle.turn = battle.turn + 1

    battle.field_start("psychicterrain")
    assert battle.fields == {Field.GRAVITY: 2, Field.PSYCHIC_TERRAIN: 3}


def test_teampreview_opponent_team():
    teampreview_message = """|player|p2|SimpleHeuristics 1|102|
|teamsize|p1|6
|teamsize|p2|6
|gen|9
|tier|[Gen 9] VGC 2024 Reg G
|rule|Species Clause: Limit one of each Pokémon
|rule|Item Clause: Limit one of each item
|clearpoke
|poke|p1|Tornadus, L50, M|
|poke|p1|Kyogre, L50|
|poke|p1|Incineroar, L50, M|
|poke|p1|Archaludon, L50, M|
|poke|p1|Amoonguss, L50, F|
|poke|p1|Urshifu-*, L50, M|
|poke|p2|Tornadus, L50, M|
|poke|p2|Kyogre, L50|
|poke|p2|Incineroar, L50, M|
|poke|p2|Archaludon, L50, M|
|poke|p2|Amoonguss, L50, M|
|poke|p2|Urshifu-*, L50, F|
|teampreview|4"""
    battle = Battle("tag", "username", MagicMock(), gen=9)

    for line in teampreview_message.split("\n"):
        battle.parse_message(line.split("|"))

    assert {mon.species for mon in battle.teampreview_opponent_team} == {
        "tornadus",
        "kyogre",
        "incineroar",
        "archaludon",
        "amoonguss",
        "urshifu",
    }
