# -*- coding: utf-8 -*-
from poke_env.data import MOVES
from poke_env.environment.move import Move
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.status import Status


def move_generator():
    for move in MOVES:
        yield Move(move)


def test_accuracy():
    volt_thunderbolt = Move("10000000voltthunderbolt")
    absorb = Move("absorb")
    aeroblast = Move("aeroblast")

    assert volt_thunderbolt.accuracy == 1
    assert absorb.accuracy == 1
    assert aeroblast.accuracy == 0.95

    for move in move_generator():
        assert isinstance(move.accuracy, float)
        assert 0 <= move.accuracy <= 1


def test_all_moves_instanciate():
    for move in move_generator():
        pass


def test_drain():
    draining_kiss = Move("drainingkiss")
    flame_thrower = Move("flamethrower")

    assert draining_kiss.drain == 0.75
    assert flame_thrower.drain == 0

    for move in move_generator():
        assert isinstance(move.drain, float)
        assert 0 <= move.drain <= 1


def test_heal():
    roost = Move("roost")
    flame_thrower = Move("flamethrower")

    assert roost.heal == 0.5
    assert flame_thrower.heal == 0

    for move in move_generator():
        assert isinstance(move.heal, float)
        assert 0 <= move.heal <= 1


def test_ignore_immunity():
    thousand_arrows = Move("thousandarrows")
    thunder_wave = Move("thunderwave")
    bide = Move("bide")
    flame_thrower = Move("flamethrower")

    assert thousand_arrows.ignore_immunity == {PokemonType["GROUND"]}
    assert thunder_wave.ignore_immunity is False
    assert bide.ignore_immunity is True
    assert flame_thrower.ignore_immunity is False

    for move in move_generator():
        assert type(move.ignore_immunity) in [bool, set]


def test_move_base_power():
    for move in move_generator():
        assert isinstance(move.base_power, int)
        assert 0 <= move.base_power <= 255


def test_move_breaks_protect():
    for move in move_generator():
        assert isinstance(move.breaks_protect, bool)


def test_n_hit():
    furys_wipes = Move("furyswipes")
    flame_thrower = Move("flamethrower")
    gear_grind = Move("geargrind")

    assert furys_wipes.n_hit == (2, 5)
    assert flame_thrower.n_hit == (1, 1)
    assert gear_grind.n_hit == (2, 2)

    for move in move_generator():
        assert isinstance(move.n_hit, tuple) and len(move.n_hit) == 2


def test_recoil():
    flare_blitz = Move("flareblitz")
    flame_thrower = Move("flamethrower")

    assert flare_blitz.recoil == 0.33
    assert flame_thrower.recoil == 0

    for move in move_generator():
        assert isinstance(move.recoil, float)
        assert 0 <= move.recoil <= 1


def test_self_boosts():
    clanging_scales = Move("clangingscales")
    close_combat = Move("closecombat")
    fire_blast = Move("fireblast")

    assert fire_blast.self_boost is None
    assert close_combat.self_boost == {"def": -1, "spd": -1}
    assert clanging_scales.self_boost == {"def": -1}

    for move in move_generator():
        assert move.self_boost is None or isinstance(move.self_boost, dict)


def test_status():
    dark_void = Move("darkvoid")
    sleep_powder = Move("sleeppowder")
    flame_thrower = Move("flamethrower")
    thunder_wave = Move("thunderwave")

    assert dark_void.status == Status["SLP"]
    assert sleep_powder.status == Status["SLP"]
    assert thunder_wave.status == Status["PAR"]
    assert flame_thrower.status is None

    for move in move_generator():
        assert move.status is None or isinstance(move.status, Status)
