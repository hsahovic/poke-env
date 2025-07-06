from collections import namedtuple

from poke_env.battle import Move, Pokemon
from poke_env.player import MaxBasePowerPlayer, RandomPlayer, SimpleHeuristicsPlayer


def test_max_base_power_player():
    from poke_env.battle import Battle
    from poke_env.player import player as player_pkg

    player = MaxBasePowerPlayer(start_listening=False)

    PseudoBattle = namedtuple(
        "PseudoBattle",
        (
            "available_moves",
            "available_switches",
            "can_z_move",
            "can_dynamax",
            "can_tera",
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

    dragapult.set_hp("100/100")
    mamoswine.set_hp("50/100")
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

    battle.active_pokemon.set_hp("100/100")
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
        mon.set_hp("100/100")
    battle.active_pokemon.set_hp("100/100")
    battle.opponent_active_pokemon.set_hp("100/100")

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
    battle.active_pokemon.stats = {stat: 0 for stat in battle.active_pokemon.base_stats}
    assert player._should_switch_out(battle) is False

    battle.available_switches.append(Pokemon(species="venusaur", gen=8))
    assert player._should_switch_out(battle) is False

    battle.available_switches.append(Pokemon(species="gyarados", gen=8))
    assert player._should_switch_out(battle) is False

    battle.active_pokemon.boost("spa", -3)
    battle.active_pokemon.stats.update({"atk": 10, "spa": 20})
    assert player._should_switch_out(battle) is True

    battle.active_pokemon.stats.update({"atk": 30, "spa": 20})
    assert player._should_switch_out(battle) is False

    battle.active_pokemon.boost("atk", -3)
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

    mon.boost("spe", 2)
    assert player._stat_estimation(mon, "spe") == 472

    mon.boost("atk", -1)
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
            "opponent_team",
            "can_dynamax",
            "can_tera",
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
        {},
        True,
        True,
        set(),
        set(),
    )
    battle.active_pokemon.stats = {
        stat: 100 for stat in battle.active_pokemon.base_stats
    }

    battle.available_switches[0].set_hp("100/100")
    assert player.choose_move(battle).message == "/choose switch togekiss"

    battle.available_moves.append(Move("quickattack", gen=8))
    assert player.choose_move(battle).message == "/choose move quickattack"

    battle.available_moves.append(Move("flamethrower", gen=8))
    assert player.choose_move(battle).message == "/choose move flamethrower"

    battle.available_moves.append(Move("dracometeor", gen=8))
    assert player.choose_move(battle).message == "/choose move dracometeor"

    battle.active_pokemon.boost("atk", -3)
    battle.active_pokemon.boost("spa", -3)
    battle.available_switches.append(Pokemon(species="sneasel", gen=8))
    battle.available_switches[1].set_hp("100/100")
    assert player.choose_move(battle).message == "/choose switch sneasel"


def test_random_player():
    from poke_env.battle import Battle
    from poke_env.player import player as player_pkg

    player = RandomPlayer(start_listening=False)

    PseudoBattle = namedtuple(
        "PseudoBattle",
        (
            "available_moves",
            "available_switches",
            "can_z_move",
            "can_dynamax",
            "can_tera",
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
