# -*- coding: utf-8 -*-

from poke_env.utils import to_id_str, get_raw_stats


def test_amoonguss_raw_stats_match_actual_stats():

    species = to_id_str("Amoonguss")
    nature = to_id_str("Timid")
    evs = [68, 0, 0, 0, 188, 252]
    ivs = [31, 0, 31, 31, 31, 31]
    level = 50

    actual_stats = [198, 81, 90, 105, 124, 90]
    raw_stats = get_raw_stats(species, evs, ivs, level, nature)

    assert actual_stats == raw_stats


def test_incineroar_raw_stats_match_actual_stats():
    species = to_id_str("Incineroar")
    nature = to_id_str("Adamant")
    evs = [252, 116, 0, 0, 140, 0]
    ivs = [31, 31, 31, 31, 31, 28]
    level = 50

    actual_stats = [202, 165, 110, 90, 128, 79]
    raw_stats = get_raw_stats(species, evs, ivs, level, nature)

    assert actual_stats == raw_stats


def test_togedemaru_raw_stats_match_actual_stats():
    species = to_id_str("Togedemaru")
    nature = to_id_str("Hasty")
    evs = [0, 252, 0, 0, 4, 252]
    ivs = [22, 31, 0, 0, 31, 31]
    level = 100

    actual_stats = [262, 295, 117, 85, 183, 320]
    raw_stats = get_raw_stats(species, evs, ivs, level, nature)

    assert actual_stats == raw_stats
