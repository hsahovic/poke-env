# -*- coding: utf-8 -*-
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.player.baselines import MaxBasePowerPlayer
from collections import namedtuple


def test_max_base_power_player():
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

    assert player.choose_move(battle) == "/choose default"

    battle.available_switches.append(Pokemon(species="ponyta"))
    assert player.choose_move(battle) == "/choose switch ponyta"

    battle.available_moves.append(Move("protect"))
    assert player.choose_move(battle) == "/choose move protect"

    battle.available_moves.append(Move("quickattack"))
    assert player.choose_move(battle) == "/choose move quickattack"

    battle.available_moves.append(Move("flamethrower"))
    assert player.choose_move(battle) == "/choose move flamethrower"
