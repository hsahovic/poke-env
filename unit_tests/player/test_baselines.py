from collections import namedtuple

from poke_env.battle import Battle, DoubleBattle, Move, Pokemon
from poke_env.player import MaxBasePowerPlayer, RandomPlayer, SimpleHeuristicsPlayer


def test_max_base_power_player():
    player = MaxBasePowerPlayer(start_listening=False)

    battle = Battle("test_battle", "test_player", None, 8)
    battle._available_moves = []
    battle._available_switches = []
    battle._can_z_move = False
    battle._can_dynamax = False
    battle._can_tera = False
    battle._can_mega_evolve = False

    assert player.choose_move(battle).message == "/choose default"

    battle._available_switches.append(Pokemon(species="ponyta", gen=8))
    assert player.choose_move(battle).message == "/choose switch Ponyta"

    battle._available_moves.append(Move("protect", gen=8))
    assert player.choose_move(battle).message == "/choose move protect"

    battle._available_moves.append(Move("quickattack", gen=8))
    assert player.choose_move(battle).message == "/choose move quickattack"

    battle._available_moves.append(Move("flamethrower", gen=8))
    assert player.choose_move(battle).message == "/choose move flamethrower"


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


def test_simple_heuristics_player_should_terastallize():
    player = SimpleHeuristicsPlayer(start_listening=False)

    active = Pokemon(species="charizard", gen=9)
    opponent = Pokemon(species="venusaur", gen=9)
    move = Move("flamethrower", gen=9)
    active._terastallized_type = move.type
    active.set_hp("100/100")
    opponent.set_hp("100/100")

    battle = namedtuple(
        "PseudoBattle", ["active_pokemon", "opponent_active_pokemon", "can_tera", "gen"]
    )(active, opponent, True, 9)

    assert player._should_terastallize(battle, move) is True

    battle = battle._replace(can_tera=False)
    assert player._should_terastallize(battle, move) is False


def test_simple_heuristics_player_should_switch_out():
    PseudoBattle = namedtuple(
        "PseudoBattle",
        ["active_pokemon", "opponent_active_pokemon", "available_switches"],
    )
    player = SimpleHeuristicsPlayer(start_listening=False)

    battle = PseudoBattle(
        Pokemon(species="charmander", gen=8), Pokemon(species="charmander", gen=8), []
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
    assert player.choose_move(battle).message == "/choose switch Togekiss"

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
    assert player.choose_move(battle).message == "/choose switch Sneasel"


def test_simple_heuristics_player_in_doubles():
    player = SimpleHeuristicsPlayer(start_listening=False)
    battle = DoubleBattle("battletag", "username", None, gen=9)
    battle._player_role = "p1"

    # Patch team
    mon1 = Pokemon(9, species="charizard")
    mon1._active = True
    mon2 = Pokemon(9, species="pikachu")
    mon2._active = True
    opp1 = Pokemon(9, species="venusaur")
    opp1._active = True
    opp2 = Pokemon(9, species="blastoise")
    opp2._active = True

    battle._team = {mon1.name: mon1, mon2.name: mon2}
    battle._opponent_team = {opp1.name: opp1, opp2.name: opp2}
    battle._active_pokemon = {"p1a": mon1, "p1b": mon2}
    battle._opponent_active_pokemon = {"p2a": opp1, "p2b": opp2}
    battle._available_moves = [
        [Move("flamethrower", gen=9)],
        [Move("thunderbolt", gen=9)],
    ]
    battle._available_switches = [[], []]

    assert (
        player.choose_move(battle).message
        == "/choose move flamethrower 1, move thunderbolt 2"
    )

    battle._opponent_active_pokemon = {"p2a": opp2, "p2b": opp1}
    assert (
        player.choose_move(battle).message
        == "/choose move flamethrower 2, move thunderbolt 1"
    )


def test_random_player():
    player = RandomPlayer(start_listening=False)

    battle = Battle("test_battle", "test_player", None, 8)
    battle._available_moves = []
    battle._available_switches = []
    battle._can_z_move = False
    battle._can_dynamax = False
    battle._can_tera = False
    battle._can_mega_evolve = False

    assert player.choose_move(battle).message == "/choose default"

    mon = Pokemon(species="charizard", gen=8)
    mon._active = True
    battle._team = {"charizard": mon}
    battle._available_switches.append(Pokemon(species="ponyta", gen=8))
    assert player.choose_move(battle).message == "/choose switch Ponyta"

    battle._available_moves.append(Move("protect", gen=8))
    assert player.choose_move(battle).message in {
        "/choose move protect",
        "/choose switch Ponyta",
    }

    battle._available_moves.append(Move("quickattack", gen=8))
    assert player.choose_move(battle).message in {
        "/choose move protect",
        "/choose switch Ponyta",
        "/choose move quickattack",
    }

    battle._available_moves.append(Move("flamethrower", gen=8))
    assert player.choose_move(battle).message in {
        "/choose move protect",
        "/choose switch Ponyta",
        "/choose move quickattack",
        "/choose move flamethrower",
    }

    assert {player.choose_move(battle).message for _ in range(500)} == {
        "/choose move protect",
        "/choose switch Ponyta",
        "/choose move quickattack",
        "/choose move flamethrower",
    }
