# -*- coding: utf-8 -*-
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.player.baselines import MaxBasePowerPlayer
from poke_env.player.baselines import SimpleHeuristicsPlayer
from collections import namedtuple


def test_max_base_power_player():
    from poke_env.player import player as player_pkg
    from poke_env.environment.battle import Battle

    player = MaxBasePowerPlayer(start_listening=False)

    PseudoBattle = namedtuple(
        "PseudoBattle",
        (
            "available_moves",
            "available_switches",
            "can_z_move",
            "can_dynamax",
            "can_mega_evolve",
        ),
    )
    battle = PseudoBattle([], [], False, False, False)

    player_pkg.Battle = PseudoBattle

    assert player.choose_move(battle).message == "/choose default"

    battle.available_switches.append(Pokemon(species="ponyta"))
    assert player.choose_move(battle).message == "/choose switch ponyta"

    battle.available_moves.append(Move("protect"))
    assert player.choose_move(battle).message == "/choose move protect"

    battle.available_moves.append(Move("quickattack"))
    assert player.choose_move(battle).message == "/choose move quickattack"

    battle.available_moves.append(Move("flamethrower"))
    assert player.choose_move(battle).message == "/choose move flamethrower"

    player_pkg.Battle = (
        Battle  # this is in case a test runner shares memory between tests
    )


def test_simple_heuristics_player_estimate_matchup():
    player = SimpleHeuristicsPlayer(start_listening=False)

    dragapult = Pokemon(species="dragapult")
    assert player._estimate_matchup(dragapult, dragapult) == 0

    gengar = Pokemon(species="gengar")
    assert player._estimate_matchup(dragapult, gengar) == -player._estimate_matchup(
        gengar, dragapult
    )
    assert player._estimate_matchup(dragapult, gengar) == player.SPEED_TIER_COEFICIENT

    mamoswine = Pokemon(species="mamoswine")
    assert (
        player._estimate_matchup(dragapult, mamoswine)
        == -1 + player.SPEED_TIER_COEFICIENT
    )

    dragapult._set_hp("100/100")
    mamoswine._set_hp("50/100")
    assert (
        player._estimate_matchup(dragapult, mamoswine)
        == -1 + player.SPEED_TIER_COEFICIENT + player.HP_FRACTION_COEFICIENT / 2
    )


def test_simple_heuristics_player_should_dynamax():
    PseudoBattle = namedtuple(
        "PseudoBattle",
        ["active_pokemon", "opponent_active_pokemon", "team", "can_dynamax"],
    )
    player = SimpleHeuristicsPlayer(start_listening=False)

    battle = PseudoBattle(
        Pokemon(species="charmander"), Pokemon(species="charmander"), {}, False
    )
    assert player._should_dynamax(battle, 4) is False

    battle = PseudoBattle(
        Pokemon(species="charmander"), Pokemon(species="charmander"), {}, True
    )
    assert player._should_dynamax(battle, 1) is True

    battle.active_pokemon._set_hp("100/100")
    battle.team["charmander"] = battle.active_pokemon
    assert player._should_dynamax(battle, 4) is True

    battle = PseudoBattle(
        Pokemon(species="squirtle"),
        Pokemon(species="charmander"),
        {
            "kakuna": Pokemon(species="kakuna"),
            "venusaur": Pokemon(species="venusaur"),
            "charmander": Pokemon(species="charmander"),
        },
        True,
    )
    for mon in battle.team.values():
        mon._set_hp("100/100")
    battle.active_pokemon._set_hp("100/100")
    battle.opponent_active_pokemon._set_hp("100/100")

    assert player._should_dynamax(battle, 4) is True


def test_simple_heuristics_player_should_switch_out():
    PseudoBattle = namedtuple(
        "PseudoBattle",
        ["active_pokemon", "opponent_active_pokemon", "available_switches"],
    )
    player = SimpleHeuristicsPlayer(start_listening=False)

    battle = PseudoBattle(
        Pokemon(species="charmander"), Pokemon(species="charmander"), []
    )
    battle.active_pokemon._last_request["stats"] = {
        stat: 0 for stat in battle.active_pokemon.base_stats
    }
    assert player._should_switch_out(battle) is False

    battle.available_switches.append(Pokemon(species="venusaur"))
    assert player._should_switch_out(battle) is False

    battle.available_switches.append(Pokemon(species="gyarados"))
    assert player._should_switch_out(battle) is False

    battle.active_pokemon._boost("spa", -3)
    battle.active_pokemon._last_request["stats"].update({"atk": 10, "spa": 20})
    assert player._should_switch_out(battle) is True

    battle.active_pokemon._last_request["stats"].update({"atk": 30, "spa": 20})
    assert player._should_switch_out(battle) is False

    battle.active_pokemon._boost("atk", -3)
    assert player._should_switch_out(battle) is True

    battle = PseudoBattle(
        Pokemon(species="gible"),
        Pokemon(species="mamoswine"),
        [Pokemon(species="charizard")],
    )
    assert player._should_switch_out(battle) is True


def test_simple_heuristics_player_stat_estimation():
    player = SimpleHeuristicsPlayer(start_listening=False)
    mon = Pokemon(species="charizard")

    assert player._stat_estimation(mon, "spe") == 236

    mon._boost("spe", 2)
    assert player._stat_estimation(mon, "spe") == 472

    mon._boost("atk", -1)
    assert player._stat_estimation(mon, "atk") == 136


def test_simple_heuristics_player():
    player = SimpleHeuristicsPlayer(start_listening=False)

    PseudoBattle = namedtuple(
        "PseudoBattle",
        (
            "active_pokemon",
            "opponent_active_pokemon",
            "available_moves",
            "available_switches",
            "team",
            "can_dynamax",
            "side_conditions",
            "opponent_side_conditions",
        ),
    )
    battle = PseudoBattle(
        Pokemon(species="dragapult"),
        Pokemon(species="gengar"),
        [],
        [Pokemon(species="togekiss")],
        {},
        True,
        set(),
        set(),
    )
    battle.active_pokemon._last_request["stats"] = {
        stat: 100 for stat in battle.active_pokemon.base_stats
    }

    battle.available_switches[0]._set_hp("100/100")
    assert player.choose_move(battle).message == "/choose switch togekiss"

    battle.available_moves.append(Move("quickattack"))
    assert player.choose_move(battle).message == "/choose move quickattack"

    battle.available_moves.append(Move("flamethrower"))
    assert player.choose_move(battle).message == "/choose move flamethrower"

    battle.available_moves.append(Move("dracometeor"))
    assert player.choose_move(battle).message == "/choose move dracometeor"

    battle.active_pokemon._boost("atk", -3)
    battle.active_pokemon._boost("spa", -3)
    battle.available_switches.append(Pokemon(species="sneasel"))
    battle.available_switches[1]._set_hp("100/100")
    assert player.choose_move(battle).message == "/choose switch sneasel"
