from unittest.mock import MagicMock

import pytest

from poke_env.battle import DoubleBattle, Effect, Field, Move, Pokemon, PokemonType


def test_battle_request_parsing(example_doubles_request):
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger, gen=8)

    battle.parse_request(example_doubles_request)
    assert len(battle.team) == 6

    pokemon_names = set(map(lambda pokemon: pokemon.species, battle.team.values()))
    assert "thundurus" in pokemon_names
    assert "raichualola" in pokemon_names
    assert "maractus" in pokemon_names
    assert "zamazentacrowned" in pokemon_names

    zamazenta = battle.get_pokemon("p1: Zamazenta")
    zamazenta_moves = zamazenta.moves
    assert (
        len(zamazenta_moves) == 4
        and "closecombat" in zamazenta_moves
        and "crunch" in zamazenta_moves
        and "psychicfangs" in zamazenta_moves
        and "behemothbash" in zamazenta_moves
    )


def test_battle_request_parsing_and_interactions(example_doubles_request):
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger, gen=8)

    battle.parse_request(example_doubles_request)
    mr_rime, klinklang = battle.active_pokemon
    (
        my_first_active,
        my_second_active,
        their_first_active,
        their_second_active,
    ) = battle.all_active_pokemons
    assert my_first_active == mr_rime and my_second_active == klinklang
    assert their_first_active is None and their_second_active is None
    assert isinstance(mr_rime, Pokemon)
    assert isinstance(klinklang, Pokemon)
    assert battle.get_pokemon("p1: Nickname") == mr_rime
    assert battle.get_pokemon("p1: Klinklang") == klinklang

    assert set(battle.available_moves[0]) == set(
        battle.active_pokemon[0].moves.values()
    )
    assert set(battle.available_moves[1]) == set(
        battle.active_pokemon[1].moves.values()
    )

    assert len(battle.available_switches) == 2
    assert all(battle.can_dynamax)
    assert not any(battle.can_z_move)
    assert not any(battle.can_mega_evolve)
    assert not any(battle.trapped)
    assert not any(battle.force_switch)
    assert not any(battle.maybe_trapped)

    mr_rime.boosts = {
        "accuracy": -2,
        "atk": 1,
        "def": -6,
        "evasion": 4,
        "spa": -4,
        "spd": 2,
        "spe": 3,
    }
    klinklang.boosts = {
        "accuracy": -6,
        "atk": 6,
        "def": -1,
        "evasion": 1,
        "spa": 4,
        "spd": -3,
        "spe": 2,
    }

    battle.clear_all_boosts()

    cleared_boosts = {
        "accuracy": 0,
        "atk": 0,
        "def": 0,
        "evasion": 0,
        "spa": 0,
        "spd": 0,
        "spe": 0,
    }

    assert mr_rime.boosts == cleared_boosts
    assert klinklang.boosts == cleared_boosts

    assert battle.active_pokemon == [mr_rime, klinklang]
    battle.parse_message(["", "swap", "p1b: Klinklang", ""])
    assert battle.active_pokemon == [klinklang, mr_rime]

    battle.switch("p2a: Milotic", "Milotic, L50, F", "48/48")
    battle.switch("p2b: Tyranitar", "Tyranitar, L50, M", "48/48")

    milotic, tyranitar = battle.opponent_active_pokemon
    assert milotic.species == "milotic"
    assert tyranitar.species == "tyranitar"

    assert not battle.opponent_used_dynamax

    assert battle.current_observation
    assert battle.current_observation.events[0] == ["", "swap", "p1b: Klinklang", ""]


def test_check_heal_message_for_ability():
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger, gen=8)
    battle.player_role = "p1"

    # Add two active opponent pokemon
    battle.parse_message(["", "switch", "p2a: Furret", "Furret, L50, F", "100/100"])
    battle.parse_message(["", "switch", "p2b: Sentret", "Sentret, L50, F", "100/100"])

    battle.parse_message(
        [
            "",
            "-heal",
            "p2a: Furret",
            "100/100",
            "[from] ability: Water Absorb",
            "[of] p2b: Sentret",
        ]
    )
    assert battle.opponent_team["p2: Furret"].ability == "waterabsorb"

    battle.parse_message(
        [
            "",
            "-heal",
            "p2b: Furret",
            "100/100",
            "[from] ability: Hospitality",
            "[of] p2a: Sentret",
        ]
    )
    assert battle.opponent_team["p2: Sentret"].ability == "hospitality"


def test_get_possible_showdown_targets(example_doubles_request):
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger, gen=8)

    battle.parse_request(example_doubles_request)
    mr_rime, klinklang = battle.active_pokemon
    psychic = mr_rime.moves["psychic"]
    slackoff = mr_rime.moves["slackoff"]

    battle.switch("p2b: Tyranitar", "Tyranitar, L50, M", "48/48")
    assert battle.get_possible_showdown_targets(psychic, mr_rime) == [-2, 2]

    battle.switch("p2a: Milotic", "Milotic, L50, F", "48/48")
    assert battle.get_possible_showdown_targets(psychic, mr_rime) == [-2, 1, 2]
    assert battle.get_possible_showdown_targets(slackoff, mr_rime) == [0]
    assert battle.get_possible_showdown_targets(psychic, mr_rime, dynamax=True) == [
        1,
        2,
    ]
    assert battle.get_possible_showdown_targets(slackoff, mr_rime, dynamax=True) == [0]

    # Override last request with terastarstorm for Mr. Rime
    terastarstorm = Move("terastarstorm", gen=9)
    battle._available_moves = [[terastarstorm], []]
    assert battle.get_possible_showdown_targets(terastarstorm, mr_rime) == [-2, 1, 2]
    mr_rime.terastallize("stellar")
    assert battle.get_possible_showdown_targets(terastarstorm, mr_rime) == [0]


def test_to_showdown_target(example_doubles_request):
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger, gen=8)

    battle.parse_request(example_doubles_request)
    mr_rime, klinklang = battle.active_pokemon
    opp1, opp2 = battle.opponent_active_pokemon
    psychic = mr_rime.moves["psychic"]
    slackoff = mr_rime.moves["slackoff"]
    dynamax_psychic = psychic.dynamaxed

    assert battle.to_showdown_target(psychic, klinklang) == -2
    assert battle.to_showdown_target(psychic, opp1) == 0
    assert battle.to_showdown_target(slackoff, mr_rime) == 0
    assert battle.to_showdown_target(slackoff, None) == 0
    assert battle.to_showdown_target(dynamax_psychic, klinklang) == -2


def test_end_illusion():
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger, gen=8)
    battle.player_role = "p2"

    battle.switch("p2a: Celebi", "Celebi", "100/100")
    battle.switch("p2b: Ferrothorn", "Ferrothorn, M", "100/100")
    battle.switch("p1a: Pelipper", "Pelipper, F", "100/100")
    battle.switch("p1b: Kingdra", "Kingdra, F", "100/100")

    battle.end_illusion("p2a: Zoroark", "Zoroark, M")
    zoroark = battle.team["p2: Zoroark"]
    celebi = battle.team["p2: Celebi"]
    ferrothorn = battle.team["p2: Ferrothorn"]
    assert zoroark in battle.active_pokemon
    assert ferrothorn in battle.active_pokemon
    assert celebi not in battle.active_pokemon


def test_one_mon_left_in_double_battles_results_in_available_move_in_the_correct_slot():
    request = {
        "active": [
            {
                "moves": [
                    {
                        "move": "Ally Switch",
                        "id": "allyswitch",
                        "pp": 18,
                        "maxpp": 24,
                        "target": "self",
                        "disabled": False,
                    }
                ]
            },
            {
                "moves": [
                    {
                        "move": "Recover",
                        "id": "recover",
                        "pp": 4,
                        "maxpp": 8,
                        "target": "self",
                        "disabled": False,
                    },
                    {
                        "move": "Haze",
                        "id": "haze",
                        "pp": 46,
                        "maxpp": 48,
                        "target": "all",
                        "disabled": False,
                    },
                ]
            },
        ],
        "side": {
            "name": "DisplayPlayer 1",
            "id": "p1",
            "pokemon": [
                {
                    "ident": "p1: Cresselia",
                    "details": "Cresselia, F",
                    "condition": "0 fnt",
                    "active": True,
                    "stats": {
                        "atk": 145,
                        "def": 350,
                        "spa": 167,
                        "spd": 277,
                        "spe": 206,
                    },
                    "moves": ["allyswitch"],
                    "baseAbility": "levitate",
                    "item": "rockyhelmet",
                    "pokeball": "pokeball",
                    "ability": "levitate",
                    "commanding": False,
                    "reviving": False,
                    "teraType": "Psychic",
                    "terastallized": "",
                },
                {
                    "ident": "p1: Milotic",
                    "details": "Milotic, F",
                    "condition": "386/394",
                    "active": True,
                    "stats": {
                        "atk": 112,
                        "def": 194,
                        "spa": 236,
                        "spd": 383,
                        "spe": 199,
                    },
                    "moves": ["recover", "haze"],
                    "baseAbility": "marvelscale",
                    "item": "leftovers",
                    "pokeball": "pokeball",
                    "ability": "marvelscale",
                    "commanding": False,
                    "reviving": False,
                    "teraType": "Water",
                    "terastallized": "Water",
                },
            ],
        },
        "rqid": 16,
    }

    battle = DoubleBattle("tag", "username", MagicMock(), gen=9)
    battle.parse_message(["", "player", "p1", "username", "102", ""])
    battle.parse_message(["", "player", "p2", "username2", "102", ""])

    battle.parse_message(["", "switch", "p1a: Milotic", "Milotic, F", "394/394"])
    battle.parse_message(["", "switch", "p1b: Cresselia", "Cresselia, F", "444/444"])
    battle.parse_message(["", "switch", "p2a: Vaporeon", "Vaporeon, F", "100/100"])
    battle.parse_message(["", "switch", "p2b: Pelipper", "Pelipper, M", "100/100"])
    battle.parse_message(["", "turn", "1"])

    battle.parse_request(request)
    assert battle.last_request == request

    battle.parse_message(
        ["", "swap", "p1b: Cresselia", "0", "[from] move: Ally Switch"]
    )

    assert battle.available_moves[0] == []
    assert [m.id for m in battle.available_moves[1]] == ["recover", "haze"]
    assert battle.active_pokemon[0] is None
    assert battle.active_pokemon[1].species == "milotic"


def test_gen_and_format(example_doubles_logs):
    battle = DoubleBattle("tag", "username", MagicMock(), gen=8)
    battle.player_role = "p1"

    with pytest.raises(RuntimeError):
        for split_message in example_doubles_logs:
            if split_message[1] == "win":
                battle.won_by(split_message[2])
            elif split_message[1] == "tie":
                battle.tied()
            else:
                battle.parse_message(split_message)

    battle = DoubleBattle("tag", "username", MagicMock(), gen=6)
    battle.player_role = "p1"

    for split_message in example_doubles_logs:
        if split_message[1] == "win":
            battle.won_by(split_message[2])
        elif split_message[1] == "tie":
            battle.tied()
        else:
            battle.parse_message(split_message)

    assert battle.gen == 6
    assert battle.battle_tag == "tag"
    assert battle.format == "gen6doublesou"


def test_pledge_moves():
    battle = DoubleBattle("tag", "username", MagicMock(), gen=8)
    battle.player_role = "p2"

    events = [
        ["", "switch", "p1a: Indeedee", "Indeedee-F, L50, F", "100/100"],
        ["", "switch", "p1b: Hatterene", "Hatterene, L50, F", "100/100"],
        ["", "switch", "p2a: Primarina", "Primarina, L50, F, shiny", "169/169"],
        ["", "switch", "p2b: Decidueye", "Decidueye-Hisui, L50, F, shiny", "171/171"],
        ["", ""],
        ["", "move", "p2b: Decidueye", "Grass Pledge", "p1a: Indeedee"],
        ["", "-waiting", "p2b: Decidueye", "p2a: Primarina"],
        [
            "",
            "move",
            "p2a: Primarina",
            "Water Pledge",
            "p1b: Hatterene",
            "[from]move: Grass Pledge",
        ],
        ["", "-combine"],
        ["", "-damage", "p1b: Hatterene", "0 fnt"],
        ["", "-sidestart", "p1: cloverspsyspamsep", "Grass Pledge"],
    ]

    for event in events:
        battle.parse_message(event)

    assert "grasspledge" not in battle.team["p2: Primarina"].moves
    assert "waterpledge" in battle.team["p2: Primarina"].moves


def test_is_grounded():
    battle = DoubleBattle("tag", "username", MagicMock(), gen=9)
    battle.player_role = "p1"
    furret = Pokemon(gen=9, species="furret")
    battle.team = {"p1: Furret": furret}

    battle.parse_message(
        ["", "switch", "p1a: Furret", "Furret, L50, F", "100/100"],
    )
    assert battle.grounded == [True, True]

    furret._type_2 = PokemonType.FLYING
    assert battle.grounded == [False, True]

    furret._type_2 = None
    furret._ability = "levitate"
    assert battle.grounded == [False, True]

    furret._ability = "frisk"
    assert battle.grounded == [True, True]

    furret._effects = {Effect.MAGNET_RISE: 1}
    assert battle.grounded == [False, True]

    furret._effects = {}
    furret.item = "airballoon"
    assert battle.grounded == [False, True]

    battle._fields = {Field.GRAVITY: 1}
    assert battle.grounded == [True, True]

    furret._ability = "levitate"
    assert battle.grounded == [True, True]

    battle._fields = {}
    assert battle.grounded == [False, True]

    furret.item = "ironball"
    assert battle.grounded == [True, True]
    assert battle.is_grounded(furret)


def test_dondozo_tatsugiri():
    battle = DoubleBattle("tag", "username", MagicMock(), gen=9)
    battle.player_role = "p1"
    dozo = Pokemon(gen=9, species="dondozo")
    battle.team = {"p1: Dondozo": dozo}
    tatsu = Pokemon(gen=9, species="tatsugiri")
    tatsu._ability = "commander"
    battle.team["p1: Tatsugiri"] = tatsu

    battle.parse_message(
        ["", "switch", "p1a: Dondozo", "Dondozo, L50, F", "100/100"],
    )
    battle.parse_message(
        ["", "switch", "p1b: Tatsugiri", "Tatsugiri, L50, F", "100/100"],
    )
    battle.parse_message(['', '-activate', 'p1b: Tatsugiri', 'ability: Commander', '[of] p1a: Dondozo'])
    assert Effect.COMMANDER in tatsu.effects

    battle.parse_message(['', 'faint', 'p1a: Dondozo'])
    assert Effect.COMMANDER not in tatsu.effects


def test_symbiosis():
    battle = DoubleBattle("tag", "username", MagicMock(), gen=9)
    battle.player_role = "p1"
    furret = Pokemon(gen=9, species="furret")
    oranguru = Pokemon(gen=9, species="oranguru")
    oranguru._ability = "symbiosis"
    oranguru._item = "choiceband"
    battle.team = {"p1: Furret": furret, "p1: Oranguru": oranguru}

    # https://github.com/smogon/pokemon-showdown/blob/5eee23883897264657c5911d8b37f77472d5eecf/data/mods/gen6/abilities.ts#L99
    battle.parse_message(["", "switch", "p1a: Furret", "Furret, L50, F", "100/100"])
    battle.parse_message(["", "switch", "p1b: Oranguru", "Oranguru, L50, F", "100/100"])
    battle.parse_message(["", "-activate", "p1b: Oranguru", "ability: Symbiosis", "Choice Band", "[of] p1a: Furret"])
    assert furret.item == "choiceband"
    assert oranguru.item is None
