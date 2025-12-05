import logging

from poke_env.battle import Battle, Move, Pokemon
from poke_env.battle.side_condition import SideCondition
from poke_env.calc.damage_calc_gen1_2 import calculate_damage_gen12
from poke_env.stats import compute_raw_stats_dvs


def create_battle(
    gen,
    p1a: Pokemon = Pokemon(2, species="furret", name="?"),
    p2a: Pokemon = Pokemon(2, species="furret", name="??"),
) -> Battle:

    if gen == 1:

        battle = Battle("tag", "elitekangaskhanai", logging.Logger(""), gen=gen)
    else:
        battle = Battle("tag", "elitefurretai", logging.Logger(""), gen=gen)
    battle._format = f"gen{gen}ou"
    battle.player_role = "p1"
    battle._team = {f"p1: {p1a.name}": p1a}
    battle._opponent_team = {f"p2: {p2a.name}": p2a}
    for mon in [p1a, p2a]:
        if any(map(lambda x: x is None, mon.stats.values())):
            mon.stats = {
                k: v
                for k, v in zip(
                    ["hp", "atk", "def", "spa", "spd", "spe"],
                    compute_raw_stats_dvs(mon.species, [15] * 6, mon.level, mon._data),
                )
            }
    for position, mon in zip(["p1", "p2"], [p1a, p2a]):
        battle.switch(
            f"{position}: {mon.name}",
            f"{mon.species}, L{mon.level}",
            f"{mon.current_hp}/{mon.max_hp}",
        )
    return battle


def test_base_cases_singles():

    # gen 1
    attacker = Pokemon(1, species="kangaskhan", name="mon1")
    attacker._level = 50
    defender = Pokemon(1, species="kangaskhan", name="mon2")
    defender._level = 100
    battle = create_battle(1, p1a=attacker, p2a=defender)

    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("doubleedge", gen=1), battle
    ) == (
        33,
        39,
        [
            33,
            33,
            33,
            33,
            33,
            33,
            34,
            34,
            34,
            34,
            34,
            34,
            35,
            35,
            35,
            35,
            35,
            35,
            35,
            36,
            36,
            36,
            36,
            36,
            36,
            37,
            37,
            37,
            37,
            37,
            37,
            37,
            38,
            38,
            38,
            38,
            38,
            38,
            39,
        ],
    )

    assert calculate_damage_gen12(
        defender_ident, attacker_ident, Move("doubleedge", gen=1), battle
    ) == (
        243,
        286,
        [
            243,
            244,
            245,
            246,
            247,
            248,
            250,
            251,
            252,
            253,
            254,
            255,
            256,
            257,
            259,
            260,
            261,
            262,
            263,
            264,
            265,
            266,
            268,
            269,
            270,
            271,
            272,
            273,
            274,
            275,
            277,
            278,
            279,
            280,
            281,
            282,
            283,
            284,
            286,
        ],
    )
    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("doubleedge", gen=1),
        battle,
        is_critical=True,
    ) == (
        62,
        73,
        [
            62,
            62,
            62,
            62,
            63,
            63,
            63,
            64,
            64,
            64,
            64,
            65,
            65,
            65,
            66,
            66,
            66,
            66,
            67,
            67,
            67,
            68,
            68,
            68,
            68,
            69,
            69,
            69,
            70,
            70,
            70,
            70,
            71,
            71,
            71,
            72,
            72,
            72,
            73,
        ],
    )

    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("surf", gen=1), battle
    ) == (
        19,
        23,
        [
            19,
            19,
            19,
            19,
            19,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            21,
            21,
            21,
            21,
            21,
            21,
            21,
            21,
            21,
            21,
            21,
            22,
            22,
            22,
            22,
            22,
            22,
            22,
            22,
            22,
            22,
            22,
            23,
        ],
    )

    # gen 2

    attacker = Pokemon(2, species="furret", name="mon1")
    attacker._level = 50
    defender = Pokemon(2, species="furret", name="mon2")
    defender._level = 100
    battle = create_battle(2, p1a=attacker, p2a=defender)

    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("doubleedge", gen=2), battle
    ) == (
        39,
        46,
        [
            39,
            39,
            39,
            39,
            39,
            40,
            40,
            40,
            40,
            40,
            40,
            41,
            41,
            41,
            41,
            41,
            42,
            42,
            42,
            42,
            42,
            42,
            43,
            43,
            43,
            43,
            43,
            44,
            44,
            44,
            44,
            44,
            44,
            45,
            45,
            45,
            45,
            45,
            46,
        ],
    )

    assert calculate_damage_gen12(
        defender_ident, attacker_ident, Move("doubleedge", gen=2), battle
    ) == (
        281,
        331,
        [
            281,
            282,
            284,
            285,
            286,
            288,
            289,
            290,
            292,
            293,
            294,
            295,
            297,
            298,
            299,
            301,
            302,
            303,
            305,
            306,
            307,
            308,
            310,
            311,
            312,
            314,
            315,
            316,
            318,
            319,
            320,
            321,
            323,
            324,
            325,
            327,
            328,
            329,
            331,
        ],
    )

    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("doubleedge", gen=2),
        battle,
        is_critical=True,
    ) == (
        76,
        90,
        [
            76,
            76,
            77,
            77,
            78,
            78,
            78,
            79,
            79,
            79,
            80,
            80,
            80,
            81,
            81,
            81,
            82,
            82,
            82,
            83,
            83,
            84,
            84,
            84,
            85,
            85,
            85,
            86,
            86,
            86,
            87,
            87,
            87,
            88,
            88,
            88,
            89,
            89,
            90,
        ],
    )
    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("surf", gen=2), battle
    ) == (
        17,
        21,
        [
            17,
            17,
            18,
            18,
            18,
            18,
            18,
            18,
            18,
            18,
            18,
            18,
            18,
            18,
            19,
            19,
            19,
            19,
            19,
            19,
            19,
            19,
            19,
            19,
            19,
            19,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            21,
        ],
    )


def test_fixed_damage():

    # Gen 1 (seismic toss/night shade should not be affected by types and should ignore immunities)
    attacker = Pokemon(1, species="alakazam")
    attacker._level = 50
    defender = Pokemon(1, species="gengar")
    defender._level = 50
    battle = create_battle(1, p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("seismictoss", gen=1), battle
    ) == (50, 50, [50])
    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("nightshade", gen=1), battle
    ) == (50, 50, [50])

    # Gen 1/2 Constant Damage moves: verify that moves that are fixed and not level dependent work properly.
    attacker = Pokemon(1, species="dragonite")
    attacker._level = 50
    defender = Pokemon(1, species="dragonite")
    defender._level = 50
    battle = create_battle(1, p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("dragonrage", gen=1), battle
    ) == (40, 40, [40])

    # Gen 2 Seismic Toss/Night Shade, weaknesses and resistances are still ignored, but immunities are no longer ignored

    attacker = Pokemon(2, species="alakazam")
    attacker._level = 50
    defender = Pokemon(2, species="gengar")
    defender._level = 50
    battle = create_battle(2, p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("seismictoss", gen=2), battle
    ) == (0, 0, [0])
    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("nightshade", gen=2), battle
    ) == (50, 50, [50])


def test_immunity():
    attacker = Pokemon(1, species="snorlax")
    defender = Pokemon(1, species="gengar")
    battle = create_battle(1, p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("hyperbeam", gen=1), battle
    ) == (0, 0.0, [0])


def test_struggle():
    attacker = Pokemon(2, species="mew")
    defender = Pokemon(2, species="gengar")
    battle = create_battle(2, p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("struggle", gen=9), battle
    ) == (
        50,
        59,
        [
            50,
            50,
            50,
            50,
            51,
            51,
            51,
            51,
            52,
            52,
            52,
            52,
            52,
            53,
            53,
            53,
            53,
            54,
            54,
            54,
            54,
            55,
            55,
            55,
            55,
            55,
            56,
            56,
            56,
            56,
            57,
            57,
            57,
            57,
            58,
            58,
            58,
            58,
            59,
        ],
    )


def test_explosion():

    attacker = Pokemon(2, species="mew")
    defender = Pokemon(2, species="vulpix")
    battle = create_battle(2, p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")
    assert calculate_damage_gen12(
        attacker_ident, defender_ident, Move("explosion", gen=2), battle
    ) == (
        602,
        708,
        [
            602,
            605,
            608,
            610,
            613,
            616,
            619,
            621,
            624,
            627,
            630,
            633,
            635,
            638,
            641,
            644,
            646,
            649,
            652,
            655,
            658,
            660,
            663,
            666,
            669,
            671,
            674,
            677,
            680,
            683,
            685,
            688,
            691,
            694,
            696,
            699,
            702,
            705,
            708,
        ],
    )


def test_ignore_mods():

    # gen 1
    attacker = Pokemon(1, species="mew")
    defender = Pokemon(1, species="vulpix")
    battle = create_battle(1, p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    attacker.set_hp_status("100/100 brn")
    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("bodyslam", gen=1),
        battle,
        is_critical=True,
    ) == (
        200,
        236,
        [
            200,
            201,
            202,
            203,
            204,
            205,
            206,
            207,
            208,
            209,
            210,
            211,
            211,
            212,
            213,
            214,
            215,
            216,
            217,
            218,
            219,
            220,
            221,
            222,
            223,
            223,
            224,
            225,
            226,
            227,
            228,
            229,
            230,
            231,
            232,
            233,
            234,
            235,
            236,
        ],
    )
    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("bodyslam", gen=1),
        battle,
        is_critical=False,
    ) == (
        51,
        61,
        [
            51,
            52,
            52,
            52,
            52,
            53,
            53,
            53,
            53,
            54,
            54,
            54,
            54,
            55,
            55,
            55,
            55,
            55,
            56,
            56,
            56,
            56,
            57,
            57,
            57,
            57,
            58,
            58,
            58,
            58,
            59,
            59,
            59,
            59,
            60,
            60,
            60,
            60,
            61,
        ],
    )
    battle._side_conditions = {SideCondition.REFLECT: 1}
    battle._opponent_side_conditions = {SideCondition.REFLECT: 1}
    attacker.cure_status()

    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("bodyslam", gen=1),
        battle,
        is_critical=True,
    ) == (
        200,
        236,
        [
            200,
            201,
            202,
            203,
            204,
            205,
            206,
            207,
            208,
            209,
            210,
            211,
            211,
            212,
            213,
            214,
            215,
            216,
            217,
            218,
            219,
            220,
            221,
            222,
            223,
            223,
            224,
            225,
            226,
            227,
            228,
            229,
            230,
            231,
            232,
            233,
            234,
            235,
            236,
        ],
    )

    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("bodyslam", gen=1),
        battle,
        is_critical=False,
    ) == (
        51,
        61,
        [
            51,
            52,
            52,
            52,
            52,
            53,
            53,
            53,
            53,
            54,
            54,
            54,
            54,
            55,
            55,
            55,
            55,
            55,
            56,
            56,
            56,
            56,
            57,
            57,
            57,
            57,
            58,
            58,
            58,
            58,
            59,
            59,
            59,
            59,
            60,
            60,
            60,
            60,
            61,
        ],
    )
    attacker.boosts["atk"] = 2
    defender.boosts["def"] = 3
    battle._side_conditions = {}
    battle._opponent_side_conditions = {}
    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("bodyslam", gen=1),
        battle,
        is_critical=True,
    ) == (
        200,
        236,
        [
            200,
            201,
            202,
            203,
            204,
            205,
            206,
            207,
            208,
            209,
            210,
            211,
            211,
            212,
            213,
            214,
            215,
            216,
            217,
            218,
            219,
            220,
            221,
            222,
            223,
            223,
            224,
            225,
            226,
            227,
            228,
            229,
            230,
            231,
            232,
            233,
            234,
            235,
            236,
        ],
    )

    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("bodyslam", gen=1),
        battle,
        is_critical=False,
    ) == (
        82,
        97,
        [
            82,
            82,
            83,
            83,
            84,
            84,
            84,
            85,
            85,
            85,
            86,
            86,
            87,
            87,
            87,
            88,
            88,
            89,
            89,
            89,
            90,
            90,
            90,
            91,
            91,
            92,
            92,
            92,
            93,
            93,
            93,
            94,
            94,
            95,
            95,
            95,
            96,
            96,
            97,
        ],
    )

    # gen 2
    attacker = Pokemon(2, species="mew")
    defender = Pokemon(2, species="vulpix")
    battle = create_battle(2, p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")
    attacker.boosts["atk"] = 3
    defender.boosts["def"] = 2

    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("bodyslam", gen=2),
        battle,
        is_critical=True,
    ) == (
        255,
        300,
        [
            255,
            256,
            257,
            258,
            260,
            261,
            262,
            263,
            264,
            265,
            267,
            268,
            269,
            270,
            271,
            272,
            274,
            275,
            276,
            277,
            278,
            280,
            281,
            282,
            283,
            284,
            285,
            287,
            288,
            289,
            290,
            291,
            292,
            294,
            295,
            296,
            297,
            298,
            300,
        ],
    )
    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("bodyslam", gen=2),
        battle,
        is_critical=False,
    ) == (
        128,
        151,
        [
            128,
            129,
            129,
            130,
            130,
            131,
            132,
            132,
            133,
            133,
            134,
            135,
            135,
            136,
            136,
            137,
            137,
            138,
            139,
            139,
            140,
            140,
            141,
            142,
            142,
            143,
            143,
            144,
            145,
            145,
            146,
            146,
            147,
            148,
            148,
            149,
            149,
            150,
            151,
        ],
    )

    attacker.boosts["atk"] = 2
    defender.boosts["def"] = 3

    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("bodyslam", gen=2),
        battle,
        is_critical=True,
    ) == (
        205,
        242,
        [
            205,
            206,
            207,
            208,
            209,
            210,
            211,
            212,
            213,
            214,
            215,
            216,
            217,
            218,
            219,
            220,
            221,
            222,
            223,
            223,
            224,
            225,
            226,
            227,
            228,
            229,
            230,
            231,
            232,
            233,
            234,
            235,
            236,
            237,
            238,
            239,
            240,
            241,
            242,
        ],
    )
    assert calculate_damage_gen12(
        attacker_ident,
        defender_ident,
        Move("bodyslam", gen=2),
        battle,
        is_critical=False,
    ) == (
        82,
        97,
        [
            82,
            82,
            83,
            83,
            84,
            84,
            84,
            85,
            85,
            85,
            86,
            86,
            87,
            87,
            87,
            88,
            88,
            89,
            89,
            89,
            90,
            90,
            90,
            91,
            91,
            92,
            92,
            92,
            93,
            93,
            93,
            94,
            94,
            95,
            95,
            95,
            96,
            96,
            97,
        ],
    )
