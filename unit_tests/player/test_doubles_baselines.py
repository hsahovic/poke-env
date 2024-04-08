from poke_env.environment import Move, Pokemon
from poke_env.player import DoublesMaxBasePowerPlayer


def test_doubles_max_damage_player():
    from poke_env.environment import DoubleBattle
    from poke_env.player import player as player_pkg

    player = DoublesMaxBasePowerPlayer(start_listening=False)

    battle = DoubleBattle(
        battle_tag="placeholder_battle_tag",
        username="placeholder_username",
        logger=None,
        gen=8,
    )
    battle.player_role = "p1"
    active_pikachu = Pokemon(species="pikachu", gen=8)
    active_pikachu.switch_in()
    battle._active_pokemon["p1a"] = active_pikachu

    # player_pkg.Battle = PseudoBattle
    player_pkg.Battle = DoubleBattle

    # calls player.choose_random_doubles_move(battle)
    assert player.choose_move(battle).message == "/choose default"

    # calls player.choose_random_doubles_move(battle)
    battle._available_switches[0].append(Pokemon(species="ponyta", gen=8))
    assert player.choose_move(battle).message == "/choose switch ponyta, default"

    active_raichu = Pokemon(species="raichu", gen=8)
    active_raichu.switch_in()
    battle._active_pokemon["p1b"] = active_raichu

    # calls player.choose_random_doubles_move(battle)
    battle._available_switches[1].append(Pokemon(species="rapidash", gen=8))
    assert (
        player.choose_move(battle).message == "/choose switch ponyta, switch rapidash"
    )

    active_ducklett = Pokemon(species="ducklett", gen=8)
    active_ducklett.switch_in()
    battle._active_pokemon["p2a"] = active_ducklett
    active_swanna = Pokemon(species="swanna", gen=8)
    active_swanna.switch_in()
    battle._active_pokemon["p2b"] = active_swanna

    # chooses a move for p1a, other slot defaults
    battle._available_moves[0].append(Move("protect", gen=8))
    assert player.choose_move(battle).message == "/choose move protect, default"

    # chooses max BP move for both pokemon, targets chosen randomly
    battle._available_moves[0].append(Move("quickattack", gen=8))
    battle._available_moves[0].append(Move("quickattack", gen=8))
    battle._available_moves[1].append(Move("flamethrower", gen=8))
    assert player.choose_move(battle).message in [
        "/choose move quickattack 1, move flamethrower 1",
        "/choose move quickattack 1, move flamethrower 2",
        "/choose move quickattack 2, move flamethrower 1",
        "/choose move quickattack 2, move flamethrower 2",
    ]

    # chooses spread move for p1b
    battle._available_moves[1].append(Move("dazzlinggleam", gen=8))
    assert player.choose_move(battle).message in [
        "/choose move quickattack 1, move dazzlinggleam",
        "/choose move quickattack 2, move dazzlinggleam",
    ]

    player_pkg.Battle = (
        DoubleBattle  # this is in case a test runner shares memory between tests
    )
