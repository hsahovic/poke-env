# -*- coding: utf-8 -*-
from poke_env.data import MOVES
from poke_env.environment.move import Move, EmptyMove
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.weather import Weather
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
        move_from_id = Move(move_id=move._id)
        assert str(move) == str(move_from_id)


def test_can_z_move():
    metronome = Move("metronome")
    flame_thrower = Move("flamethrower")

    assert metronome.can_z_move is False
    assert flame_thrower.can_z_move is True

    for move in move_generator():
        assert isinstance(move.can_z_move, bool)


def test_category():
    flame_thrower = Move("flamethrower")
    close_combat = Move("closecombat")
    protect = Move("protect")

    assert flame_thrower.category == MoveCategory["SPECIAL"]
    assert close_combat.category == MoveCategory["PHYSICAL"]
    assert protect.category == MoveCategory["STATUS"]

    for move in move_generator():
        assert isinstance(move.category, MoveCategory)


def test_drain():
    draining_kiss = Move("drainingkiss")
    flame_thrower = Move("flamethrower")

    assert draining_kiss.drain == 0.75
    assert flame_thrower.drain == 0

    for move in move_generator():
        assert isinstance(move.drain, float)
        assert 0 <= move.drain <= 1


def test_empty_move():
    # instanciation
    special_move = EmptyMove("justamove")

    assert special_move.drain == 0
    assert special_move.base_power == 0


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


def test_weather():
    flame_thrower = Move("flamethrower")
    sand_storm = Move("sandstorm")

    assert flame_thrower.weather is None
    assert sand_storm.weather is Weather["SANDSTORM"]


def test_z_move_boost():
    misty_terrain = Move("mistyterrain")
    flame_thrower = Move("flamethrower")
    mist = Move("mist")

    assert misty_terrain.z_move_boost == {"spd": 1}
    assert flame_thrower.z_move_boost is None
    assert mist.z_move_boost is None

    for move in move_generator():
        assert move.z_move_boost is None or isinstance(move.z_move_boost, dict)


def test_z_move_effect():
    flare_blitz = Move("flareblitz")
    flame_thrower = Move("flamethrower")
    mist = Move("mist")

    assert flare_blitz.z_move_effect is None
    assert flame_thrower.z_move_effect is None
    assert mist.z_move_effect == "heal"

    for move in move_generator():
        assert move.z_move_effect is None or isinstance(move.z_move_effect, str)


def test_z_move_power():
    flare_blitz = Move("flareblitz")
    flame_thrower = Move("flamethrower")
    mist = Move("mist")

    assert flare_blitz.z_move_power == 190
    assert flame_thrower.z_move_power == 175
    assert mist.z_move_power == 0

    for move in move_generator():
        assert isinstance(move.z_move_power, int)
