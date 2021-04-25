from poke_env.data import GEN_TO_MOVES
from poke_env.environment.move import (
    Move,
    Gen4Move,
    Gen5Move,
    Gen6Move,
    Gen7Move,
    Gen8Move,
    GEN_TO_MOVE_CLASS,
)
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon import (
    Gen4Pokemon,
    Gen5Pokemon,
    Gen6Pokemon,
    Gen7Pokemon,
    Gen8Pokemon,
    GEN_TO_POKEMON,
)
from poke_env.environment.battle import (
    Gen4Battle,
    Gen5Battle,
    Gen6Battle,
    Gen7Battle,
    Gen8Battle,
)
from unittest.mock import MagicMock

# MOVES TESTS


def move_generator(gen):
    for move in GEN_TO_MOVES[gen]:
        yield GEN_TO_MOVE_CLASS[gen](move)


def test_tackle():
    g4 = Gen4Move("tackle")
    g5 = Gen5Move("tackle")
    g6 = Gen6Move("tackle")
    g7 = Gen7Move("tackle")
    g8 = Gen8Move("tackle")
    gx = Move("tackle")
    assert g4.base_power == 35
    assert g5.base_power == 50
    assert g6.base_power == 50
    assert g7.base_power == 40
    assert g8.base_power == 40
    assert gx.base_power == 40


def test_water_shuriken():
    try:
        Gen5Move("watershuriken")
        assert 1 == 0
    except ValueError:
        assert 1 == 1


def test_accuracy():
    g7_volt_thunderbolt = Gen7Move("10000000voltthunderbolt")
    g8_volt_thunderbolt = Gen8Move("10000000voltthunderbolt")
    assert g7_volt_thunderbolt.accuracy == 1
    assert g8_volt_thunderbolt.accuracy == 1

    for gen in range(4, 8 + 1):
        absorb = GEN_TO_MOVE_CLASS[gen]("absorb")
        aeroblast = GEN_TO_MOVE_CLASS[gen]("aeroblast")
        assert absorb.accuracy == 1
        assert aeroblast.accuracy == 0.95

        for move in move_generator(gen):
            assert isinstance(move.accuracy, float)
            assert 0 <= move.accuracy <= 1


def test_all_moves_instanciate():
    for gen in range(4, 8 + 1):
        for move in move_generator(gen):
            move_from_id = GEN_TO_MOVE_CLASS[gen](move_id=move.id)
            assert str(move) == str(move_from_id)


def test_category():
    for gen in range(4, 8 + 1):
        flame_thrower = GEN_TO_MOVE_CLASS[gen]("flamethrower")
        close_combat = GEN_TO_MOVE_CLASS[gen]("closecombat")
        protect = GEN_TO_MOVE_CLASS[gen]("protect")

        assert flame_thrower.category == MoveCategory["SPECIAL"]
        assert close_combat.category == MoveCategory["PHYSICAL"]
        assert protect.category == MoveCategory["STATUS"]

        for move in move_generator(gen):
            assert isinstance(move.category, MoveCategory)


# POKEMON TESTS


def test_right_gen_move():
    for gen in range(4, 8 + 1):
        mon = GEN_TO_POKEMON[gen](species="charizard")

        mon._moved("flamethrower")
        assert "flamethrower" in mon.moves
        flame_thrower = mon.moves["flamethrower"]
        assert isinstance(flame_thrower, GEN_TO_MOVE_CLASS[gen])


def test_right_abilities():
    g4_nido = Gen4Pokemon(species="nidoqueen")
    assert len(g4_nido.possible_abilities) == 2
    g5_nido = Gen5Pokemon(species="nidoqueen")
    assert len(g5_nido.possible_abilities) == 3

    g5_dusk = Gen5Pokemon(species="dusknoir")
    assert len(g5_dusk.possible_abilities) == 1
    g6_dusk = Gen6Pokemon(species="dusknoir")
    assert len(g6_dusk.possible_abilities) == 2

    g7_weez = Gen7Pokemon(species="weezing")
    assert len(g7_weez.possible_abilities) == 1
    g8_weez = Gen8Pokemon(species="weezing")
    assert len(g8_weez.possible_abilities) == 3


# BATTLE TEST


def test_right_gen_mon():
    GEN_TO_BATTLE = {
        4: Gen4Battle,
        5: Gen5Battle,
        6: Gen6Battle,
        7: Gen7Battle,
        8: Gen8Battle,
    }
    for gen in range(4, 8 + 1):
        logger = MagicMock()
        battle = GEN_TO_BATTLE[gen]("tag", "username", logger)

        battle.get_pokemon("p2: azumarill", force_self_team=True)
        assert "p2: azumarill" in battle.team
        assert isinstance(battle.team["p2: azumarill"], GEN_TO_POKEMON[gen])
