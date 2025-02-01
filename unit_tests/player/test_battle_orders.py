from poke_env.environment import EmptyMove, Move, Pokemon
from poke_env.player import BattleOrder, DoubleBattleOrder, ForfeitBattleOrder


def test_recharge_order():
    recharge = EmptyMove("recharge")
    assert BattleOrder(recharge).message == "/choose move 1"


def test_single_orders():
    move = Move("flamethrower", gen=8)
    assert (
        BattleOrder(move).message
        == "/choose move flamethrower"
        == str(BattleOrder(move))
    )

    assert BattleOrder(move, mega=True).message == "/choose move flamethrower mega"

    assert BattleOrder(move, z_move=True).message == "/choose move flamethrower zmove"

    mon = Pokemon(species="charizard", gen=8)
    assert BattleOrder(mon).message == "/choose switch charizard"


def test_double_orders():
    move = BattleOrder(Move("selfdestruct", gen=8), move_target=2)
    mon = BattleOrder(Pokemon(species="lugia", gen=8))

    assert (
        DoubleBattleOrder(move, mon).message
        == "/choose move selfdestruct 2, switch lugia"
    )
    assert (
        DoubleBattleOrder(mon, move).message
        == "/choose switch lugia, move selfdestruct 2"
    )
    assert DoubleBattleOrder(mon).message == "/choose switch lugia, pass"
    assert DoubleBattleOrder(None, move).message == "/choose pass, move selfdestruct 2"
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
        "/choose move selfdestruct 2, pass",
        "/choose switch lugia, pass",
    }
    assert second == {
        "/choose pass, move selfdestruct 2",
        "/choose pass, switch lugia",
    }
    assert none == {"/choose default"}


def test_forfeit_order():
    fo = ForfeitBattleOrder()
    assert isinstance(fo, BattleOrder)
    assert fo.message == "/forfeit"
