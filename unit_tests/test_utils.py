# -*- coding: utf-8 -*-

from poke_env.utils import to_id_str, compute_raw_stats
from poke_env.player_configuration import _create_player_configuration_from_player


def test_amoonguss_raw_stats_match_actual_stats():
    species = to_id_str("Amoonguss")
    nature = to_id_str("Timid")
    evs = [68, 0, 0, 0, 188, 252]
    ivs = [31, 0, 31, 31, 31, 31]
    level = 50

    actual_stats = [198, 81, 90, 105, 124, 90]
    raw_stats = compute_raw_stats(species, evs, ivs, level, nature)

    assert actual_stats == raw_stats


def test_incineroar_raw_stats_match_actual_stats():
    species = to_id_str("Incineroar")
    nature = to_id_str("Adamant")
    evs = [252, 116, 0, 0, 140, 0]
    ivs = [31, 31, 31, 31, 31, 28]
    level = 50

    actual_stats = [202, 165, 110, 90, 128, 79]
    raw_stats = compute_raw_stats(species, evs, ivs, level, nature)

    assert actual_stats == raw_stats


def test_togedemaru_raw_stats_match_actual_stats():
    species = to_id_str("Togedemaru")
    nature = to_id_str("Hasty")
    evs = [0, 252, 0, 0, 4, 252]
    ivs = [22, 31, 0, 0, 31, 31]
    level = 100

    actual_stats = [262, 295, 117, 85, 183, 320]
    raw_stats = compute_raw_stats(species, evs, ivs, level, nature)

    assert actual_stats == raw_stats


def test_blissey_raw_stats_match_actual_stats():
    species = to_id_str("Blissey")
    nature = to_id_str("Timid")
    evs = [252, 0, 4, 0, 0, 252]
    ivs = [31, 31, 31, 31, 31, 31]
    level = 100

    actual_stats = [714, 50, 57, 186, 306, 229]
    raw_stats = compute_raw_stats(species, evs, ivs, level, nature)

    assert actual_stats == raw_stats


def test_shedinja_raw_stats_match_actual_stats():
    species = to_id_str("Shedinja")
    nature = to_id_str("Adamant")
    evs = [0, 252, 4, 0, 0, 252]
    ivs = [31, 31, 31, 31, 31, 31]

    level = 50
    actual_stats = [1, 156, 66, 45, 50, 92]
    raw_stats = compute_raw_stats(species, evs, ivs, level, nature)
    assert actual_stats == raw_stats

    level = 100
    actual_stats = [1, 306, 127, 86, 96, 179]
    raw_stats = compute_raw_stats(species, evs, ivs, level, nature)
    assert actual_stats == raw_stats


def test_player_configuration_auto_naming():
    class ShortPlayer:
        pass

    class VeryLongPlayerClassName:
        pass

    assert (
        _create_player_configuration_from_player(ShortPlayer()).username
        == "ShortPlayer 1"
    )
    assert (
        _create_player_configuration_from_player(ShortPlayer()).username
        == "ShortPlayer 2"
    )
    assert (
        _create_player_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 1"
    )
    assert (
        _create_player_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 2"
    )
    assert (
        _create_player_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 3"
    )
    assert (
        _create_player_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 4"
    )
    assert (
        _create_player_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 5"
    )
    assert (
        _create_player_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 6"
    )
    assert (
        _create_player_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 7"
    )
    assert (
        _create_player_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 8"
    )
    assert (
        _create_player_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerCl 9"
    )
    assert (
        _create_player_configuration_from_player(VeryLongPlayerClassName()).username
        == "VeryLongPlayerC 10"
    )
