import copy
import itertools

from poke_env.battle import (
    Effect,
    Field,
    Move,
    MoveCategory,
    PokemonType,
    SideCondition,
    Status,
    Target,
    Weather,
)
from poke_env.data import GenData


def move_generator(gen=8):
    for move in GenData.from_gen(gen).moves:
        yield Move(move, gen=gen)
        yield Move("z" + move, gen=gen)


def test_accuracy():
    volt_thunderbolt = Move("10000000voltthunderbolt", gen=8)
    absorb = Move("absorb", gen=8)
    aeroblast = Move("aeroblast", gen=8)

    assert volt_thunderbolt.accuracy == 1
    assert absorb.accuracy == 1
    assert aeroblast.accuracy == 0.95

    for move in move_generator():
        assert isinstance(move.accuracy, float)
        assert 0 <= move.accuracy <= 1


def test_all_moves_instanciate():
    for move in move_generator():
        move_from_id = Move(move_id=move.id, gen=8)
        assert str(move) == str(move_from_id)


def test_boosts():
    sharpen = Move("sharpen", gen=8)
    flame_thrower = Move("flamethrower", gen=8)

    assert flame_thrower.boosts is None
    assert sharpen.boosts == {"atk": 1}

    for move in move_generator():
        assert move.boosts is None or isinstance(move.boosts, dict)


def test_can_z_move():
    flame_thrower = Move("flamethrower", gen=8)

    assert flame_thrower.can_z_move is True

    for move in move_generator():
        assert isinstance(move.can_z_move, bool)


def test_category():
    flame_thrower = Move("flamethrower", gen=8)
    close_combat = Move("closecombat", gen=8)
    protect = Move("protect", gen=8)

    assert flame_thrower.category == MoveCategory["SPECIAL"]
    assert close_combat.category == MoveCategory["PHYSICAL"]
    assert protect.category == MoveCategory["STATUS"]

    for move in move_generator():
        assert isinstance(move.category, MoveCategory)


def test_category_pre_gen4():
    for gen in range(1, 10):
        flame_thrower = Move("flamethrower", gen=gen)
        fire_punch = Move("firepunch", gen=gen)

        hyper_beam = Move("hyperbeam", gen=gen)
        headbutt = Move("headbutt", gen=gen)

        assert flame_thrower.category == MoveCategory["SPECIAL"]

        if gen <= 3:
            assert fire_punch.category == MoveCategory["SPECIAL"]
        else:
            assert fire_punch.category == MoveCategory["PHYSICAL"]

        assert headbutt.category == MoveCategory["PHYSICAL"]

        if gen <= 3:
            assert hyper_beam.category == MoveCategory["PHYSICAL"]
        else:
            assert hyper_beam.category == MoveCategory["SPECIAL"]


def test_crit_ratio():
    aeroblast = Move("aeroblast", gen=8)
    flame_thrower = Move("flamethrower", gen=8)

    assert aeroblast.crit_ratio == 2
    assert flame_thrower.crit_ratio == 0

    for move in move_generator():
        assert isinstance(move.crit_ratio, int)


def test_current_pp():
    for move in move_generator():
        assert isinstance(move.current_pp, int)
        assert move.current_pp == move.max_pp


def test_damage():
    flame_thrower = Move("flamethrower", gen=8)
    night_shade = Move("nightshade", gen=8)
    dragon_rage = Move("dragonrage", gen=8)

    assert flame_thrower.damage == 0
    assert night_shade.damage == "level"
    assert dragon_rage.damage == 40

    for move in move_generator():
        assert isinstance(move.damage, int) or isinstance(move.damage, str)


def test_defensive_category():
    psyshock = Move("psyshock", gen=8)
    close_combat = Move("closecombat", gen=8)
    flame_thrower = Move("flamethrower", gen=8)

    assert psyshock.defensive_category == MoveCategory["PHYSICAL"]
    assert close_combat.defensive_category == MoveCategory["PHYSICAL"]
    assert flame_thrower.defensive_category == MoveCategory["SPECIAL"]

    for move in move_generator():
        assert isinstance(move.defensive_category, MoveCategory)


def test_drain():
    draining_kiss = Move("drainingkiss", gen=8)
    flame_thrower = Move("flamethrower", gen=8)

    assert draining_kiss.drain == 0.75
    assert flame_thrower.drain == 0

    for move in move_generator():
        assert isinstance(move.drain, float)
        assert 0 <= move.drain <= 1


def test_flags():
    flame_thrower = Move("flamethrower", gen=8)
    sludge_bomb = Move("sludgebomb", gen=8)

    assert flame_thrower.flags == {"metronome", "protect", "mirror"}
    assert sludge_bomb.flags == {"bullet", "metronome", "protect", "mirror"}
    for move in move_generator():
        assert isinstance(move.flags, set)


def test_heal():
    roost = Move("roost", gen=8)
    flame_thrower = Move("flamethrower", gen=8)

    assert roost.heal == 0.5
    assert flame_thrower.heal == 0

    for move in move_generator():
        assert isinstance(move.heal, float)
        assert 0 <= move.heal <= 1


def test_ignore_ability():
    flame_thrower = Move("flamethrower", gen=8)
    menacing_moonraze_maelstrom = Move("menacingmoonrazemaelstrom", gen=8)

    assert menacing_moonraze_maelstrom.ignore_ability is True
    assert flame_thrower.ignore_ability is False

    for move in move_generator():
        assert isinstance(move.ignore_ability, bool)


def test_ignore_defensive():
    flame_thrower = Move("flamethrower", gen=8)
    chipaway = Move("chipaway", gen=8)

    assert chipaway.ignore_defensive is True
    assert flame_thrower.ignore_defensive is False

    for move in move_generator():
        assert isinstance(move.ignore_defensive, bool)


def test_ignore_evasion():
    flame_thrower = Move("flamethrower", gen=8)
    chipaway = Move("chipaway", gen=8)

    assert chipaway.ignore_evasion is True
    assert flame_thrower.ignore_evasion is False

    for move in move_generator():
        assert isinstance(move.ignore_evasion, bool)


def test_ignore_immunity():
    thousand_arrows = Move("thousandarrows", gen=8)
    thunder_wave = Move("thunderwave", gen=8)
    bide = Move("bide", gen=8)
    flame_thrower = Move("flamethrower", gen=8)

    assert thousand_arrows.ignore_immunity == {PokemonType["GROUND"]}
    assert thunder_wave.ignore_immunity is False
    assert bide.ignore_immunity is True
    assert flame_thrower.ignore_immunity is False

    for move in move_generator():
        assert type(move.ignore_immunity) in [bool, set]


def test_is_z():
    flame_thrower = Move("flamethrower", gen=8)
    clangorous_soul_blaze = Move("clangoroussoulblaze", gen=8)

    assert clangorous_soul_blaze.is_z is True
    assert flame_thrower.is_z is False

    for move in move_generator():
        assert isinstance(move.is_z, bool)


def test_force_switch():
    flame_thrower = Move("flamethrower", gen=8)
    dragon_tail = Move("dragontail", gen=8)

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
    furys_wipes = Move("furyswipes", gen=8)
    flame_thrower = Move("flamethrower", gen=8)
    gear_grind = Move("geargrind", gen=8)

    assert furys_wipes.n_hit == (2, 5)
    assert flame_thrower.n_hit == (1, 1)
    assert gear_grind.n_hit == (2, 2)

    for move in move_generator():
        assert isinstance(move.n_hit, tuple) and len(move.n_hit) == 2


def test_no_pp_boosts():
    flame_thrower = Move("flamethrower", gen=8)
    sketch = Move("sketch", gen=8)

    assert sketch.no_pp_boosts is True
    assert flame_thrower.no_pp_boosts is False

    for move in move_generator():
        assert isinstance(move.no_pp_boosts, bool)


def test_non_ghost_target():
    flame_thrower = Move("flamethrower", gen=8)
    curse = Move("curse", gen=8)

    assert curse.non_ghost_target is True
    assert flame_thrower.non_ghost_target is False

    for move in move_generator():
        assert isinstance(move.non_ghost_target, bool)


def test_priority():
    flame_thrower = Move("flamethrower", gen=8)
    trick_room = Move("trickroom", gen=8)
    fake_out = Move("fakeout", gen=8)

    assert flame_thrower.priority == 0
    assert trick_room.priority == -7
    assert fake_out.priority == 3

    for move in move_generator():
        assert isinstance(move.priority, int)


def test_pseudo_weather():
    flame_thrower = Move("flamethrower", gen=8)
    fairy_lock = Move("fairylock", gen=8)

    assert flame_thrower.pseudo_weather is None
    assert fairy_lock.pseudo_weather == "fairylock"

    for move in move_generator():
        assert isinstance(move.pseudo_weather, str) or move.pseudo_weather is None


def test_recoil():
    flare_blitz = Move("flareblitz", gen=8)
    flame_thrower = Move("flamethrower", gen=8)

    assert flare_blitz.recoil == 0.33
    assert flame_thrower.recoil == 0

    for move in move_generator():
        assert isinstance(move.recoil, float)
        assert 0 <= move.recoil <= 1


def test_secondary():
    fake_out = Move("fakeout", gen=8)
    flame_thrower = Move("flamethrower", gen=8)
    acid_armor = Move("acidarmor", gen=8)

    assert fake_out.secondary == [{"chance": 100, "volatileStatus": "flinch"}]
    assert fake_out.volatile_status == Effect.FLINCH
    assert flame_thrower.secondary == [{"chance": 10, "status": "brn"}]
    assert acid_armor.secondary == []

    for move in move_generator():
        assert isinstance(move.secondary, list)
        for secondary in move.secondary:
            assert isinstance(secondary, dict)


def test_self_boosts():
    clanging_scales = Move("clangingscales", gen=8)
    close_combat = Move("closecombat", gen=8)
    fire_blast = Move("fireblast", gen=8)

    assert fire_blast.self_boost is None
    assert close_combat.self_boost == {"def": -1, "spd": -1}
    assert clanging_scales.self_boost == {"def": -1}

    for move in move_generator():
        assert move.self_boost is None or isinstance(move.self_boost, dict)


def test_self_destruct():
    flame_thrower = Move("flamethrower", gen=8)
    self_destruct = Move("selfdestruct", gen=8)

    assert self_destruct.self_destruct == "always"
    assert flame_thrower.self_destruct is None

    for move in move_generator():
        assert move.self_destruct is None or isinstance(move.self_destruct, str)


def test_self_switch():
    flame_thrower = Move("flamethrower", gen=8)
    baton_pass = Move("batonpass", gen=8)
    parting_shot = Move("partingshot", gen=8)

    assert baton_pass.self_switch == "copyvolatile"
    assert flame_thrower.self_switch is False
    assert parting_shot.self_switch is True

    for move in move_generator():
        assert isinstance(move.self_switch, bool) or isinstance(move.self_switch, str)


def test_side_condition():
    flame_thrower = Move("flamethrower", gen=8)
    quick_guard = Move("quickguard", gen=8)

    assert quick_guard.side_condition == SideCondition.QUICK_GUARD
    assert flame_thrower.side_condition is None

    assert SideCondition.from_data("i dont know") == SideCondition.UNKNOWN
    assert SideCondition.from_showdown_message("i dont know") == SideCondition.UNKNOWN

    # Make sure we know every move that has a SideCondition is one we know
    side_conditions = set()
    for move in itertools.chain(move_generator(8), move_generator(9)):
        if move.side_condition:
            assert move.side_condition != SideCondition.UNKNOWN
            side_conditions.add(move.side_condition)

    # SideConditions that don't exist in moves data
    to_exclude = set(
        [
            SideCondition.FIRE_PLEDGE,
            SideCondition.WATER_PLEDGE,
            SideCondition.GRASS_PLEDGE,
            SideCondition.UNKNOWN,
            SideCondition.G_MAX_WILDFIRE,
            SideCondition.G_MAX_VOLCALITH,
            SideCondition.G_MAX_VINE_LASH,
            SideCondition.G_MAX_STEELSURGE,
            SideCondition.G_MAX_CANNONADE,
        ]
    )

    # Make sure we don't have any SideConditions that don't exist in moves data
    assert side_conditions == set(
        list(filter(lambda x: x not in to_exclude, SideCondition))
    )


def test_sleep_usable():
    flame_thrower = Move("flamethrower", gen=8)
    sleep_talk = Move("sleeptalk", gen=8)

    assert sleep_talk.sleep_usable is True
    assert flame_thrower.sleep_usable is False

    for move in move_generator():
        assert isinstance(move.sleep_usable, bool)


def test_slot_condition():
    flame_thrower = Move("flamethrower", gen=8)
    healing_wish = Move("healingwish", gen=8)

    assert healing_wish.slot_condition == "healingwish"
    assert flame_thrower.slot_condition is None

    for move in move_generator():
        assert isinstance(move.slot_condition, str) or move.slot_condition is None


def test_stalling_move():
    flame_thrower = Move("flamethrower", gen=8)
    kings_shield = Move("kingsshield", gen=8)

    assert kings_shield.stalling_move is True
    assert flame_thrower.stalling_move is False

    for move in move_generator():
        assert isinstance(move.stalling_move, bool)


def test_status():
    dark_void = Move("darkvoid", gen=8)
    sleep_powder = Move("sleeppowder", gen=8)
    flame_thrower = Move("flamethrower", gen=8)
    thunder_wave = Move("thunderwave", gen=8)

    assert dark_void.status == Status["SLP"]
    assert sleep_powder.status == Status["SLP"]
    assert thunder_wave.status == Status["PAR"]
    assert flame_thrower.status is None

    for move in move_generator():
        assert move.status is None or isinstance(move.status, Status)


def test_steals_boosts():
    flame_thrower = Move("flamethrower", gen=8)
    spectral_thief = Move("spectralthief", gen=8)

    assert spectral_thief.steals_boosts is True
    assert flame_thrower.steals_boosts is False

    for move in move_generator():
        assert isinstance(move.steals_boosts, bool)


def test_target():
    flame_thrower = Move("flamethrower", gen=8)
    earthquake = Move("earthquake", gen=8)

    assert earthquake.target == Target.ALL_ADJACENT
    assert flame_thrower.target == Target.NORMAL

    for move in move_generator():
        assert isinstance(move.target, Target)


def test_terrain():
    flame_thrower = Move("flamethrower", gen=8)
    electric_terrain = Move("electricterrain", gen=8)

    assert electric_terrain.terrain == Field.ELECTRIC_TERRAIN
    assert flame_thrower.terrain is None

    for move in move_generator():
        assert isinstance(move.terrain, Field) or move.terrain is None


def test_thaws_target():
    flame_thrower = Move("flamethrower", gen=8)
    scald = Move("scald", gen=8)

    assert scald.thaws_target is True
    assert flame_thrower.thaws_target is False

    for move in move_generator():
        assert isinstance(move.thaws_target, bool)


def test_type():
    flame_thrower = Move("flamethrower", gen=8)
    scald = Move("scald", gen=8)

    assert scald.type == PokemonType["WATER"]
    assert flame_thrower.type == PokemonType["FIRE"]

    for move in move_generator():
        assert isinstance(move.type, PokemonType)


def test_use_target_offensive():
    flame_thrower = Move("flamethrower", gen=8)
    foul_play = Move("foulplay", gen=8)

    assert foul_play.use_target_offensive is True
    assert flame_thrower.use_target_offensive is False

    for move in move_generator():
        assert isinstance(move.use_target_offensive, bool)


def test_volatile_status():
    fake_out = Move("fakeout", gen=8)
    flame_thrower = Move("flamethrower", gen=8)
    heal_block = Move("healblock", gen=8)

    assert fake_out.volatile_status == Effect.FLINCH
    assert heal_block.volatile_status == Effect.HEAL_BLOCK
    assert flame_thrower.volatile_status is None

    for move in move_generator():
        assert isinstance(move.volatile_status, Effect) or move.volatile_status is None


def test_weather():
    flame_thrower = Move("flamethrower", gen=8)
    sand_storm = Move("sandstorm", gen=8)

    assert flame_thrower.weather is None
    assert sand_storm.weather is Weather["SANDSTORM"]


def test_z_move_boost():
    misty_terrain = Move("mistyterrain", gen=8)
    flame_thrower = Move("flamethrower", gen=8)
    mist = Move("mist", gen=8)

    assert misty_terrain.z_move_boost == {"spd": 1}
    assert flame_thrower.z_move_boost is None
    assert mist.z_move_boost is None

    for move in move_generator():
        assert move.z_move_boost is None or isinstance(move.z_move_boost, dict)


def test_z_move_effect():
    flare_blitz = Move("flareblitz", gen=8)
    flame_thrower = Move("flamethrower", gen=8)
    mist = Move("mist", gen=8)

    assert flare_blitz.z_move_effect is None
    assert flame_thrower.z_move_effect is None
    assert mist.z_move_effect == "heal"

    for move in move_generator():
        assert move.z_move_effect is None or isinstance(move.z_move_effect, str)


def test_z_move_power():
    flare_blitz = Move("flareblitz", gen=8)
    flame_thrower = Move("flamethrower", gen=8)
    mist = Move("mist", gen=8)

    assert flare_blitz.z_move_power == 190
    assert flame_thrower.z_move_power == 175
    assert mist.z_move_power == 0

    for move in move_generator():
        assert isinstance(move.z_move_power, int)


def test_dynamax_move_with_boosts():
    move = Move("dracometeor", gen=8)
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts == {"atk": -1}
    assert dynamaxed.damage == 0
    assert dynamaxed.weather is None
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost is None

    move = Move("tackle", gen=8)
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts == {"spe": -1}
    assert dynamaxed.weather is None
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost is None


def test_dynamax_move_with_self_boosts():
    move = Move("fly", gen=8)
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather is None
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost == {"spe": 1}

    move = Move("earthquake", gen=8)
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather is None
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost == {"spd": 1}


def test_dynamax_move_with_terrain():
    move = Move("psychic", gen=8)
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather is None
    assert dynamaxed.terrain == Field.PSYCHIC_TERRAIN
    assert dynamaxed.self_boost is None

    move = Move("thunder", gen=8)
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather is None
    assert dynamaxed.terrain == Field.ELECTRIC_TERRAIN
    assert dynamaxed.self_boost is None


def test_dynamax_move_with_weather():
    move = Move("flamethrower", gen=8)
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather == Weather.SUNNYDAY
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost is None

    move = Move("watergun", gen=8)
    dynamaxed = move.dynamaxed

    assert dynamaxed.boosts is None
    assert dynamaxed.weather == Weather.RAINDANCE
    assert dynamaxed.terrain is None
    assert dynamaxed.self_boost is None


def test_misc_dynamax_move_properties():
    move = Move("watergun", gen=8)
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

    move = Move("closecombat", gen=8)
    dynamaxed = move.dynamaxed
    assert dynamaxed.defensive_category is MoveCategory.PHYSICAL
    assert dynamaxed.type == PokemonType.FIGHTING


def test_dynamax_status_move_properties():
    move = Move("recover", gen=8)
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
        move = Move(move_name, gen=8)
        dynamaxed = move.dynamaxed
        assert dynamaxed == move.dynamaxed == move._dynamaxed_move  # testing caching
        assert dynamaxed.base_power == bp


def test_should_be_stored():
    assert Move.should_be_stored("flamethrower", gen=8)
    assert not Move.should_be_stored("aciddownpour", gen=8)
    assert not Move.should_be_stored("maxooze", gen=8)


def test_is_max_move():
    assert not Move.is_max_move("flamethrower", gen=8)
    assert Move.is_max_move("gmaxwildfire", gen=8)
    assert Move.is_max_move("gmaxcannonade", gen=8)
    assert Move.is_max_move("maxooze", gen=8)


def test_expected_hits():
    assert Move("flamethrower", gen=8).expected_hits == 1
    assert (
        Move("triplekick", gen=8).expected_hits == 5.23
    )  # TODO: double check interactions here
    assert Move("bulletseed", gen=8).expected_hits == 3.166666666666667


def test_is_protect_move():
    assert not Move("flamethrower", gen=8).is_protect_move
    assert not Move("flamethrower", gen=8).is_side_protect_move
    assert Move("protect", gen=8).is_protect_move
    assert not Move("protect", gen=8).is_side_protect_move
    assert not Move("wideguard", gen=8).is_protect_move
    assert Move("wideguard", gen=8).is_side_protect_move


def test_hiddenpower_types():
    hidden_power_bug = Move("hiddenpowerbug", gen=8)
    hidden_power_fire = Move("hiddenpowerfire", gen=8)
    hidden_power_water = Move("hiddenpowerwater", gen=8)

    assert hidden_power_bug.type == PokemonType.BUG
    assert hidden_power_fire.type == PokemonType.FIRE
    assert hidden_power_water.type == PokemonType.WATER


def test_deepcopy_move():
    move = Move("flamethrower", gen=8)
    copy_move = copy.deepcopy(move)
    assert copy_move != move
    assert copy_move.id == move.id


def test_three_question_marks_move():
    for gen in range(2, 5):
        move = Move("curse", gen=gen)
        assert move.type == PokemonType.THREE_QUESTION_MARKS

    for gen in range(5, 9):
        move = Move("curse", gen=gen)
        assert move.type == PokemonType.GHOST
