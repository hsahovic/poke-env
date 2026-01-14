from poke_env.battle import Move, Pokemon
from poke_env.player import (
    BattleOrder,
    DoubleBattleOrder,
    ForfeitBattleOrder,
    PassBattleOrder,
    SingleBattleOrder,
)


def test_single_orders():
    move = Move("flamethrower", gen=8)
    assert (
        SingleBattleOrder(move).message
        == "/choose move flamethrower"
        == str(SingleBattleOrder(move))
    )

    assert (
        SingleBattleOrder(move, mega=True).message == "/choose move flamethrower mega"
    )

    assert (
        SingleBattleOrder(move, z_move=True).message
        == "/choose move flamethrower zmove"
    )

    mon = Pokemon(species="charizard", gen=8)
    assert SingleBattleOrder(mon).message == "/choose switch Charizard"

    assert SingleBattleOrder(move, mega=True, move_target=2) == SingleBattleOrder(
        move, mega=True, move_target=2
    )


def test_pass_order():
    po = PassBattleOrder()
    assert isinstance(po, BattleOrder)
    assert po.message == "/choose pass"

    so = PassBattleOrder()
    assert so == po


def test_double_orders():
    move = SingleBattleOrder(Move("selfdestruct", gen=8), move_target=2)
    mon = SingleBattleOrder(Pokemon(species="lugia", gen=8))

    assert (
        DoubleBattleOrder(move, mon).message
        == "/choose move selfdestruct 2, switch Lugia"
    )
    assert (
        DoubleBattleOrder(mon, move).message
        == "/choose switch Lugia, move selfdestruct 2"
    )
    assert DoubleBattleOrder(mon).message == "/choose switch Lugia, pass"
    assert (
        DoubleBattleOrder(second_order=move).message
        == "/choose pass, move selfdestruct 2"
    )
    assert DoubleBattleOrder().message == "/choose pass, pass"

    orders = [move, mon]

    both = {order.message for order in DoubleBattleOrder.join_orders(orders, orders)}
    first = {order.message for order in DoubleBattleOrder.join_orders(orders, [])}
    second = {order.message for order in DoubleBattleOrder.join_orders([], orders)}
    none = {order.message for order in DoubleBattleOrder.join_orders([], [])}

    assert both == {
        "/choose move selfdestruct 2, move selfdestruct 2",
        "/choose move selfdestruct 2, switch Lugia",
        "/choose switch Lugia, move selfdestruct 2",
    }
    assert first == {"/choose move selfdestruct 2, pass", "/choose switch Lugia, pass"}
    assert second == {"/choose pass, move selfdestruct 2", "/choose pass, switch Lugia"}
    assert none == set()


def test_forfeit_order():
    fo = ForfeitBattleOrder()
    assert isinstance(fo, BattleOrder)
    assert fo.message == "/forfeit"
