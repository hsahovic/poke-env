from poke_env.environment import Move, Pokemon
from poke_env.player import MaxBasePowerPlayer, RandomPlayer, SimpleHeuristicsPlayer
from collections import namedtuple


def test_max_base_power_player():
    from poke_env.player import player as player_pkg
    from poke_env.environment import Battle

    player = MaxBasePowerPlayer(start_listening=False)

    PseudoBattle = namedtuple(
        "PseudoBattle",
        (
            "available_moves",
            "available_switches",
            "can_z_move",
            "can_dynamax",
            "can_terastallize",
            "can_mega_evolve",
            "gen",
        ),
    )
    battle = PseudoBattle([], [], False, False, False, False, 8)

    player_pkg.Battle = PseudoBattle

    assert player.choose_move(battle).message == "/choose default"

    battle.available_switches.append(Pokemon(species="ponyta", gen=8))
    assert player.choose_move(battle).message == "/choose switch ponyta"

    battle.available_moves.append(Move("protect", gen=8))
    assert player.choose_move(battle).message == "/choose move protect"

    battle.available_moves.append(Move("quickattack", gen=8))
    assert player.choose_move(battle).message == "/choose move quickattack"

    battle.available_moves.append(Move("flamethrower", gen=8))
    assert player.choose_move(battle).message == "/choose move flamethrower"

    player_pkg.Battle = (
        Battle  # this is in case a test runner shares memory between tests
    )


def test_simple_heuristics_player_estimate_matchup():
    player = SimpleHeuristicsPlayer(start_listening=False)

    dragapult = Pokemon(species="dragapult", gen=8)
    assert player._estimate_matchup(dragapult, dragapult) == 0

    gengar = Pokemon(species="gengar", gen=8)
    assert player._estimate_matchup(dragapult, gengar) == -player._estimate_matchup(
        gengar, dragapult
    )
    assert player._estimate_matchup(dragapult, gengar) == player.SPEED_TIER_COEFICIENT

    mamoswine = Pokemon(species="mamoswine", gen=8)
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
        Pokemon(species="charmander", gen=8),
        Pokemon(species="charmander", gen=8),
        {},
        False,
    )
    assert player._should_dynamax(battle, 4) is False

    battle = PseudoBattle(
        Pokemon(species="charmander", gen=8),
        Pokemon(species="charmander", gen=8),
        {},
        True,
    )
    assert player._should_dynamax(battle, 1) is True

    battle.active_pokemon._set_hp("100/100")
    battle.team["charmander"] = battle.active_pokemon
    assert player._should_dynamax(battle, 4) is True

    battle = PseudoBattle(
        Pokemon(species="squirtle", gen=8),
        Pokemon(species="charmander", gen=8),
        {
            "kakuna": Pokemon(species="kakuna", gen=8),
            "venusaur": Pokemon(species="venusaur", gen=8),
            "charmander": Pokemon(species="charmander", gen=8),
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
        Pokemon(species="charmander", gen=8),
        Pokemon(species="charmander", gen=8),
        [],
    )
    battle.active_pokemon._last_request["stats"] = {
        stat: 0 for stat in battle.active_pokemon.base_stats
    }
    assert player._should_switch_out(battle) is False

    battle.available_switches.append(Pokemon(species="venusaur", gen=8))
    assert player._should_switch_out(battle) is False

    battle.available_switches.append(Pokemon(species="gyarados", gen=8))
    assert player._should_switch_out(battle) is False

    battle.active_pokemon._boost("spa", -3)
    battle.active_pokemon._last_request["stats"].update({"atk": 10, "spa": 20})
    assert player._should_switch_out(battle) is True

    battle.active_pokemon._last_request["stats"].update({"atk": 30, "spa": 20})
    assert player._should_switch_out(battle) is False

    battle.active_pokemon._boost("atk", -3)
    assert player._should_switch_out(battle) is True

    battle = PseudoBattle(
        Pokemon(species="gible", gen=8),
        Pokemon(species="mamoswine", gen=8),
        [Pokemon(species="charizard", gen=8)],
    )
    assert player._should_switch_out(battle) is True


def test_simple_heuristics_player_stat_estimation():
    player = SimpleHeuristicsPlayer(start_listening=False)
    mon = Pokemon(species="charizard", gen=8)

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
        Pokemon(species="dragapult", gen=8),
        Pokemon(species="gengar", gen=8),
        [],
        [Pokemon(species="togekiss", gen=8)],
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

    battle.available_moves.append(Move("quickattack", gen=8))
    assert player.choose_move(battle).message == "/choose move quickattack"

    battle.available_moves.append(Move("flamethrower", gen=8))
    assert player.choose_move(battle).message == "/choose move flamethrower"

    battle.available_moves.append(Move("dracometeor", gen=8))
    assert player.choose_move(battle).message == "/choose move dracometeor"

    battle.active_pokemon._boost("atk", -3)
    battle.active_pokemon._boost("spa", -3)
    battle.available_switches.append(Pokemon(species="sneasel", gen=8))
    battle.available_switches[1]._set_hp("100/100")
    assert player.choose_move(battle).message == "/choose switch sneasel"


def test_random_player():
    from poke_env.player import player as player_pkg
    from poke_env.environment import Battle

    player = RandomPlayer(start_listening=False)

    PseudoBattle = namedtuple(
        "PseudoBattle",
        (
            "available_moves",
            "available_switches",
            "can_z_move",
            "can_dynamax",
            "can_terastallize",
            "can_mega_evolve",
            "gen",
        ),
    )
    battle = PseudoBattle([], [], False, False, False, False, 8)

    player_pkg.Battle = PseudoBattle

    assert player.choose_move(battle).message == "/choose default"

    battle.available_switches.append(Pokemon(species="ponyta", gen=8))
    assert player.choose_move(battle).message == "/choose switch ponyta"

    battle.available_moves.append(Move("protect", gen=8))
    assert player.choose_move(battle).message in {
        "/choose move protect",
        "/choose switch ponyta",
    }

    battle.available_moves.append(Move("quickattack", gen=8))
    assert player.choose_move(battle).message in {
        "/choose move protect",
        "/choose switch ponyta",
        "/choose move quickattack",
    }

    battle.available_moves.append(Move("flamethrower", gen=8))
    assert player.choose_move(battle).message in {
        "/choose move protect",
        "/choose switch ponyta",
        "/choose move quickattack",
        "/choose move flamethrower",
    }

    assert {player.choose_move(battle).message for _ in range(500)} == {
        "/choose move protect",
        "/choose switch ponyta",
        "/choose move quickattack",
        "/choose move flamethrower",
    }

    player_pkg.Battle = (
        Battle  # this is in case a test runner shares memory between tests
    )
