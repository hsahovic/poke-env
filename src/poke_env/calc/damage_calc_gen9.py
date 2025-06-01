"""This module defines a gen9 damage calculator"""

import math
from typing import Dict, List, Optional, Union

from poke_env.battle import (
    Battle,
    DoubleBattle,
    Effect,
    Field,
    Move,
    MoveCategory,
    Pokemon,
    PokemonGender,
    PokemonType,
    SideCondition,
    Status,
    Target,
    Weather,
)
from poke_env.data import GenData


# Source: https://github.com/smogon/damage-calc/blob/master/calc/src/mechanics/gen789.ts#L52
# NOTE: dont deal with multihits (just take average)
# NOTE: don't deal with shell side arm, naturalgift, technoblast, pursuit, multiattack, aurawheel, fling
# NOTE: don't deal with xerneas or zygarde or yveltal auras, or battlebond
# NOTE: dont deal with metronome (the item) or stellar because we dont keep a log of historical move usage
# NOTE: I ignore dynamax, mega, primal,battlebond and parental bond (not legal in gen9)
# NOTE: knockoff damage isnt realllllly right cuz I dont look at pokemon/item pairs, just items
def calculate_damage(
    attacker_identifier: str,
    defender_identifier: str,
    move: Move,
    battle: Union[Battle, DoubleBattle],
    is_critical: bool = False,
):
    """Return the possible damage range for a move.

    :param attacker_identifier: Identifier of the attacking Pokémon.
    :type attacker_identifier: str
    :param defender_identifier: Identifier of the defending Pokémon.
    :type defender_identifier: str
    :param move: Move being used.
    :type move: Move
    :param battle: Current battle object containing both Pokémon.
    :type battle: Battle or DoubleBattle
    :param is_critical: Whether to compute damage for a critical hit.
    :type is_critical: bool
    :return: Tuple of minimum and maximum damage rolls.
    :rtype: Tuple[int, int]

    Notes that several edge cases are ignored and behaviour may deviate from
    the official damage calculator.
    """
    attacker = battle.get_pokemon(attacker_identifier)
    defender = battle.get_pokemon(defender_identifier)

    assert battle.player_role is not None and battle.opponent_role is not None
    assert all(
        map(
            lambda x: isinstance(x, int) or isinstance(x, float),
            attacker.stats.values(),
        )
    ), "attacker stats not defined"
    assert all(
        map(
            lambda x: isinstance(x, int) or isinstance(x, float),
            defender.stats.values(),
        )
    ), "defender stats not defined"

    move_category = move.category
    flags = {x: 1 for x in move.entry.get("flags", {})}

    # NOTE: I don't deal with shell side arm
    if (
        move.id in ["photongeyser", "terablast"]
        and attacker.stats["atk"]
        and attacker.stats["spa"]
    ):
        move_category = (
            MoveCategory.PHYSICAL
            if attacker.stats["atk"] * BOOST_MULTIPLIERS[attacker.boosts["atk"]]
            > attacker.stats["spa"] * BOOST_MULTIPLIERS[attacker.boosts["spa"]]
            else MoveCategory.SPECIAL
        )

    if move_category == MoveCategory.STATUS and not move.id == "naturepower":
        return 0, 0

    if flags.get("punch", 0) and attacker.item == "punchingglove":
        flags["contact"] = 0

    move_breaks_protect = move.breaks_protect or (
        attacker.ability == "unseenfist" and flags.get("contact", 0) == 1
    )

    if (
        any(map(lambda x: x in PROTECT_EFFECTS, defender.effects))
        and not move_breaks_protect
    ):
        return 0, 0

    if move.id == "painsplit":
        attacker_hp_stat = attacker.stats.get("hp", None)
        defender_hp_stat = defender.stats.get("hp", None)
        if attacker_hp_stat is not None and defender_hp_stat is not None:
            attacker_hp = (
                math.floor(attacker_hp_stat * attacker.current_hp_fraction)
                if attacker_hp_stat
                else 0
            )
            defender_hp = (
                math.floor(defender_hp_stat * defender.current_hp_fraction)
                if defender_hp_stat
                else 0
            )
            damage = max(0, defender_hp - math.floor((attacker_hp + defender_hp) / 2))
            return damage, damage
        else:
            return 0, 0

    defender_ability = defender.ability
    attacker_ability = attacker.ability
    if move.id in MOVE_IGNORES_ABILITY or (
        attacker.ability in ATTACKER_IGNORES_ABILITY
        and not defender.item == "abilityshield"
    ):
        defender_ability = ""

    if any(
        map(lambda x: x and x.ability == "neutralizinggas", battle.all_active_pokemons)
    ):
        if (
            defender.ability not in ABILITY_IGNORES_NEUTRALIZING_GAS
            or not defender.item == "abilityshield"
        ):
            defender_ability = ""
        elif (
            attacker.ability not in ABILITY_IGNORES_NEUTRALIZING_GAS
            or not attacker.item == "abilityshield"
        ):
            attacker_ability = ""

    if defender_ability in ["battlearmor", "shellarmor"]:
        is_critical = False
    elif attacker_ability == "merciless" and defender.status in [
        Status.PSN,
        Status.TOX,
    ]:
        is_critical = True

    defender_weight = defender.weight
    if defender_ability == "lightmetal":
        defender_weight *= 0.5
    elif defender_ability == "heavymetal":
        defender_weight *= 2
    if defender.item == "floatstone":
        defender_weight *= 0.5

    # NOTE: no support for technoblast or multiattack or naturalgift, or aurawheel
    move_type: Optional[PokemonType] = move.type
    move_target: Target = move.target if move.target is not None else Target.SELF
    if move.id == "weatherball":
        if Weather.SUNNYDAY in battle.weather and attacker.item != "utilityumbrella":
            move_type = PokemonType.FIRE
        elif Weather.RAINDANCE in battle.weather and attacker.item != "utilityumbrella":
            move_type = PokemonType.WATER
        elif Weather.SANDSTORM in battle.weather:
            move_type = PokemonType.ROCK
        elif Weather.HAIL in battle.weather or Weather.SNOW in battle.weather:
            move_type = PokemonType.ICE
        else:
            move_type = PokemonType.NORMAL
    elif move.id == "judgment" and attacker.item and attacker.item.endswith("plate"):
        move_type = get_item_boost_type(attacker.item)
    elif move.id == "naturepower" or (
        move.id == "terrainpulse" and battle.is_grounded(attacker)
    ):
        if Field.ELECTRIC_TERRAIN in battle.fields:
            move_type = PokemonType.ELECTRIC
        elif Field.GRASSY_TERRAIN in battle.fields:
            move_type = PokemonType.GRASS
        elif Field.MISTY_TERRAIN in battle.fields:
            move_type = PokemonType.FAIRY
        elif Field.PSYCHIC_TERRAIN in battle.fields:
            move_type = PokemonType.PSYCHIC
        else:
            move_type = PokemonType.NORMAL
    elif move.id == "revelationdance":
        move_type = attacker.type_1
    elif move.id == "ragingbull":
        if attacker.species == "taurospaldeacombat":
            move_type = PokemonType.FIGHTING
        elif attacker.species == "taurospaldeablaze":
            move_type = PokemonType.FIRE
        elif attacker.species == "taurospaldeaaqua":
            move_type = PokemonType.WATER

        flags["ignorescreens"] = 1
    elif move.id == "ivycudgel":
        if attacker.species == "ogerponcornerstone":
            move_type = PokemonType.ROCK
        elif attacker.species == "ogerponhearthflame":
            move_type = PokemonType.FIRE
        elif attacker.species == "ogerponwellspring":
            move_type = PokemonType.WATER
    elif move.id == "terastarstorm" and attacker.species == "terapagosstellar":
        move_target = Target.ALL_ADJACENT_FOES
        move_type = PokemonType.STELLAR
    elif move.id in ["brickbreak", "psychicfangs"]:
        flags["ignorescreens"] = 1
    # NOTE: had to add this; not present in showdown file
    elif move.id == "expandingforce" and Field.PSYCHIC_TERRAIN in battle.fields:
        move_target = Target.ALL_ADJACENT_FOES

    has_ate_ability_type_change = False  # measures whether the move type has changed by an -ate ability (eg pixilate)
    no_type_change = move.id in {
        "revelationdance",
        "judgment",
        "naturepower",
        "technoblast",
        "multiattack",
        "naturalgift",
        "weatherball",
        "terrainpulse",
        "struggle",
    } or (move.id == "terablast" and attacker.is_terastallized)

    if not no_type_change:
        if attacker_ability == "aerilate" and move_type == PokemonType.NORMAL:
            move_type = PokemonType.FLYING
            has_ate_ability_type_change = True
        elif attacker_ability == "galvanize" and move_type == PokemonType.NORMAL:
            move_type = PokemonType.ELECTRIC
            has_ate_ability_type_change = True
        elif attacker_ability == "liquidvoice" and flags.get("sound", 0) == 1:
            move_type = PokemonType.WATER
        elif attacker_ability == "pixilate" and move_type == PokemonType.NORMAL:
            move_type = PokemonType.FAIRY
            has_ate_ability_type_change = True
        elif attacker_ability == "refrigerate" and move_type == PokemonType.NORMAL:
            move_type = PokemonType.ICE
            has_ate_ability_type_change = True
        elif attacker_ability == "normalize":
            move_type = PokemonType.NORMAL
            has_ate_ability_type_change = True

    if move.id == "terablast" and attacker.is_terastallized:
        move_type = attacker.type_1

    move_priority = move.priority
    if (attacker_ability == "triage" and "heal" in flags) or (
        attacker_ability == "galewings"
        and move_type == PokemonType.FLYING
        and attacker.current_hp_fraction == 100
    ):
        move_priority = 1

    first_type_effectiveness = get_move_effectiveness(
        move,
        move_type or move.type,
        defender.type_1,
        attacker_ability in ["scrappy", "mindseye"],
        Field.GRAVITY in battle.fields,
        defender.item == "ringtarget",
    )
    second_type_effectiveness = (
        1
        if len(defender.types) == 1
        else get_move_effectiveness(
            move,
            move_type or move.type,
            defender.type_2,  # type: ignore
            attacker_ability in ["scrappy", "mindseye"],
            Field.GRAVITY in battle.fields,
            defender.item == "ringtarget",
        )
    )

    type_effectiveness = first_type_effectiveness * second_type_effectiveness

    if (
        type_effectiveness == 0
        and move_type == PokemonType.GROUND
        and defender.item == "ironball"
    ):
        type_effectiveness = 1

    if type_effectiveness == 0 and move.id == "thousandarrows":
        type_effectiveness = 1

    if type_effectiveness == 0:
        return 0, 0

    if move.id == "skydrop" and (
        PokemonType.FLYING in defender.types
        or defender_weight >= 200
        or Field.GRAVITY in battle.fields
    ):
        return 0, 0
    elif move.id == "synchronoise" and not (
        attacker.type_1 in defender.types or attacker.type_2 in defender.types
    ):
        return 0, 0
    elif move.id == "dreameater" and not (
        defender.status == Status.SLP or defender_ability == "comatose"
    ):
        return 0, 0
    elif move.id == "steelroller" and not any(
        map(lambda x: x.is_terrain, battle.fields)
    ):
        return 0, 0
    elif move.id == "poltergeist" and not defender.item:
        return 0, 0

    if move_type == PokemonType.STELLAR:
        type_effectiveness = 2 if defender.is_terastallized else 1

    if defender_ability == "terashell" and defender.current_hp_fraction == 100:
        type_effectiveness = 0.5

    if isinstance(battle, DoubleBattle):
        defender_identifier = defender.identifier(
            (
                battle.player_role
                if defender in battle.active_pokemon
                else battle.opponent_role
            ),
        )
    else:
        defender_identifier = defender.identifier(
            battle.player_role
            if defender == battle.active_pokemon
            else battle.opponent_role
        )

    if defender_ability == "wonderguard" and type_effectiveness <= 1:
        return 0, 0
    elif move_type == PokemonType.GRASS and defender_ability == "sapsipper":
        return 0, 0
    elif move_type == PokemonType.FIRE and defender_ability in [
        "flashfire",
        "wellbakedbody",
    ]:
        return 0, 0
    elif move_type == PokemonType.WATER and defender_ability in [
        "dryskin",
        "stormdrain",
        "waterabsorb",
    ]:
        return 0, 0
    elif move_type == PokemonType.ELECTRIC and defender_ability in [
        "lightningrod",
        "motordrive",
        "voltabsorb",
    ]:
        return 0, 0
    elif (
        move_type == PokemonType.GROUND
        and Field.GRAVITY not in battle.fields
        and not move.id == "thousandarrows"
        and not defender.item == "ironball"
        and defender.ability == "levitate"
    ):
        return 0, 0
    elif flags.get("bullet", 0) == 1 and defender_ability == "bulletproof":
        return 0, 0
    elif (
        flags.get("sound", 0) == 1
        and not move.id == "clangoroussoul"
        and defender_ability == "soundproof"
    ):
        return 0, 0
    elif move.priority > 0 and defender_ability in [
        "queenlymajesty",
        "dazzling",
        "armortail",
    ]:
        return 0, 0
    elif move_type == PokemonType.GROUND and defender_ability == "eartheater":
        return 0, 0
    elif flags.get("wind", 0) == 1 and defender_ability == "windrider":
        return 0, 0
    elif (
        move_type == PokemonType.GROUND
        and move.id != "thousandarrows"
        and Field.GRAVITY not in battle.fields
        and defender.item == "airballoon"
    ):
        return 0, 0
    elif (
        move_priority > 0
        and Field.PSYCHIC_TERRAIN in battle.fields
        and battle.is_grounded(defender)
    ):
        return 0, 0

    if move.id in ["seismictoss", "nightshade"]:
        return attacker.level, attacker.level
    elif move.id == "dragonrage":
        return 40, 40
    elif move.id == "sonicboom":
        return 20, 20

    # NOTE: this will be wrong if we use just Showdown ingested
    if move.id == "finalgambit":
        hp_stat = attacker.stats.get("hp", None)
        damage = math.floor(hp_stat * attacker.current_hp_fraction) if hp_stat else 0
        return damage, damage

    base_power = calculate_base_power(
        attacker_identifier,
        defender_identifier,
        move,
        battle,
        has_ate_ability_type_change,
    )

    # NOTE: I don't want to deal with multihit complexity so I calculate the average damage expected
    # This makes damage calc inaccurate for tripleaxel
    if move.n_hit != (1, 1):
        base_power = base_power * ((move.n_hit[0] + move.n_hit[1]) / 2)

    if base_power == 0:
        return 0, 0

    attack = calculate_attack(
        attacker_identifier, defender_identifier, move, battle, is_critical
    )
    defense = calculate_defense(
        attacker_identifier, defender_identifier, move, battle, is_critical
    )

    base_damage = calculate_base_damage(
        attacker_identifier,
        defender_identifier,
        base_power,
        attack,
        defense,
        move,
        move_type,
        move_target,
        battle,
        is_critical,
    )

    # the random factor is applied between the crit mod and the stab mod, so don't apply anything
    # below this until we're inside the loop
    pre_stellar_stab_mod = get_stab_mod(attacker, move, move_type)
    stab_mod = get_stellar_stab_mod(attacker, move, pre_stellar_stab_mod)

    apply_burn = (
        attacker.status == Status.BRN
        and move_category == MoveCategory.PHYSICAL
        and not attacker_ability == "guts"
        and not move.id == "facade"
    )

    final_mods = calculate_final_mods(
        attacker_identifier,
        defender_identifier,
        move,
        battle,
        type_effectiveness,
        flags,
        is_critical,
    )

    final_mod = chain_mods(final_mods, 41, 131072)

    return (
        get_final_damage(
            base_damage, 0, type_effectiveness, apply_burn, stab_mod, final_mod
        ),
        get_final_damage(
            base_damage, 15, type_effectiveness, apply_burn, stab_mod, final_mod
        ),
    )


# NOTE: doesn't calculate pursuit or fling or naturalgift or battlebond
def calculate_base_power(
    attacker_identifier: str,
    defender_identifier: str,
    move: Move,
    battle: Union[Battle, DoubleBattle],
    has_ate_ability_type_change: bool,
):
    assert battle.player_role is not None and battle.opponent_role is not None
    attacker = battle.get_pokemon(attacker_identifier)
    defender = battle.get_pokemon(defender_identifier)

    attacker_spe = (attacker.stats["spe"] or 0) * (
        1.5 if attacker.item == "choicescarf" else 1
    )
    defender_spe = (defender.stats["spe"] or 0) * (
        1.5 if defender.item == "choicescarf" else 1
    )
    attacker_first = attacker_spe > defender_spe

    if isinstance(battle, DoubleBattle):
        attacker_identifier = attacker.identifier(
            (
                battle.player_role
                if attacker in battle.active_pokemon
                else battle.opponent_role
            ),
        )
        defender_identifier = defender.identifier(
            (
                battle.player_role
                if defender in battle.active_pokemon
                else battle.opponent_role
            ),
        )
    else:
        attacker_identifier = attacker.identifier(
            battle.player_role
            if attacker == battle.active_pokemon
            else battle.opponent_role
        )
        defender_identifier = defender.identifier(
            battle.player_role
            if defender == battle.active_pokemon
            else battle.opponent_role
        )

    abilities_suppressed = any(
        map(lambda x: x and x.ability == "neutralizinggas", battle.all_active_pokemons)
    )

    base_power = move.base_power * 1.0

    defender_ability = defender.ability
    if move.id in MOVE_IGNORES_ABILITY or (
        attacker.ability in ATTACKER_IGNORES_ABILITY
        and not defender.item == "abilityshield"
    ):
        defender_ability = ""

    defender_weight = defender.weight
    if defender_ability == "lightmetal" and not abilities_suppressed:
        defender_weight *= 0.5
    elif defender_ability == "heavymetal" and not abilities_suppressed:
        defender_weight *= 2
    if defender.item == "floatstone":
        defender_weight *= 0.5

    attacker_weight = attacker.weight
    if attacker.ability == "lightmetal" and not abilities_suppressed:
        defender_weight *= 0.5
    elif attacker.ability == "heavymetal" and not abilities_suppressed:
        defender_weight *= 2
    if attacker.item == "floatstone":
        attacker_weight *= 0.5

    if move.id == "payback":
        base_power = base_power * (2 if not attacker_first else 1)
    elif move.id in ["boltbeak", "fishiousrend"]:
        base_power = base_power * (2 if attacker_first else 1)

    elif move.id == "electroball":
        if defender_spe == 0:
            base_power = 40
        elif math.floor(attacker_spe / defender_spe) >= 4:
            base_power = 150
        elif math.floor(attacker_spe / defender_spe) >= 3:
            base_power = 120
        elif math.floor(attacker_spe / defender_spe) >= 2:
            base_power = 80
        elif math.floor(attacker_spe / defender_spe) >= 1:
            base_power = 60
        else:
            base_power = 40
    elif move.id == "gyroball":
        if attacker_spe == 0:
            base_power = 1
        else:
            base_power = min(150, math.floor((25 * defender_spe) / attacker_spe) + 1)
    elif move.id == "punishment":
        base_power = min(
            200,
            60
            + 20
            * sum(
                map(lambda x: defender.boosts[x], ["atk", "def", "spa", "spd", "spe"])
            ),
        )
    elif move.id in ["lowkick", "grassknot"]:
        if defender_weight >= 200:
            base_power = 120
        elif defender_weight >= 100:
            base_power = 100
        elif defender_weight >= 50:
            base_power = 80
        elif defender_weight >= 25:
            base_power = 60
        elif defender_weight >= 10:
            base_power = 40
        else:
            base_power = 20
    elif move.id in ["hex", "infernalparade"]:
        base_power = base_power * (
            2 if defender.status is not None or defender.ability == "comatose" else 1
        )
    elif move.id == "barbarrage":
        base_power = base_power * (
            2 if defender.status in [Status.PSN, Status.TOX] else 1
        )
    elif move.id in ["heavyslam", "heatcrash"]:
        if defender_weight == 0:
            base_power = 40
        elif attacker_weight / defender_weight >= 5:
            base_power = 120
        elif attacker_weight / defender_weight >= 4:
            base_power = 100
        elif attacker_weight / defender_weight >= 3:
            base_power = 80
        elif attacker_weight / defender_weight >= 2:
            base_power = 60
        else:
            base_power = 40
    elif move.id in ["storedpower", "powertrip"]:
        base_power = 20 + 20 * sum(
            map(lambda x: attacker.boosts[x], ["atk", "def", "spa", "spd", "spe"])
        )
    elif move.id == "acrobatics":
        base_power = base_power * (
            2 if attacker.item == "flyinggem" or attacker.item is None else 1
        )
    elif move.id == "wakeupslap":
        base_power = base_power * (
            2 if defender.status == Status.SLP or defender.ability == "comatose" else 1
        )
    elif move.id == "smellsalts":
        base_power = base_power * (2 if defender.status == Status.PAR else 1)
    elif move.id == "weatherball":
        base_power = base_power * (2 if len(battle.weather) > 0 else 1)
        if attacker.item == "utilityumbrella" and (
            Weather.SUNNYDAY in battle.weather or Weather.RAINDANCE in battle.weather
        ):
            base_power = move.base_power
    elif move.id == "terrainpulse":
        base_power = base_power * (
            2
            if battle.is_grounded(attacker)
            and any(map(lambda x: x.is_terrain, battle.fields))
            else 1
        )
    elif move.id == "risingvoltage":
        base_power = base_power * (
            2
            if battle.is_grounded(defender) and Field.ELECTRIC_TERRAIN in battle.fields
            else 1
        )
    elif move.id == "psyblade":
        base_power = base_power * (
            1.5 if Field.ELECTRIC_TERRAIN in battle.fields else 1
        )
    elif move.id in ["dragonenergy", "eruption", "waterspout"]:
        base_power = max(1, math.floor(150 * attacker.current_hp_fraction))
    elif move.id in ["flail", "reversal"]:
        if math.floor(48 * attacker.current_hp_fraction) <= 1:
            base_power = 200
        elif math.floor(48 * attacker.current_hp_fraction) <= 4:
            base_power = 150
        elif math.floor(48 * attacker.current_hp_fraction) <= 9:
            base_power = 100
        elif math.floor(48 * attacker.current_hp_fraction) <= 16:
            base_power = 80
        elif math.floor(48 * attacker.current_hp_fraction) <= 32:
            base_power = 40
        else:
            base_power = 20
    elif move.id == "naturepower":
        if attacker.ability == "prankster" and PokemonType.DARK in defender.types:
            base_power = 0
        elif Field.ELECTRIC_TERRAIN in battle.fields:
            base_power = 90
        elif Field.GRASSY_TERRAIN in battle.fields:
            base_power = 90
        elif Field.MISTY_TERRAIN in battle.fields:
            base_power = 95
        elif Field.PSYCHIC_TERRAIN in battle.fields:
            if attacker.ability == "prankster" and battle.is_grounded(defender):
                base_power = 0
            else:
                base_power = 90
        else:
            base_power = 80
    elif move.id in ["crushgrip", "wringout", "hardpress"]:
        base_power = 100 * math.floor((defender.current_hp_fraction * 4096))
        base_power = math.floor(math.floor((120 * base_power + 2048 - 1) / 4096) / 100)
    elif move.id == "terablast":
        base_power = 100 if attacker.type_1 == PokemonType.STELLAR else 80

    if base_power == 0:
        return 0

    bp_mods = calculate_base_power_mods(
        attacker_identifier,
        defender_identifier,
        move,
        battle,
        base_power,
        has_ate_ability_type_change,
        attacker_first,
    )
    base_power = max(
        1, poke_round(base_power * chain_mods(bp_mods, 41, 2097152) / 4096)
    )

    # Tera moves have a minimum base power
    if (
        attacker.is_terastallized
        and move.type == attacker.tera_type
        and move.priority <= 0
        and move.base_power > 0
        and base_power < 60
    ) and move.id != "struggle":
        base_power = 60
    return base_power


def calculate_base_power_mods(
    attacker_identifier: str,
    defender_identifier: str,
    move: Move,
    battle: Union[Battle, DoubleBattle],
    base_power: float,
    has_ate_ability_type_change: bool,
    attacker_first: bool,  # replaces turn_order
):
    assert battle.player_role
    attacker = battle.get_pokemon(attacker_identifier)
    defender = battle.get_pokemon(defender_identifier)

    bp_mods = []
    abilities_suppressed = any(
        map(lambda x: x and x.ability == "neutralizinggas", battle.all_active_pokemons)
    )

    # ####################### Move Effects ########################
    # technically they need to be item/mon pairs, but this is good enough
    extra_knockoff_damage = defender.item is not None
    if defender.item is not None:
        if defender.item.endswith("memory"):
            extra_knockoff_damage = False
        elif defender.item.endswith("drive"):
            extra_knockoff_damage = False
        elif defender.item in {
            "adamantcrystal",
            "lustrousglobe",
            "griseousorb",
            "griseouscore",
            "redorb",
            "blueorb",
            "drive",
            "memory",
            "rustedsword",
            "rustedsheild",
            "cornerstonemask",
            "hearthflamemask",
            "wellspringmask",
            None,
        }:
            extra_knockoff_damage = False

    if (
        (
            move.id == "facade"
            and attacker.status in {Status.BRN, Status.PAR, Status.PSN, Status.TOX}
        )
        or (move.id == "brine" and defender.current_hp_fraction <= 0.5)
        or (move.id == "venoshock" and defender.status in {Status.PSN, Status.TOX})
        or (move.id == "lashout" and sum(attacker.boosts.values()) < 0)
    ):
        bp_mods.append(8192)
    elif (
        move.id == "expandingforce"
        and battle.is_grounded(attacker)
        and Field.PSYCHIC_TERRAIN in battle.fields
    ):
        bp_mods.append(6144)
    elif (
        (move.id == "knockoff" and extra_knockoff_damage)
        or (
            move.id == "mistyexplosion"
            and battle.is_grounded(attacker)
            and Field.MISTY_TERRAIN in battle.fields
        )
        or (move.id == "gravapple" and Field.GRAVITY in battle.fields)
    ):
        bp_mods.append(6144)
    elif (
        move.id in ["solarbeam", "solarblade"]
        and len(battle.weather) > 0
        and Weather.SUNNYDAY not in battle.fields
    ):
        bp_mods.append(2048)
    elif move.id in ["electrodrift", "collisioncourse"]:

        first_type_effectiveness = get_move_effectiveness(
            move,
            move.type,
            defender.type_1,
            attacker.ability in ["scrappy", "mindseye"],
            Field.GRAVITY in battle.fields,
            defender.item == "ringtarget",
        )

        second_type_effectiveness = (
            1
            if len(defender.types) == 1
            else get_move_effectiveness(
                move,
                move.type,
                defender.type_2,  # type: ignore
                attacker.ability in ["scrappy", "mindseye"],
                Field.GRAVITY in battle.fields,
                defender.item == "ringtarget",
            )
        )

        if first_type_effectiveness * second_type_effectiveness >= 2:
            bp_mods.append(5461)

    if Effect.HELPING_HAND in attacker.effects:
        bp_mods.append(6144)

    # ####################### Field Effects ########################

    if battle.is_grounded(attacker) and (
        (Field.ELECTRIC_TERRAIN in battle.fields and move.type == PokemonType.ELECTRIC)
        or (Field.GRASSY_TERRAIN in battle.fields and move.type == PokemonType.GRASS)
        or (Field.PSYCHIC_TERRAIN in battle.fields and move.type == PokemonType.PSYCHIC)
    ):
        bp_mods.append(5325)

    if battle.is_grounded(defender) and (
        (Field.MISTY_TERRAIN in battle.fields and move.type == PokemonType.DRAGON)
        or (
            Field.GRASSY_TERRAIN in battle.fields
            and move.id in ["bulldoze", "earthquake"]
        )
    ):
        bp_mods.append(2048)

    # ####################### Ability Effects ########################
    # NOTE: I don't support auras here

    if not abilities_suppressed and (
        (attacker.ability == "technician" and base_power <= 60)
        or (
            attacker.ability == "flareboost"
            and attacker.status == Status.BRN
            and move.category == MoveCategory.SPECIAL
        )
        or (
            attacker.ability == "toxicboost"
            and attacker.status in {Status.PSN, Status.TOX}
            and move.category == MoveCategory.PHYSICAL
        )
        or (attacker.ability == "megalauncher" and "pulse" in move.flags)
        or (attacker.ability == "strongjaw" and "bite" in move.flags)
        or (attacker.ability == "sharpness" and "slicing" in move.flags)
    ):
        bp_mods.append(6144)

    if not abilities_suppressed and (
        (attacker.ability == "sheerforce" and (move.secondary or move.id == "orderup"))
        or (
            attacker.ability == "sandforce"
            and Weather.SANDSTORM in battle.weather
            and move.type in {PokemonType.ROCK, PokemonType.GROUND, PokemonType.STEEL}
        )
        or (attacker.ability == "analytic" and not attacker_first)
        or (attacker.ability == "toughclaws" and "contact" in move.flags)
        or (attacker.ability == "punkrock" and "sound" in move.flags)
    ):
        bp_mods.append(5325)

    attacking_mons = (
        battle.active_pokemon
        if attacker_identifier.startswith(battle.player_role)
        else battle.opponent_active_pokemon
    )
    ally_attacking_mon = None
    if isinstance(battle, DoubleBattle) and isinstance(attacking_mons, list):
        ally_attacking_mon = battle.active_pokemon[
            1 if attacker == attacking_mons[0] else 0
        ]
    for mon in attacking_mons if isinstance(attacking_mons, list) else [attacking_mons]:
        if (
            mon is not None
            and mon.ability == "steelyspirit"
            and move.type == PokemonType.STEEL
            and not abilities_suppressed
        ):
            bp_mods.append(6144)

    if (
        ally_attacking_mon
        and ally_attacking_mon.ability == "battery"
        and move.category == MoveCategory.SPECIAL
        and not abilities_suppressed
    ):
        bp_mods.append(5325)

    if (
        ally_attacking_mon
        and ally_attacking_mon.ability == "powerspot"
        and not abilities_suppressed
    ):
        bp_mods.append(5325)

    if (
        attacker.ability == "rivalry"
        and not attacker.gender == PokemonGender.NEUTRAL
        and not defender.gender == PokemonGender.NEUTRAL
        and not abilities_suppressed
    ):
        if attacker.gender == defender.gender:
            bp_mods.append(5120)
        else:
            bp_mods.append(3072)

    if has_ate_ability_type_change:
        bp_mods.append(4915)

    if not abilities_suppressed and (
        (attacker.ability == "reckless" and move.recoil > 0)
        or (attacker.ability == "ironfist" and "punch" in move.flags)
    ):
        bp_mods.append(4915)

    if (
        defender.ability == "dryskin"
        and move.type == PokemonType.FIRE
        and not abilities_suppressed
    ):
        bp_mods.append(5120)

    attacking_team = (
        battle.team
        if attacker_identifier.startswith(battle.player_role)
        else battle.opponent_team
    )
    num_fainted = len([mon for mon in attacking_team.values() if mon.fainted])
    if (
        attacker.ability == "supremeoverlord"
        and num_fainted > 0
        and not abilities_suppressed
    ):
        pow_mod = [4096, 4506, 4915, 5325, 5734, 6144]
        bp_mods.append(pow_mod[min(num_fainted, 5)])

    # ####################### Item Effects ########################
    if (attacker.item or "").replace(" gem", "") == move.type.name.lower():
        bp_mods.append(5325)
    elif (
        (
            attacker.item == "adamantcrystal"
            and attacker.species == "dialgaorigin"
            and move.type in [PokemonType.STEEL, PokemonType.DRAGON]
        )
        or (
            attacker.item == "adamantorb"
            and attacker.species == "dialga"
            and move.type in [PokemonType.STEEL, PokemonType.DRAGON]
        )
        or (
            attacker.item == "lustrousorb"
            and attacker.species == "palkia"
            and move.type in [PokemonType.WATER, PokemonType.DRAGON]
        )
        or (
            attacker.item == "lustrousglobe"
            and attacker.species == "palkiaorigin"
            and move.type in [PokemonType.WATER, PokemonType.DRAGON]
        )
        or (
            attacker.item in ["griseousorb", "griseouscore"]
            and attacker.species in ["giratinaorigin", "giratina"]
            and move.type in [PokemonType.GHOST, PokemonType.DRAGON]
        )
        or (attacker.item == "souldew" and attacker.species in ["latios", "latias"])
        and move.type in [PokemonType.PSYCHIC, PokemonType.DRAGON]
        or (attacker.item and move.type == get_item_boost_type(attacker.item))
        or (
            attacker.species.startswith("ogerpon")
            and attacker.item
            and attacker.item.endswith("mask")
        )
    ):
        bp_mods.append(4915)
    elif (attacker.item == "muscleband" and move.category == MoveCategory.PHYSICAL) or (
        attacker.item == "wiseglasses" and move.category == MoveCategory.SPECIAL
    ):
        bp_mods.append(4505)
    elif attacker.item == "punchingglove" and "punch" in move.flags:
        bp_mods.append(4506)

    return bp_mods


def calculate_attack(
    attacker_identifier: str,
    defender_identifier: str,
    move: Move,
    battle: Union[Battle, DoubleBattle],
    is_critical: bool = False,
):
    attacker = battle.get_pokemon(attacker_identifier)
    defender = battle.get_pokemon(defender_identifier)

    attack = 0
    attack_stat = "atk" if move.category == MoveCategory.PHYSICAL else "spa"
    if move.id == "bodypress":
        attack_stat = "def"

    attack_source = attacker if move.id != "foulplay" else defender

    if (
        attack_source.stats[attack_stat] is not None
        and attack_source.boosts[attack_stat] == 0
        or (is_critical and attack_source.boosts[attack_stat] < 0)
        or defender.ability == "unaware"
    ):
        attack = attack_source.stats[attack_stat]  # type: ignore
    elif attack_source.stats[attack_stat] is not None:
        attack = math.floor(
            attack_source.stats[attack_stat]  # type: ignore
            * BOOST_MULTIPLIERS[attack_source.boosts[attack_stat]]
        )

    if attacker.ability == "hustle" and move.category == MoveCategory.PHYSICAL:
        attack = poke_round((attack * 3) / 2)  # type: ignore

    at_mods = calculate_atk_mods(attacker_identifier, defender_identifier, move, battle)
    return max(1, poke_round((attack * chain_mods(at_mods, 410, 131072)) / 4096))  # type: ignore


def calculate_atk_mods(
    attacker_identifier: str,
    defender_identifier: str,
    move: Move,
    battle: Union[Battle, DoubleBattle],
):
    assert battle.player_role is not None
    attacker = battle.get_pokemon(attacker_identifier)
    defender = battle.get_pokemon(defender_identifier)

    atk_mods = []
    attacker_mons = (
        battle.active_pokemon
        if attacker_identifier.startswith(battle.player_role)
        else battle.opponent_active_pokemon
    )
    attacker_ally = None
    if isinstance(battle, DoubleBattle) and isinstance(attacker_mons, list):
        attacker_ally = (
            attacker_mons[0] if attacker == attacker_mons[1] else attacker_mons[1]
        )

    abilities_suppressed = any(
        map(lambda x: x and x.ability == "neutralizinggas", battle.all_active_pokemons)
    )

    if (
        Effect.SLOW_START in attacker.effects and move.category == MoveCategory.PHYSICAL
    ) or (attacker.ability == "defeatist" and attacker.current_hp_fraction <= 0.5):
        atk_mods.append(2048)
    elif (
        attacker.ability == "solarpower"
        and Weather.SUNNYDAY in battle.weather
        and move.category == MoveCategory.SPECIAL
    ) or (
        attacker.species == "cherrim"
        and attacker.ability == "flowergift"
        and Weather.SUNNYDAY in battle.weather
        and move.category == MoveCategory.PHYSICAL
    ):
        atk_mods.append(6144)
    elif (
        attacker.ability == "gorillatactics" and move.category == MoveCategory.PHYSICAL
    ):
        atk_mods.append(6144)
    elif (
        (
            attacker.ability == "guts"
            and attacker.status
            and move.category == MoveCategory.PHYSICAL
        )
        or (
            attacker.current_hp_fraction <= 1.0 / 3
            and (
                (attacker.ability == "overgrow" and move.type == PokemonType.GRASS)
                or (attacker.ability == "blaze" and move.type == PokemonType.FIRE)
                or (attacker.ability == "torrent" and move.type == PokemonType.WATER)
                or (attacker.ability == "swarm" and move.type == PokemonType.BUG)
            )
        )
        or (
            isinstance(battle, DoubleBattle)
            and move.category == MoveCategory.SPECIAL
            and attacker_mons[0]  # type: ignore
            and attacker_mons[1]  # type: ignore
            and attacker_mons[0].ability in ["plus", "minus"]  # type: ignore
            and attacker_mons[1].ability in ["plus", "minus"]  # type: ignore
            and attacker_mons[0].ability != attacker_mons[1].ability  # type: ignore
            and not abilities_suppressed
        )
    ):
        atk_mods.append(6144)
    elif (
        attacker.ability == "flashfire"
        and Effect.FLASH_FIRE in attacker.effects
        and move.type == PokemonType.FIRE
    ):
        atk_mods.append(6144)
    elif (
        (attacker.ability == "steelworker" and move.type == PokemonType.STEEL)
        or (attacker.ability == "dragonsmaw" and move.type == PokemonType.DRAGON)
        or (attacker.ability == "rockypayload" and move.type == PokemonType.ROCK)
    ):
        atk_mods.append(6144)
    elif attacker.ability == "transistor" and move.type == PokemonType.ELECTRIC:
        atk_mods.append(5325)
    elif attacker.ability == "stakeout" and not abilities_suppressed:
        atk_mods.append(8192)
    elif (attacker.ability == "waterbubble" and move.type == PokemonType.WATER) or (
        attacker.ability in ["hugemount", "purepower"]
        and move.category == MoveCategory.PHYSICAL
    ):
        atk_mods.append(8192)

    if (
        attacker_ally
        and attacker_ally.ability == "flowergift"
        and Weather.SUNNYDAY in battle.weather
        and move.category == MoveCategory.PHYSICAL
        and not abilities_suppressed
    ):
        atk_mods.append(6144)

    if (
        attacker.ability == "steellyspirit"
        or (attacker_ally and attacker_ally.ability == "steellyspirit")
    ) and not abilities_suppressed:
        atk_mods.append(6144)

    if (
        (
            defender.ability == "thickfat"
            and move.type in [PokemonType.FIRE, PokemonType.ICE]
        )
        or (defender.ability == "waterbubble" and move.type == PokemonType.FIRE)
        or (defender.ability == "purifysalt" and move.type == PokemonType.GHOST)
    ):
        atk_mods.append(2048)

    if defender.ability == "heatproof" and move.type == PokemonType.FIRE:
        atk_mods.append(2048)

    is_tablets_of_ruin_active = (
        any(
            map(
                lambda x: x and x.ability == "tabletsofruin", battle.all_active_pokemons
            )
        )
        and not abilities_suppressed
    )

    is_vessel_of_ruin_active = (
        any(
            map(lambda x: x and x.ability == "vesselofruin", battle.all_active_pokemons)
        )
        and not abilities_suppressed
    )

    if is_tablets_of_ruin_active and move.category == MoveCategory.PHYSICAL:
        atk_mods.append(3072)

    if is_vessel_of_ruin_active and move.category == MoveCategory.SPECIAL:
        atk_mods.append(3072)

    if (
        (
            Effect.PROTOSYNTHESISATK in attacker.effects
            and move.category == MoveCategory.PHYSICAL
        )
        or (
            Effect.QUARKDRIVEATK in attacker.effects
            and move.category == MoveCategory.PHYSICAL
        )
        or (
            Effect.PROTOSYNTHESISSPA in attacker.effects
            and move.category == MoveCategory.SPECIAL
        )
        or (
            Effect.QUARKDRIVESPA in attacker.effects
            and move.category == MoveCategory.SPECIAL
        )
    ):
        atk_mods.append(5325)

    if (
        attacker.ability == "hadronengine"
        and move.category == MoveCategory.SPECIAL
        and Field.ELECTRIC_TERRAIN in battle.fields
    ) or (
        attacker.ability == "orichalcumpulse"
        and move.category == MoveCategory.PHYSICAL
        and Weather.SUNNYDAY in battle.weather
        and not attacker.item == "utilityumbrella"
    ):
        atk_mods.append(5461)

    if (
        (
            attacker.item == "thickclub"
            and attacker.base_species in ["cubone", "marowak"]
            and move.category == MoveCategory.PHYSICAL
        )
        or (
            attacker.item == "deepseatooth"
            and attacker.base_species == "clamperl"
            and move.category == MoveCategory.SPECIAL
        )
        or (attacker.item == "lightball" and attacker.base_species == "pikachu")
    ):
        atk_mods.append(8192)
    elif (attacker.item == "choiceband" and move.category == MoveCategory.PHYSICAL) or (
        attacker.item == "choicespecs" and move.category == MoveCategory.SPECIAL
    ):
        atk_mods.append(6144)

    return atk_mods


# NOTE: ignore shellsidearm
def calculate_defense(
    attacker_identifier: str,
    defender_identifier: str,
    move: Move,
    battle: Union[Battle, DoubleBattle],
    is_critical: bool = False,
):
    attacker = battle.get_pokemon(attacker_identifier)
    defender = battle.get_pokemon(defender_identifier)

    defense = 0

    hits_physical = (
        move.category == MoveCategory.PHYSICAL
        or move.entry.get("overrideDefensiveStat", "") == "def"
    )
    defense_stat = "def" if hits_physical else "spd"

    if (
        defender.stats[defense_stat] is not None
        and defender.boosts[defense_stat] == 0
        or (is_critical and defender.boosts[defense_stat] > 0)
        or move.ignore_defensive
        or attacker.ability == "unaware"
    ):
        defense = defender.stats[defense_stat]  # type: ignore
    elif defender.stats[defense_stat] is not None:
        defense = math.floor(
            defender.stats[defense_stat]  # type: ignore
            * BOOST_MULTIPLIERS[defender.boosts[defense_stat]]
        )

    if (
        Weather.SANDSTORM in battle.weather
        and PokemonType.ROCK in defender.types
        and not hits_physical
    ) or (
        Weather.SNOW in battle.weather
        and PokemonType.ICE in defender.types
        and hits_physical
    ):
        defense = poke_round((defense * 3) / 2)  # type: ignore

    def_mods = calculate_def_mods(
        attacker_identifier, defender_identifier, battle, hits_physical
    )

    return max(1, poke_round((defense * chain_mods(def_mods, 410, 131072)) / 4096))  # type: ignore


def calculate_def_mods(
    attacker_identifier: str,
    defender_identifier: str,
    battle: Union[Battle, DoubleBattle],
    hits_physical: bool = False,
):
    assert battle.player_role is not None
    attacker = battle.get_pokemon(attacker_identifier)
    defender = battle.get_pokemon(defender_identifier)

    defender_mons = (
        battle.active_pokemon
        if defender_identifier.startswith(battle.player_role)
        else battle.opponent_active_pokemon
    )
    defender_ally = None
    if isinstance(battle, DoubleBattle) and isinstance(defender_mons, list):
        defender_ally = (
            defender_mons[0] if defender == defender_mons[1] else defender_mons[1]
        )

    abilities_suppressed = any(
        map(lambda x: x and x.ability == "neutralizinggas", battle.all_active_pokemons)
    )

    def_mods = []
    if defender.ability == "marvelscale" and defender.status and hits_physical:
        def_mods.append(6144)
    elif (
        defender.species == "cherrim"
        and defender.ability == "flowergift"
        and Weather.SUNNYDAY not in battle.weather
        and not hits_physical
    ):
        def_mods.append(6144)
    elif (
        defender_ally
        and defender_ally.ability == "flowergift"
        and Weather.SUNNYDAY in battle.weather
        and not hits_physical
        and not abilities_suppressed
    ):
        def_mods.append(6144)
    elif (
        defender.ability == "grasspelt"
        and Field.GRASSY_TERRAIN in battle.fields
        and hits_physical
    ):
        def_mods.append(6144)
    elif defender.ability == "furcoat" and hits_physical:
        def_mods.append(8192)

    is_swords_of_ruin_active = (
        attacker.ability == "swordsofruin"
        or (
            any(
                map(
                    lambda x: x and x.ability == "swordsofruin",
                    battle.all_active_pokemons,
                )
            )
            and defender.ability != "swordsofruin"
        )
    ) and not abilities_suppressed

    is_beads_of_ruin_active = (
        attacker.ability == "beadsofruin"
        or (
            any(
                map(
                    lambda x: x and x.ability == "beadsofruin",
                    battle.all_active_pokemons,
                )
            )
            and defender.ability != "beadsofruin"
        )
    ) and not abilities_suppressed

    if (is_swords_of_ruin_active and hits_physical) or (
        is_beads_of_ruin_active and not hits_physical
    ):
        def_mods.append(3072)

    if (
        hits_physical
        and (
            Effect.QUARKDRIVEDEF in defender.effects
            or Effect.PROTOSYNTHESISDEF in defender.effects
        )
    ) or (
        not hits_physical
        and (
            Effect.QUARKDRIVESPD in defender.effects
            or Effect.PROTOSYNTHESISSPD in defender.effects
        )
    ):
        def_mods.append(5324)

    if (
        defender.item == "eviolite"
        and (
            defender.species == "dipplin"
            or len(defender._data.pokedex[defender.species].get("evos", [])) > 0
        )
    ) or (defender.item == "assaultvest" and not hits_physical):
        def_mods.append(6144)
    elif (
        defender.item == "metalpowder" and defender.species == "ditto" and hits_physical
    ) or (
        defender.item == "deepseascale"
        and defender.species == "clamperl"
        and not hits_physical
    ):
        def_mods.append(8192)

    return def_mods


def calculate_base_damage(
    attacker_identifier: str,
    defender_identifier: str,
    base_power: float,
    attack: float,
    defense: float,
    move: Move,
    move_type: Optional[PokemonType],
    move_target: Target,
    battle: Union[Battle, DoubleBattle],
    is_critical: bool = False,
):
    assert battle.player_role is not None
    attacker = battle.get_pokemon(attacker_identifier)
    defender = battle.get_pokemon(defender_identifier)
    defending_mons = (
        battle.active_pokemon
        if defender_identifier.startswith(battle.player_role)
        else battle.opponent_active_pokemon
    )

    is_spread = (
        isinstance(battle, DoubleBattle)
        and defending_mons[0] is not None  # type: ignore
        and defending_mons[1] is not None  # type: ignore
        and move_target in [Target.ALL_ADJACENT, Target.ALL_ADJACENT_FOES]
    )

    base_damage = math.floor(
        math.floor(
            (math.floor(2 * attacker.level / 5 + 2) * base_power) * attack / defense
        )
        / 50
        + 2
    )

    if is_spread:
        base_damage = poke_round((base_damage * 3072) / 4096)

    if (
        Weather.SUNNYDAY in battle.weather
        and move.id == "hydrosteam"
        and attacker.item != "utilityumbrella"
    ):
        base_damage = poke_round((base_damage * 6144) / 4096)
    elif defender.item != "utilityumbrella":
        if (Weather.SUNNYDAY in battle.weather and move_type == PokemonType.FIRE) or (
            Weather.RAINDANCE in battle.weather and move_type == PokemonType.WATER
        ):
            base_damage = poke_round((base_damage * 6144) / 4096)
        elif (
            Weather.SUNNYDAY in battle.weather and move_type == PokemonType.WATER
        ) or (Weather.RAINDANCE in battle.weather and move_type == PokemonType.FIRE):
            base_damage = poke_round((base_damage * 2048) / 4096)

    if is_critical:
        base_damage = poke_round((base_damage * 1.5))

    return base_damage


# NOTE: do not calculate metronome
def calculate_final_mods(
    attacker_identifier: str,
    defender_identifier: str,
    move: Move,
    battle: Union[Battle, DoubleBattle],
    type_effectiveness: float,
    flags: Dict[str, int],
    is_critical: bool = False,
    hit_count: int = 0,
):
    assert battle.player_role is not None
    attacker = battle.get_pokemon(attacker_identifier)
    defender = battle.get_pokemon(defender_identifier)
    final_mods = []

    defender_side_conditions = (
        battle.side_conditions
        if defender_identifier.startswith(battle.player_role)
        else battle.opponent_side_conditions
    )
    defending_mons = (
        battle.active_pokemon
        if defender_identifier.startswith(battle.player_role)
        else battle.opponent_active_pokemon
    )
    defender_ally = None
    if isinstance(defending_mons, list):
        defender_ally = (
            defending_mons[0] if defender == defending_mons[1] else defending_mons[1]
        )

    abilities_suppressed = any(
        map(lambda x: x and x.ability == "neutralizinggas", battle.all_active_pokemons)
    )

    if (
        SideCondition.REFLECT in defender_side_conditions
        and move.category == MoveCategory.PHYSICAL
        and not is_critical
        and SideCondition.AURORA_VEIL not in defender_side_conditions
        and not flags.get("ignorescreens", 0) == 1
    ):
        final_mods.append(2048 if not isinstance(battle, DoubleBattle) else 2732)
    elif (
        SideCondition.LIGHT_SCREEN in defender_side_conditions
        and move.category == MoveCategory.SPECIAL
        and not is_critical
        and SideCondition.AURORA_VEIL not in defender_side_conditions
        and not flags.get("ignorescreens", 0) == 1
    ):
        final_mods.append(2048 if not isinstance(battle, DoubleBattle) else 2732)
    elif (
        SideCondition.AURORA_VEIL in defender_side_conditions
        and not is_critical
        and not flags.get("ignorescreens", 0) == 1
    ):
        final_mods.append(2048 if not isinstance(battle, DoubleBattle) else 2732)

    if attacker.ability == "neuroforce" and type_effectiveness > 1:
        final_mods.append(5120)
    elif attacker.ability == "sniper" and is_critical:
        final_mods.append(6144)
    elif attacker.ability == "tintedlens" and type_effectiveness < 1:
        final_mods.append(8192)

    if (
        defender.ability in ["multiscale", "shadowshield"]
        and defender.current_hp_fraction == 1
        and hit_count <= 1
    ):
        final_mods.append(2048)

    if (
        defender.ability == "fluffy"
        and "contact" in flags
        and not attacker.ability == "longreach"
    ):
        final_mods.append(2048)
    elif (defender.ability == "punkrock" and "sound" in flags) or (
        defender.ability == "icescales" and move.category == MoveCategory.SPECIAL
    ):
        final_mods.append(2048)

    if (
        defender.ability in ["solidrock", "filter", "prismarmor"]
        and type_effectiveness > 1
    ):
        final_mods.append(3072)

    if (
        defender_ally
        and defender_ally.ability == "friendguard"
        and not abilities_suppressed
    ):
        final_mods.append(3072)

    if defender.ability == "fluffy" and move.type == PokemonType.FIRE:
        final_mods.append(8192)

    if defender.ability == "fluffy" and move.type == PokemonType.FIRE:
        final_mods.append(8192)

    if attacker.item == "expertbelt" and type_effectiveness > 1:
        final_mods.append(4915)
    elif attacker.item == "lifeorb":
        final_mods.append(5324)

    if (
        (defender.item and get_berry_resist_type(defender.item) == move.type)
        and (type_effectiveness > 1 or PokemonType.NORMAL)
        and hit_count == 0
        and attacker.ability not in ["unnerve", "asone"]
    ):
        final_mods.append(1024 if defender.ability == "ripen" else 2048)

    return final_mods


def get_stab_mod(pokemon: Pokemon, move: Move, move_type: Optional[PokemonType]):
    stab_mod = 4096
    if move.id == "struggle":  # struggle is typeless
        return stab_mod

    if move_type in pokemon.original_types:
        stab_mod += 2048
    elif pokemon.ability in ["protean", "libero"] and not pokemon.is_terastallized:
        stab_mod += 2048

    tera_type = pokemon.tera_type
    if (
        tera_type == move_type
        and tera_type != PokemonType.STELLAR
        and pokemon.is_terastallized
    ):
        stab_mod += 2048
    if pokemon.ability == "adaptability" and move_type in pokemon.types:
        stab_mod += (
            1024
            if pokemon.is_terastallized and tera_type in pokemon.original_types
            else 2048
        )

    return stab_mod


# NOTE: we don't store whether a pokemon used a first move after stellar, and so
# we fail all stellar calculations
def get_stellar_stab_mod(pokemon: Pokemon, move: Move, stab_mod=1):
    is_stellar_boosted = False
    # is_stellar_boosted = (
    #     pokemon.tera_type == PokemonType.STELLAR and (
    #         (move.is_stellar_first_use and turns == 0) or pokemon.species == "terapagosstellar"
    #     )
    # )

    if is_stellar_boosted:
        if move.type in pokemon.original_types:
            stab_mod += 2048
        else:
            stab_mod = 4915

    return stab_mod


def get_berry_resist_type(berry: str) -> Optional[PokemonType]:
    return BERRY_RESISTS.get(berry, None)


def get_item_boost_type(item: str) -> Optional[PokemonType]:
    return ITEM_BOOST_TYPES.get(item, None)  # type: ignore


# Gamefreak rounds down on even number
def poke_round(num: float):
    return math.ceil(num) if num % 1 > 0.5 else math.floor(num)


def get_final_damage(
    base_amount: int,
    i: int,
    effectiveness: float,
    is_burned: bool,
    stab_mod: int,
    final_mod: int,
) -> float:
    damage_amount = math.floor(base_amount * (85 + i) / 100) * 1.0
    if stab_mod != 4096:
        damage_amount = (damage_amount * stab_mod) / 4096

    damage_amount = math.floor(poke_round(damage_amount) * effectiveness)

    if is_burned:
        damage_amount = math.floor(damage_amount / 2)

    return poke_round(max(1, (damage_amount * final_mod) / 4096))


def chain_mods(mods: List[int], lb: int, ub: int):
    m = 4096
    for mod in mods:
        if mod != 4096:
            m = (m * mod + 2048) >> 12

    return max(min(m, ub), lb)


def get_move_effectiveness(
    move: Move,
    move_type: PokemonType,
    type: PokemonType,
    is_ghost_revealed: Optional[bool] = False,
    is_gravity: Optional[bool] = False,
    is_ring_target: Optional[bool] = False,
) -> float:
    if (
        is_ghost_revealed
        and type == PokemonType.GHOST
        and move_type in (PokemonType.NORMAL, PokemonType.FIGHTING)
    ):
        return 1
    elif move.id == "struggle":
        return 1
    elif is_gravity and type == PokemonType.FLYING and move_type == PokemonType.GROUND:
        return 1
    elif move.id == "freezedry" and type == PokemonType.WATER:
        return 2
    else:
        effectiveness = PokemonType.damage_multiplier(
            move_type, type, type_chart=GenData.from_gen(9).type_chart
        )
        if effectiveness == 0 and is_ring_target:
            effectiveness = 1
        if move.id == "flyingpress":
            effectiveness *= PokemonType.damage_multiplier(
                PokemonType.FLYING, type, type_chart=GenData.from_gen(9).type_chart
            )
        return effectiveness


PROTECT_EFFECTS = {
    Effect.PROTECT,
    Effect.SPIKY_SHIELD,
    Effect.KINGS_SHIELD,
    Effect.BANEFUL_BUNKER,
    Effect.BURNING_BULWARK,
    Effect.OBSTRUCT,
    Effect.MAX_GUARD,
    Effect.SILK_TRAP,
}

ABILITY_IGNORES_NEUTRALIZING_GAS = {
    "asone",
    "battlebond",
    "comatose",
    "disguise",
    "gulpmissile",
    "iceface",
    "multitype",
    "neutralizinggas",
    "powerconstruct",
    "rksystem",
    "schooling",
    "shieldsdown",
    "stancechange",
    "terashift",
    "zenmode",
    "zerotohero",
}

ATTACKER_IGNORES_ABILITY = {"moldbreaker", "teravolt", "turboblaze"}

MOVE_IGNORES_ABILITY = {"moongeistbeam", "photongeyser", "sunsteelstrike"}

DEFENDER_ABILITY_IGNORED = {
    "armortail",
    "aromaveil",
    "aurabreak",
    "battlearmor",
    "bigpecks",
    "bulletproof",
    "clearbody",
    "contrary",
    "damp",
    "dazzling",
    "disguise",
    "dryskin",
    "eartheater",
    "filter",
    "flashfire",
    "flowergift",
    "flowerveil",
    "fluffy",
    "friendguard",
    "furcoat",
    "goodasgold",
    "grasspelt",
    "guarddog",
    "heatproof",
    "heavymetal",
    "hypercutter",
    "iceface",
    "icescales",
    "illuminate",
    "immunity",
    "innerfocus",
    "insomnia",
    "keeneye",
    "leafguard",
    "levitate",
    "lightmetal",
    "lightningrod",
    "limber",
    "magicbounce",
    "magmarmor",
    "marvelscale",
    "mindseye",
    "mirrorarmor",
    "motordrive",
    "multiscale",
    "oblivious",
    "overcoat",
    "owntempo",
    "pastelveil",
    "punkrock",
    "purifysalt",
    "queenlymajesty",
    "quickfeet",
    "raindish",
    "rockhead",
    "rocky",
    "roughskin",
    "sandveil",
    "scrappy",
    "simple",
    "snowcloak",
    "snowwarning",
    "solidrock",
    "soundproof",
    "speedboost",
    "stakeout",
    "steelworker",
    "strongjaw",
    "suctioncups",
    "tintedlens",
    "torrent",
    "trace",
    "waterabsorb",
    "waterveil",
    "weakarmor",
    "wonderguard",
    "wonderskin",
}

BOOST_MULTIPLIERS = {
    -6: 2.0 / 8,
    -5: 2.0 / 7,
    -4: 2.0 / 6,
    -3: 2.0 / 5,
    -2: 2.0 / 4,
    -1: 2.0 / 3,
    0: 1,
    1: 1.5,
    2: 2,
    3: 2.5,
    4: 3,
    5: 3.5,
    6: 4,
}

BERRY_RESISTS = {
    "chilanberry": PokemonType.NORMAL,
    "occaberry": PokemonType.FIRE,
    "passhoberry": PokemonType.WATER,
    "wacanberry": PokemonType.ELECTRIC,
    "rindoberry": PokemonType.GRASS,
    "yacheberry": PokemonType.ICE,
    "chopleberry": PokemonType.FIGHTING,
    "kebiaberry": PokemonType.POISON,
    "shucaberry": PokemonType.GROUND,
    "cobaberry": PokemonType.FLYING,
    "payapaberry": PokemonType.PSYCHIC,
    "tangaberry": PokemonType.BUG,
    "chartiberry": PokemonType.ROCK,
    "kasiberry": PokemonType.GHOST,
    "habanberry": PokemonType.DRAGON,
    "colburberry": PokemonType.DARK,
    "babiriberry": PokemonType.STEEL,
    "roseliberry": PokemonType.FAIRY,
}

ITEM_BOOST_TYPES = {
    "dracoplate": PokemonType.DRAGON,
    "dragonfang": PokemonType.DRAGON,
    "dreadplate": PokemonType.DARK,
    "blackglasses": PokemonType.DARK,
    "earthplate": PokemonType.GROUND,
    "softsand": PokemonType.GROUND,
    "fistplate": PokemonType.FIGHTING,
    "blackbelt": PokemonType.FIGHTING,
    "flameplate": PokemonType.FIRE,
    "charcoal": PokemonType.FIRE,
    "icicleplate": PokemonType.ICE,
    "nevermeltice": PokemonType.ICE,
    "insectplate": PokemonType.BUG,
    "silverpowder": PokemonType.BUG,
    "ironplate": PokemonType.STEEL,
    "metalcoat": PokemonType.STEEL,
    "meadowplate": PokemonType.GRASS,
    "roseincense": PokemonType.GRASS,
    "miracleseed": PokemonType.GRASS,
    "mindplate": PokemonType.PSYCHIC,
    "oddincense": PokemonType.PSYCHIC,
    "twistedspoon": PokemonType.PSYCHIC,
    "fairyfeather": PokemonType.FAIRY,
    "pixieplate": PokemonType.FAIRY,
    "skyplate": PokemonType.FLYING,
    "sharpbeak": PokemonType.FLYING,
    "splashplate": PokemonType.WATER,
    "seaincense": PokemonType.WATER,
    "waveincense": PokemonType.WATER,
    "mysticwater": PokemonType.WATER,
    "spookyplate": PokemonType.GHOST,
    "spelltag": PokemonType.GHOST,
    "stoneplate": PokemonType.ROCK,
    "rockincense": PokemonType.ROCK,
    "hardstone": PokemonType.ROCK,
    "toxicplate": PokemonType.POISON,
    "poisonbarb": PokemonType.POISON,
    "zapplate": PokemonType.ELECTRIC,
    "magnet": PokemonType.ELECTRIC,
    "silkscarf": PokemonType.NORMAL,
    "pinkbow": PokemonType.NORMAL,
    "polkadotbow": PokemonType.NORMAL,
}
