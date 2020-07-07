# -*- coding: utf-8 -*-
"""This module contains utilies to convert to raw stats based on species, level, nature, EVs and IVs.
"""

import math
from typing import List, Any

from poke_env.data import POKEDEX, STATS_TO_IDX, NATURES

StatList = List[int]


def _raw_stat(base: int, ev: int, iv: int, level: int, nature_multiplier: float) -> int:
    """ Converts to raw stat
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


def _raw_hp(base: int, ev: int, iv: int, level: int) -> int:
    """ Converts to raw hp
        :param base: the base stat
        :param ev: HP Effort Value (EV)
        :param iv: HP Individual Value (IV)
        :param level: pokemon level
        :return: the raw hp
    """
    s = math.floor((math.floor(ev / 4) + iv + 2 * base) * level / 100) + level + 10
    return int(s)


def get_raw_stats(
    species: str, evs: StatList, ivs: StatList, level: int, nature: str
) -> StatList:
    """ Converts to raw stats
    :param species: pokemon species
    :param evs: list of pokemon's EVs (size 6)
    :param ivs: list of pokemon's IVs (size 6)
    :param level: pokemon level
    :param nature: pokemon nature
    :return: the raw stats in order [hp, atk, def, spa, spd, spe]
    """

    assert len(evs) == 6
    assert len(ivs) == 6

    base_stats = [0] * 6
    for stat, value in POKEDEX[species]["baseStats"].items():
        if stat in STATS_TO_IDX:
            base_stats[STATS_TO_IDX[stat]] = value

    nature_multiplier = [1] * 6
    for stat, multiplier in NATURES[nature].items():
        if stat in STATS_TO_IDX:
            nature_multiplier[STATS_TO_IDX[stat]] = multiplier

    raw_stats = [0] * 6
    raw_stats[0] = _raw_hp(base_stats[0], evs[0], ivs[0], level)
    for i in range(1, 6):
        raw_stats[i] = _raw_stat(
            base_stats[i], evs[i], ivs[i], level, nature_multiplier[i]
        )

    return raw_stats
