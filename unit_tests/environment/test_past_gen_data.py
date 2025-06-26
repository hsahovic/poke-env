from unittest.mock import MagicMock

import pytest

from poke_env.battle import Battle, Move, MoveCategory, Pokemon
from poke_env.data import GenData

# MOVES TESTS


def move_generator(gen):
    for move in GenData.from_gen(gen).moves:
        yield Move(move, gen=gen)


def test_tackle():
    g4 = Move("tackle", gen=4)
    g5 = Move("tackle", gen=5)
    g6 = Move("tackle", gen=6)
    g7 = Move("tackle", gen=7)
    g8 = Move("tackle", gen=8)
    assert g4.base_power == 35
    assert g5.base_power == 50
    assert g6.base_power == 50
    assert g7.base_power == 40
    assert g8.base_power == 40


def test_water_shuriken():
    try:
        Move("watershuriken", gen=5)
        assert 1 == 0
    except ValueError:
        assert 1 == 1


def test_accuracy():
    g7_volt_thunderbolt = Move("10000000voltthunderbolt", gen=7)
    g8_volt_thunderbolt = Move("10000000voltthunderbolt", gen=8)
    assert g7_volt_thunderbolt.accuracy == 1
    assert g8_volt_thunderbolt.accuracy == 1

    for gen in range(4, 8 + 1):
        absorb = Move("absorb", gen=gen)
        aeroblast = Move("aeroblast", gen=gen)
        assert absorb.accuracy == 1
        assert aeroblast.accuracy == 0.95

        for move in move_generator(gen):
            assert isinstance(move.accuracy, float)
            assert 0 <= move.accuracy <= 1


def test_all_moves_instanciate():
    for gen in range(4, 8 + 1):
        for move in move_generator(gen):
            move_from_id = Move(move_id=move.id, gen=gen)
            assert str(move) == str(move_from_id)


def test_category():
    for gen in range(4, 8 + 1):
        flame_thrower = Move("flamethrower", gen=gen)
        close_combat = Move("closecombat", gen=gen)
        protect = Move("protect", gen=gen)

        assert flame_thrower.category == MoveCategory["SPECIAL"]
        assert close_combat.category == MoveCategory["PHYSICAL"]
        assert protect.category == MoveCategory["STATUS"]

        for move in move_generator(gen):
            assert isinstance(move.category, MoveCategory)


# POKEMON TESTS


def test_right_gen_move():
    for gen in range(4, 8 + 1):
        mon = Pokemon(species="charizard", gen=gen)

        mon.moved("flamethrower")
        assert "flamethrower" in mon.moves
        flame_thrower = mon.moves["flamethrower"]
        assert flame_thrower._moves_dict == GenData.from_gen(gen).moves


def test_right_abilities():
    g4_nido = Pokemon(species="nidoqueen", gen=4)
    assert len(g4_nido.possible_abilities) == 2
    g5_nido = Pokemon(species="nidoqueen", gen=5)
    assert len(g5_nido.possible_abilities) == 3

    g5_dusk = Pokemon(species="dusknoir", gen=5)
    assert len(g5_dusk.possible_abilities) == 1
    g6_dusk = Pokemon(species="dusknoir", gen=6)
    assert len(g6_dusk.possible_abilities) == 2

    g7_weez = Pokemon(species="weezing", gen=7)
    assert len(g7_weez.possible_abilities) == 1
    g8_weez = Pokemon(species="weezing", gen=8)
    assert len(g8_weez.possible_abilities) == 3


# BATTLE TEST


def test_right_gen_mon():
    for gen in range(1, 9):
        logger = MagicMock()
        battle = Battle("tag", "username", logger, gen=gen)

        if gen == 1:
            with pytest.raises(KeyError):
                battle.get_pokemon("p2: azumarill", force_self_team=True)
            continue

        battle.get_pokemon("p2: azumarill", force_self_team=True)

        assert "p2: azumarill" in battle.team
        assert battle.team["p2: azumarill"]._data.gen == gen
