# -*- coding: utf-8 -*-
import copy

from poke_env.data import MOVES
from poke_env.environment.field import Field
from poke_env.environment.move import Move, EmptyMove
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.weather import Weather
from poke_env.environment.status import Status


def move_generator():
    for move in MOVES:
        yield Move(move)
        yield Move("z" + move)


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
        move_from_id = Move(move_id=move.id)
        assert str(move) == str(move_from_id)


def test_boosts():
    sharpen = Move("sharpen")
    flame_thrower = Move("flamethrower")

    assert flame_thrower.boosts is None
    assert sharpen.boosts == {"atk": 1}

    for move in move_generator():
        assert move.boosts is None or isinstance(move.boosts, dict)


def test_can_z_move():
    flame_thrower = Move("flamethrower")

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


def test_crit_ratio():
    aeroblast = Move("aeroblast")
    flame_thrower = Move("flamethrower")

    assert aeroblast.crit_ratio == 2
    assert flame_thrower.crit_ratio == 0

    for move in move_generator():
        assert isinstance(move.crit_ratio, int)


def test_current_pp():
    for move in move_generator():
        assert isinstance(move.current_pp, int)
        assert move.current_pp == move.max_pp


def test_damage():
    flame_thrower = Move("flamethrower")
    night_shade = Move("nightshade")
    dragon_rage = Move("dragonrage")

    assert flame_thrower.damage == 0
    assert night_shade.damage == "level"
    assert dragon_rage.damage == 40

    for move in move_generator():
        assert isinstance(move.damage, int) or isinstance(move.damage, str)


def test_defensive_category():
    psyshock = Move("psyshock")
    close_combat = Move("closecombat")
    flame_thrower = Move("flamethrower")

    assert psyshock.defensive_category == MoveCategory["PHYSICAL"]
    assert close_combat.defensive_category == MoveCategory["PHYSICAL"]
    assert flame_thrower.defensive_category == MoveCategory["SPECIAL"]

    for move in move_generator():
        assert isinstance(move.defensive_category, MoveCategory)


def test_drain():
    draining_kiss = Move("drainingkiss")
    flame_thrower = Move("flamethrower")

    assert draining_kiss.drain == 0.75
    assert flame_thrower.drain == 0

    for move in move_generator():
        assert isinstance(move.drain, float)
        assert 0 <= move.drain <= 1


def test_empty_move_basic():
    empty_move = EmptyMove("justamove")

    assert empty_move.drain == 0
    assert empty_move.base_power == 0
    assert empty_move.is_empty is True


def test_flags():
    flame_thrower = Move("flamethrower")
    sludge_bomb = Move("sludgebomb")

    assert flame_thrower.flags == {"protect", "mirror"}
    assert sludge_bomb.flags == {"bullet", "protect", "mirror"}
    for move in move_generator():
        assert isinstance(move.flags, set)


def test_heal():
    roost = Move("roost")
    flame_thrower = Move("flamethrower")

    assert roost.heal == 0.5
    assert flame_thrower.heal == 0

    for move in move_generator():
        assert isinstance(move.heal, float)
        assert 0 <= move.heal <= 1


def test_ignore_ability():
    flame_thrower = Move("flamethrower")
    menacing_moonraze_maelstrom = Move("menacingmoonrazemaelstrom")

    assert menacing_moonraze_maelstrom.ignore_ability is True
    assert flame_thrower.ignore_ability is False

    for move in move_generator():
        assert isinstance(move.ignore_ability, bool)


def test_ignore_defensive():
    flame_thrower = Move("flamethrower")
    chipaway = Move("chipaway")

    assert chipaway.ignore_defensive is True
    assert flame_thrower.ignore_defensive is False

    for move in move_generator():
        assert isinstance(move.ignore_defensive, bool)


def test_ignore_evasion():
    flame_thrower = Move("flamethrower")
    chipaway = Move("chipaway")

    assert chipaway.ignore_evasion is True
    assert flame_thrower.ignore_evasion is False

    for move in move_generator():
        assert isinstance(move.ignore_evasion, bool)


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


def test_is_z():
    flame_thrower = Move("flamethrower")
    clangorous_soul_blaze = Move("clangoroussoulblaze")

    assert clangorous_soul_blaze.is_z is True
    assert flame_thrower.is_z is False

    for move in move_generator():
        assert isinstance(move.is_z, bool)


def test_force_switch():
    flame_thrower = Move("flamethrower")
    dragon_tail = Move("dragontail")

    assert flame_thrower.force_switch is False
    assert dragon_tail.force_switch is True

    for move in move_generator():
        assert isinstance(move.force_switch, bool)


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


def test_no_pp_boosts():
    flame_thrower = Move("flamethrower")
    sketch = Move("sketch")

    assert sketch.no_pp_boosts is True
    assert flame_thrower.no_pp_boosts is False

    for move in move_generator():
        assert isinstance(move.no_pp_boosts, bool)


def test_non_ghost_target():
    flame_thrower = Move("flamethrower")
    curse = Move("curse")

    assert curse.non_ghost_target is True
    assert flame_thrower.non_ghost_target is False

    for move in move_generator():
        assert isinstance(move.non_ghost_target, bool)


def test_priority():
    flame_thrower = Move("flamethrower")
    trick_room = Move("trickroom")
    fake_out = Move("fakeout")

    assert flame_thrower.priority == 0
    assert trick_room.priority == -7
    assert fake_out.priority == 3

    for move in move_generator():
        assert isinstance(move.priority, int)


def test_pseudo_weather():
    flame_thrower = Move("flamethrower")
    fairy_lock = Move("fairylock")

    assert flame_thrower.pseudo_weather is None
    assert fairy_lock.pseudo_weather == "fairylock"

    for move in move_generator():
        assert isinstance(move.pseudo_weather, str) or move.pseudo_weather is None


def test_recoil():
    flare_blitz = Move("flareblitz")
    flame_thrower = Move("flamethrower")

    assert flare_blitz.recoil == 0.33
    assert flame_thrower.recoil == 0

    for move in move_generator():
        assert isinstance(move.recoil, float)
        assert 0 <= move.recoil <= 1


def test_secondary():
    fake_out = Move("fakeout")
    flame_thrower = Move("flamethrower")
    acid_armor = Move("acidarmor")

    assert fake_out.secondary == [{"chance": 100, "volatileStatus": "flinch"}]
    assert flame_thrower.secondary == [{"chance": 10, "status": "brn"}]
    assert acid_armor.secondary == []

    for move in move_generator():
        if move.secondary:
            print(move.id, move.secondary)
        assert isinstance(move.secondary, list)
        for secondary in move.secondary:
            assert isinstance(secondary, dict)


def test_self_boosts():
    clanging_scales = Move("clangingscales")
    close_combat = Move("closecombat")
    fire_blast = Move("fireblast")

    assert fire_blast.self_boost is None
    assert close_combat.self_boost == {"def": -1, "spd": -1}
    assert clanging_scales.self_boost == {"def": -1}

    for move in move_generator():
        assert move.self_boost is None or isinstance(move.self_boost, dict)


def test_self_destruct():
    flame_thrower = Move("flamethrower")
    self_destruct = Move("selfdestruct")

    assert self_destruct.self_destruct == "always"
    assert flame_thrower.self_destruct is None

    for move in move_generator():
        assert move.self_destruct is None or isinstance(move.self_destruct, str)


def test_self_switch():
    flame_thrower = Move("flamethrower")
    baton_pass = Move("batonpass")
    parting_shot = Move("partingshot")

    assert baton_pass.self_switch == "copyvolatile"
    assert flame_thrower.self_switch is False
    assert parting_shot.self_switch is True

    for move in move_generator():
        assert isinstance(move.self_switch, bool) or isinstance(move.self_switch, str)


def test_side_condition():
    flame_thrower = Move("flamethrower")
    quick_guard = Move("quickguard")

    assert quick_guard.side_condition == "quickguard"
    assert flame_thrower.side_condition is None

    for move in move_generator():
        assert isinstance(move.side_condition, str) or move.side_condition is None


def test_sleep_usable():
    flame_thrower = Move("flamethrower")
    sleep_talk = Move("sleeptalk")

    assert sleep_talk.sleep_usable is True
    assert flame_thrower.sleep_usable is False

    for move in move_generator():
        assert isinstance(move.sleep_usable, bool)


def test_slot_condition():
    flame_thrower = Move("flamethrower")
    healing_wish = Move("healingwish")

    assert healing_wish.slot_condition == "healingwish"
    assert flame_thrower.slot_condition is None

    for move in move_generator():
        assert isinstance(move.slot_condition, str) or move.slot_condition is None


def test_stalling_move():
    flame_thrower = Move("flamethrower")
    kings_shield = Move("kingsshield")

    assert kings_shield.stalling_move is True
    assert flame_thrower.stalling_move is False

    for move in move_generator():
        assert isinstance(move.stalling_move, bool)


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


def test_steals_boosts():
    flame_thrower = Move("flamethrower")
    spectral_thief = Move("spectralthief")

    assert spectral_thief.steals_boosts is True
    assert flame_thrower.steals_boosts is False

    for move in move_generator():
        assert isinstance(move.steals_boosts, bool)


def test_target():
    flame_thrower = Move("flamethrower")
    earthquake = Move("earthquake")

    assert earthquake.target == "allAdjacent"
    assert flame_thrower.target == "normal"

    for move in move_generator():
        assert isinstance(move.target, str)


def test_terrain():
    flame_thrower = Move("flamethrower")
    electric_terrain = Move("electricterrain")

    assert electric_terrain.terrain == Field.ELECTRIC_TERRAIN
    assert flame_thrower.terrain is None

    for move in move_generator():
        assert isinstance(move.terrain, Field) or move.terrain is None


def test_thaws_target():
    flame_thrower = Move("flamethrower")
    scald = Move("scald")

    assert scald.thaws_target is True
    assert flame_thrower.thaws_target is False

    for move in move_generator():
        assert isinstance(move.thaws_target, bool)


def test_type():
    flame_thrower = Move("flamethrower")
    scald = Move("scald")

    assert scald.type == PokemonType["WATER"]
    assert flame_thrower.type == PokemonType["FIRE"]

    for move in move_generator():
        assert isinstance(move.type, PokemonType)


def test_use_target_offensive():
    flame_thrower = Move("flamethrower")
    foul_play = Move("foulplay")

    assert foul_play.use_target_offensive is True
    assert flame_thrower.use_target_offensive is False

    for move in move_generator():
        assert isinstance(move.use_target_offensive, bool)


def test_volatile_status():
    flame_thrower = Move("flamethrower")
    heal_block = Move("healblock")

    assert heal_block.volatile_status == "healblock"
    assert flame_thrower.volatile_status is None

    for move in move_generator():
        assert isinstance(move.volatile_status, str) or move.volatile_status is None


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


def test_dynamax_move_with_boosts():
    move = Move("dracometeor")
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts == {"atk": -1}
    assert dynamaxed.damage == 0
    assert dynamaxed.weather is None
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost is None

    move = Move("tackle")
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts == {"spe": -1}
    assert dynamaxed.weather is None
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost is None


def test_dynamax_move_with_self_boosts():
    move = Move("fly")
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather is None
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost == {"spe": 1}

    move = Move("earthquake")
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather is None
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost == {"spd": 1}


def test_dynamax_move_with_terrain():
    move = Move("psychic")
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather is None
    assert dynamaxed.terrain == Field.PSYCHIC_TERRAIN
    assert dynamaxed.self_boost is None

    move = Move("thunder")
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather is None
    assert dynamaxed.terrain == Field.ELECTRIC_TERRAIN
    assert dynamaxed.self_boost is None


def test_dynamax_move_with_weather():
    move = Move("flamethrower")
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather == Weather.SUNNYDAY
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost is None

    move = Move("watergun")
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather == Weather.RAINDANCE
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost is None


def test_misc_dynamax_move_properties():
    move = Move("watergun")
    dynamaxed = move.dynamaxed

    assert dynamaxed.accuracy == 1
    assert dynamaxed.breaks_protect is False
    assert dynamaxed.crit_ratio == 0
    assert dynamaxed.defensive_category is MoveCategory.SPECIAL
    assert dynamaxed.expected_hits == 1
    assert dynamaxed.force_switch is False
    assert dynamaxed.heal == 0
    assert dynamaxed.is_protect_counter is False
    assert dynamaxed.is_protect_move is False
    assert dynamaxed.n_hit == (1, 1)
    assert dynamaxed.priority == 0
    assert dynamaxed.recoil == 0
    assert dynamaxed.status is None
    assert dynamaxed.type == PokemonType.WATER

    move = Move("closecombat")
    dynamaxed = move.dynamaxed
    assert dynamaxed.defensive_category is MoveCategory.PHYSICAL
    assert dynamaxed.type == PokemonType.FIGHTING


def test_dynamax_status_move_properties():
    move = Move("recover")
    dynamaxed = move.dynamaxed

    assert dynamaxed.accuracy == 1
    assert dynamaxed.breaks_protect is False
    assert dynamaxed.crit_ratio == 0
    assert dynamaxed.defensive_category is MoveCategory.STATUS
    assert dynamaxed.expected_hits == 1
    assert dynamaxed.force_switch is False
    assert dynamaxed.heal == 0
    assert dynamaxed.is_protect_counter is True
    assert dynamaxed.is_protect_move is True
    assert dynamaxed.n_hit == (1, 1)
    assert dynamaxed.priority == 0
    assert dynamaxed.recoil == 0
    assert dynamaxed.status is None
    assert dynamaxed.type == PokemonType.NORMAL

    assert dynamaxed.boosts is None
    assert dynamaxed.weather is None
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost is None

    assert dynamaxed.base_power == 0


def test_dynamax_moves_base_power():
    move_to_dynamax_power = {
        "doublekick": 70,
        "rocksmash": 75,
        "karatechop": 80,
        "forcepalm": 85,
        "vitalthrow": 90,
        "closecombat": 95,
        "focuspunch": 100,
        "firespin": 90,
        "ember": 100,
        "flamecharge": 110,
        "incinerate": 120,
        "flameburst": 130,
        "burnup": 140,
        "eruption": 150,
    }

    for move_name, bp in move_to_dynamax_power.items():
        print("Expecting", move_name, "to have", bp, "base power once dynamaxed")
        move = Move(move_name)
        dynamaxed = move.dynamaxed
        assert dynamaxed == move.dynamaxed == move._dynamaxed_move  # testing caching
        assert dynamaxed.base_power == bp


def test_should_be_stored():
    assert Move.should_be_stored("flamethrower")
    assert not Move.should_be_stored("aciddownpour")
    assert not Move.should_be_stored("maxooze")


def test_is_max_move():
    assert not Move.is_max_move("flamethrower")
    assert Move.is_max_move("gmaxwildfire")
    assert Move.is_max_move("gmaxcannonade")
    assert Move.is_max_move("maxooze")


def test_expected_hits():
    assert Move("flamethrower").expected_hits == 1
    assert (
        Move("triplekick").expected_hits == 5.23
    )  # TODO: double check interactions here
    assert Move("bulletseed").expected_hits == 3.166666666666667


def test_is_protect_move():
    assert not Move("flamethrower").is_protect_move
    assert not Move("flamethrower").is_side_protect_move
    assert Move("protect").is_protect_move
    assert not Move("protect").is_side_protect_move
    assert not Move("wideguard").is_protect_move
    assert Move("wideguard").is_side_protect_move


def test_hiddenpower_types():
    hidden_power_bug = Move("hiddenpowerbug")
    hidden_power_fire = Move("hiddenpowerfire")
    hidden_power_water = Move("hiddenpowerwater")

    assert hidden_power_bug.type == PokemonType.BUG
    assert hidden_power_fire.type == PokemonType.FIRE
    assert hidden_power_water.type == PokemonType.WATER


def test_deepcopy_move():
    move = Move("flamethrower")
    copy_move = copy.deepcopy(move)
    assert copy_move != move
    assert copy_move.id == move.id


def test_deepcopy_empty_move():
    move = EmptyMove("recharge")
    copy_move = copy.deepcopy(move)
    assert copy_move != move
    assert copy_move.id == move.id
    assert copy_move.base_power == 0
    assert copy_move.is_empty
