"""This module contains utility functions and objects related to stats."""

import math
from typing import List

from poke_env.data import GenData

STATS_TO_IDX = {
    "hp": 0,
    "atk": 1,
    "def": 2,
    "spa": 3,
    "spd": 4,
    "spe": 5,
    "satk": 3,
    "sdef": 4,
}


def _raw_stat(base: int, ev: int, iv: int, level: int, nature_multiplier: float) -> int:
    """Converts to raw stat
    :param base: the base stat
    :param ev: Stat Effort Value (EV)
    :param iv: Stat Individual Values (IV)
    :param level: pokemon level
    :param nature_multiplier: stat multiplier of the nature (either 0.9, 1 or 1.1)
    :return: the raw stat
    """
    s = math.floor(
        (5 + math.floor((math.floor(ev / 4) + iv + 2 * base) * level / 100))
        * nature_multiplier
    )
    return int(s)


def _raw_stat_dv(base: int, dv: int, level: int) -> int:
    """Converts to raw stat using dvs instead of ivs. EVs are not included as they are assumed to be maxed out.
    :param base: the base stat
    :param dv: Stat Determinant Values (DV)
    :param level: pokemon level
    :return: the raw stat
    """
    s = math.floor((((base + dv) * 2 + 63) * level) / 100) + 5
    return int(s)


def _raw_hp(base: int, ev: int, iv: int, level: int) -> int:
    """Converts to raw hp
    :param base: the base stat
    :param ev: HP Effort Value (EV)
    :param iv: HP Individual Value (IV)
    :param level: pokemon level
    :return: the raw hp
    """
    s = math.floor((math.floor(ev / 4) + iv + 2 * base) * level / 100) + level + 10
    return int(s)


def _raw_hp_dv(base: int, dv: int, level: int) -> int:
    """Converts to raw hp using DV's instead of IV's. This is for generation 1 and 2. (Note that max evs are used)
    :param base: the base stat
    :param iv: HP Determinant Value (DV)
    :param level: pokemon level
    :return: the raw hp
    """
    s = math.floor((((base + dv) * 2 + 63) * level) / 100) + level + 10
    return int(s)


def compute_raw_stats(
    species: str, evs: List[int], ivs: List[int], level: int, nature: str, data: GenData
) -> List[int]:
    """Compute raw stats for a Pokémon.

    :param species: Pokémon species.
    :param evs: List of EV values (size 6).
    :param ivs: List of IV values (size 6).
    :param level: Pokémon level.
    :param nature: Pokémon nature.
    :param data: ``GenData`` instance providing Pokédex information.
    :return: Raw stats as ``[hp, atk, def, spa, spd, spe]``.
    """

    assert len(evs) == 6
    assert len(ivs) == 6

    base_stats = [0] * 6
    for stat, value in data.pokedex[species]["baseStats"].items():
        base_stats[STATS_TO_IDX[stat]] = value

    nature_multiplier = [1.0] * 6
    for stat, multiplier in data.natures[nature].items():
        if stat != "num":
            nature_multiplier[STATS_TO_IDX[stat]] = multiplier

    raw_stats = [0] * 6

    if species == "shedinja":
        raw_stats[0] = 1
    else:
        raw_stats[0] = _raw_hp(base_stats[0], evs[0], ivs[0], level)

    for i in range(1, 6):
        raw_stats[i] = _raw_stat(
            base_stats[i], evs[i], ivs[i], level, nature_multiplier[i]
        )

    return raw_stats


def compute_raw_stats_dvs(
    species: str, dvs: List[int], level: int, data: GenData
) -> List[int]:
    """Compute raw stats for a Pokémon in gen 1 or 2 as calculation for those generations is different. EV's are not included as they are assumed to be maxed out.

    :param species: Pokémon species.
    :param evs: List of EV values (size 6).
    :param dvs: List of DV values (size 6).
    :param level: Pokémon level.
    :param data: ``GenData`` instance providing Pokédex information.
    :return: Raw stats as ``[hp, atk, def, spa, spd, spe]``.
    """

    assert len(dvs) == 6

    base_stats = [0] * 6
    for stat, value in data.pokedex[species]["baseStats"].items():
        base_stats[STATS_TO_IDX[stat]] = value

    raw_stats = [0] * 6

    raw_stats[0] = _raw_hp_dv(base_stats[0], dvs[0], level)

    for i in range(1, 6):
        raw_stats[i] = _raw_stat_dv(base_stats[i], dvs[i], level)

    return raw_stats
