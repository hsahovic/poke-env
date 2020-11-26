# -*- coding: utf-8 -*-
from poke_env.player.battle_order import BattleOrder, DoubleBattleOrder
from poke_env.environment.move import Move, SPECIAL_MOVES
from poke_env.environment.pokemon import Pokemon


def test_recharge_order():
    recharge = SPECIAL_MOVES["recharge"]
    assert BattleOrder(recharge).message == "/choose move 1"


def test_single_orders():
    move = Move("flamethrower")
    assert BattleOrder(move).message == "/choose move flamethrower"

    assert BattleOrder(move, mega=True).message == "/choose move flamethrower mega"

    assert BattleOrder(move, z_move=True).message == "/choose move flamethrower zmove"

    mon = Pokemon(species="charizard")
    assert BattleOrder(mon).message == "/choose switch charizard"


def test_double_orders():
    move = BattleOrder(Move("selfdestruct"), move_target=2)
    mon = BattleOrder(Pokemon(species="lugia"))

    assert (
        DoubleBattleOrder(move, mon).message
        == "/choose move selfdestruct 2, switch lugia"
    )
    assert (
        DoubleBattleOrder(mon, move).message
        == "/choose switch lugia, move selfdestruct 2"
    )
    assert DoubleBattleOrder(mon).message == "/choose switch lugia, default"
    assert (
        DoubleBattleOrder(None, move).message == "/choose move selfdestruct 2, default"
    )
    assert DoubleBattleOrder().message == "/choose default"

    orders = [move, mon]

    both = {order.message for order in DoubleBattleOrder.join_orders(orders, orders)}
    first = {order.message for order in DoubleBattleOrder.join_orders(orders, [])}
    second = {order.message for order in DoubleBattleOrder.join_orders([], orders)}
    none = {order.message for order in DoubleBattleOrder.join_orders([], [])}

    assert both == {
        "/choose move selfdestruct 2, switch lugia",
        "/choose switch lugia, move selfdestruct 2",
    }
    assert first == {
        "/choose move selfdestruct 2, default",
        "/choose switch lugia, default",
    }
    assert second == {
        "/choose move selfdestruct 2, default",
        "/choose switch lugia, default",
    }
    assert none == {"/choose default"}
