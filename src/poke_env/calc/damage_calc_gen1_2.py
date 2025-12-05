"""This module defines a gen1-2 damage calculator"""

import math
from typing import List, Optional, Union

from poke_env.battle import (
    Battle,
    DoubleBattle,
    Effect,
    Field,
    Move,
    MoveCategory,
    Pokemon,
    PokemonType,
    SideCondition,
    Status,
    Weather,
)
from poke_env.data import GenData

# Source: https://github.com/smogon/damage-calc/blob/master/calc/src/mechanics/gen12.ts


def calculate_damage_gen12(
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
    :return: Tuple of minimum, maximum, and complete list of damage rolls.
    :rtype: Tuple[int, int, list]
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
    if move_category == MoveCategory.STATUS:
        return (0, 0, [0])

    if any(map(lambda x: x in PROTECT_EFFECTS, defender.effects)):
        return (0, 0, [0])

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
            return (damage, damage, [damage])
        else:
            return (0, 0, [0])
    if battle.gen == 1 and "damage" in move.entry:
        damage = handleFixedDamageMoves(attacker, move)
        return (damage, damage, [damage])

    first_defender_type = defender.type_1
    second_defender_type = defender.type_2 if len(defender.types) > 1 else None
    if (
        second_defender_type
        and first_defender_type != second_defender_type
        and battle.gen == 2
    ):
        first_type_precedence = TYPE_EFFECTIVENESS_PRECEDENCE_RULES.index(
            first_defender_type.name
        )
        second_type_precedence = TYPE_EFFECTIVENESS_PRECEDENCE_RULES.index(
            second_defender_type.name
        )

        if first_type_precedence > second_type_precedence:
            first_defender_type, second_defender_type = (
                second_defender_type,
                first_defender_type,
            )

    move_type = move.type
    first_type_effectiveness = get_move_effectiveness(
        battle.gen,
        move,
        move_type,
        first_defender_type,
        Effect.FORESIGHT in defender.effects,
        Field.GRAVITY in battle.fields,
        defender.item == "ringtarget",
    )
    second_type_effectiveness = (
        1
        if second_defender_type is None
        else get_move_effectiveness(
            battle.gen,
            move,
            move_type or move.type,
            second_defender_type,  # type: ignore
            Effect.FORESIGHT in defender.effects,
            Field.GRAVITY in battle.fields,
            defender.item == "ringtarget",
        )
    )

    type_effectiveness = first_type_effectiveness * second_type_effectiveness
    if type_effectiveness == 0:
        return (0, 0, [0])

    if battle.gen == 2 and "damage" in move.entry:
        damage = handleFixedDamageMoves(attacker, move)
        return (damage, damage, [damage])

    if move.id in ("flail", "reversal"):
        is_critical = False
        p = (48 * attacker.current_hp) // attacker.max_hp
        if p <= 1:
            move._base_power_override = 200
        elif p <= 4:
            move._base_power_override = 150
        elif p <= 9:
            move._base_power_override = 100
        elif p <= 16:
            move._base_power_override = 80
        elif p <= 32:
            move._base_power_override = 40
        else:
            move._base_power_override = 20
    elif move.id == "present":  # doesn't calculate for other base power options
        move._base_power_override = 40
    if move.base_power == 0:
        return (0, 0, [0])

    is_physical = move.category == MoveCategory.PHYSICAL
    attack_stat = "atk" if is_physical else "spa"
    defense_stat = "def" if is_physical else "spd"

    # Stats are guaranteed to be int/float by assertions above
    attacker_attack = attacker.stats[attack_stat]
    defender_defense = defender.stats[defense_stat]
    assert attacker_attack is not None
    assert defender_defense is not None

    at = int(attacker_attack * BOOST_MULTIPLIERS[attacker.boosts[attack_stat]])
    df = int(defender_defense * BOOST_MULTIPLIERS[defender.boosts[defense_stat]])

    # Determine if modifiers should be ignored due to a critical hit
    ignore_mods = is_critical and (
        battle.gen == 1
        or (
            battle.gen == 2
            and attacker.boosts[attack_stat] <= defender.boosts[defense_stat]
        )
    )

    lv = attacker.level
    assert at is not None, f"{attack_stat} is None in attacker.stats"

    if ignore_mods:
        assert attacker_attack is not None
        assert defender_defense is not None
        at = int(attacker_attack)
        df = int(defender_defense)

        if battle.gen == 1:
            lv *= 2
    else:
        if is_physical and attacker.status == Status.BRN:
            at = at // 2
    assert at is not None, f"{attack_stat} is None in attacker.stats"
    assert df is not None, f"{defense_stat} is None in defender.stats"
    # Explosion and Self-Destruct halve the defender's defense
    if move.id in ["explosion", "selfdestruct"]:
        df = df // 2
    defender_side_conditions = (
        battle.side_conditions
        if defender_identifier.startswith(battle.player_role)
        else battle.opponent_side_conditions
    )
    # Reflect and Light Screen double the defender's defense unless mods are ignored
    if not ignore_mods:
        if is_physical and SideCondition.REFLECT in defender_side_conditions:
            df *= 2
        elif not is_physical and SideCondition.LIGHT_SCREEN in defender_side_conditions:
            df *= 2

    # Item-based attack boosts
    if (
        attacker.species == "pikachu"
        and attacker.item == "lightball"
        and not is_physical
    ) or (
        attacker.species in ["cubone", "marowak"]
        and attacker.item == "thickclub"
        and is_physical
    ):
        at *= 2

    # Gen 1 overflow fix: cap stats to 8-bit range
    if at > 255 or df > 255:
        at = (at // 4) % 256
        df = (df // 4) % 256

    # Gen 2 Present has a glitched damage calculation using the secondary types of the Pokemon
    # for the Attacker's Level and Defender's Defense.
    if move.id == "present":
        lookup = {
            "NORMAL": 0,
            "FIGHTING": 1,
            "FLYING": 2,
            "POISON": 3,
            "GROUND": 4,
            "ROCK": 5,
            "BUG": 7,
            "GHOST": 8,
            "STEEL": 9,
            "???": 19,
            "FIRE": 20,
            "WATER": 21,
            "GRASS": 22,
            "ELECTRIC": 23,
            "PSYCHIC": 24,
            "ICE": 25,
            "DRAGON": 26,
            "DARK": 27,
        }

        at = 10

        attacker_type = (
            attacker.type_2 if attacker.type_2 is not None else attacker.type_1
        )
        defender_type = (
            defender.type_2 if defender.type_2 is not None else defender.type_1
        )

        df = max(lookup.get(attacker_type.name, 1), 1)
        lv = max(lookup.get(defender_type.name, 1), 1)

    if defender.name == "ditto" and defender.item == "metalpowder":
        df = math.floor(df * 1.5)

    base_damage = math.floor(
        math.floor(
            math.floor((2 * lv) / 5 + 2) * max(1, at) * move.base_power / max(1, df)
        )
        / 50
    )
    # Gen 1 handles move.isCrit above by doubling level
    if battle.gen == 2 and is_critical:
        base_damage *= 2

    # Gen 2 item handling
    if attacker.item:
        item_boost_type = get_item_boost_type(attacker.item)
    else:
        item_boost_type = None

    if move.type.name == item_boost_type:
        base_damage = math.floor(base_damage * 1.1)

    base_damage = min(997, base_damage) + 2
    if (Weather.SUNNYDAY in battle.weather and move.type == PokemonType.FIRE) or (
        Weather.RAINDANCE in battle.weather and move.type == PokemonType.WATER
    ):

        base_damage = math.floor(base_damage * 1.5)
    elif (
        (Weather.SUNNYDAY in battle.weather and move.type == PokemonType.WATER)
        or (Weather.RAINDANCE in battle.weather and move.type == PokemonType.FIRE)
        or move.id == "solarbeam"
    ):
        base_damage = math.floor(base_damage / 2)

    if any(move.type == t for t in attacker.types):
        base_damage = math.floor(base_damage * 1.5)

    if battle.gen == 1:
        base_damage = math.floor(base_damage * first_type_effectiveness)
        base_damage = math.floor(base_damage * second_type_effectiveness)
    else:
        base_damage = math.floor(base_damage * type_effectiveness)
    # Flail and Reversal don't use random factor
    if move.id in ("flail", "reversal"):
        return (base_damage, base_damage, [base_damage])

    damage_rolls: List[int] = []

    for i in range(217, 256):
        if battle.gen == 2:
            # In Gen 2, damage is always rounded up to at least 1
            dmg = max(1, math.floor((base_damage * i) / 255))
        else:
            # In Gen 1, skip random factor if base damage is 1
            if base_damage == 1:
                dmg = 1
            else:
                dmg = math.floor((base_damage * i) / 255)
        damage_rolls.append(dmg)
    if "multihit" in move.entry:
        damage_matrix = [damage_rolls]
        min_vector = []
        max_vector = []

        for times in range(1, move.n_hit[-1]):
            hit_damage: List[int] = []
            for damage_multiplier in range(217, 256):
                if battle.gen == 2:
                    new_final_damage = max(
                        1, math.floor((base_damage * damage_multiplier) / 255)
                    )
                else:
                    new_final_damage = (
                        1
                        if base_damage == 1
                        else math.floor((base_damage * damage_multiplier) / 255)
                    )

                hit_damage.append(new_final_damage)
            min_vector.append(min(hit_damage))
            max_vector.append(max(hit_damage))

            damage_matrix.append(hit_damage)
        return (min_vector, max_vector, damage_matrix)

    return (min(damage_rolls), max(damage_rolls), damage_rolls)


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

TYPE_EFFECTIVENESS_PRECEDENCE_RULES = [
    "NORMAL",
    "FIRE",
    "WATER",
    "ELECTRIC",
    "GRASS",
    "ICE",
    "FIGHTING",
    "POISON",
    "GROUND",
    "FLYING",
    "PSYCHIC",
    "BUG",
    "ROCK",
    "GHOST",
    "DRAGON",
    "DARK",
    "STEEL",
]
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


def handleFixedDamageMoves(attacker: Pokemon, move: Move):
    if move.entry["damage"] == "level":
        return attacker.level
    else:
        return move.entry["damage"]


def get_move_effectiveness(
    gen: int,
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
    elif move.id == "struggle" and gen > 1:
        return 1
    elif is_gravity and type == PokemonType.FLYING and move_type == PokemonType.GROUND:
        return 1
    elif move.id == "freezedry" and type == PokemonType.WATER:
        return 2
    else:
        effectiveness = PokemonType.damage_multiplier(
            move_type, type, type_chart=GenData.from_gen(gen).type_chart
        )
        if effectiveness == 0 and is_ring_target:
            effectiveness = 1
        if move.id == "flyingpress":
            effectiveness *= PokemonType.damage_multiplier(
                PokemonType.FLYING, type, type_chart=GenData.from_gen(gen).type_chart
            )
        return effectiveness


def get_item_boost_type(item: str) -> Optional[str]:
    item_type_map = {
        "dracoplate": "DRAGON",
        "dragonfang": "undefined",
        "dragonscale": "DRAGON",
        "dreadplate": "DARK",
        "blackglasses": "DARK",
        "earthplate": "GROUND",
        "softsand": "GROUND",
        "fistplate": "FIGHTING",
        "blackbelt": "FIGHTING",
        "flameplate": "FIRE",
        "charcoal": "FIRE",
        "icicleplate": "ICE",
        "nevermeltice": "ICE",
        "insectplate": "BUG",
        "silverpowder": "BUG",
        "ironplate": "STEEL",
        "metalcoat": "STEEL",
        "meadowplate": "GRASS",
        "roseincense": "GRASS",
        "miracleseed": "GRASS",
        "mindplate": "PSYCHIC",
        "oddincense": "PSYCHIC",
        "twistedspoon": "PSYCHIC",
        "fairyfeather": "FAIRY",
        "pixieplate": "FAIRY",
        "skyplate": "FLYING",
        "sharpbeak": "FLYING",
        "splashplate": "WATER",
        "seaincense": "WATER",
        "waveincense": "WATER",
        "mysticwater": "WATER",
        "spookyplate": "GHOST",
        "spelltag": "GHOST",
        "stoneplate": "ROCK",
        "rockincense": "ROCK",
        "hardstone": "ROCK",
        "toxicplate": "POISON",
        "poisonbarb": "POISON",
        "zapplate": "ELECTRIC",
        "magnet": "ELECTRIC",
        "silkscarf": "NORMAL",
        "pinkbow": "NORMAL",
        "polkadotbow": "NORMAL",
    }

    return item_type_map.get(item)
