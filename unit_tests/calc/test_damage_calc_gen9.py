import logging
from typing import Union

from poke_env.battle import Battle, DoubleBattle, Move, Pokemon
from poke_env.calc.damage_calc_gen9 import calculate_base_power, calculate_damage
from poke_env.data import GenData
from poke_env.stats import compute_raw_stats
from poke_env.teambuilder import Teambuilder


def create_battle(
    p1a: Pokemon = Pokemon(9, species="furret", name="?"),
    p2a: Pokemon = Pokemon(9, species="furret", name="??"),
    p1b: Pokemon = Pokemon(9, species="furret", name="???"),
    p2b: Pokemon = Pokemon(9, species="furret", name="????"),
    doubles: bool = True,
) -> Union[DoubleBattle, Battle]:
    if doubles:
        battle = DoubleBattle("tag", "elitefurretai", logging.Logger("example"), gen=9)

        battle._format = "gen9vgc2023regulationc"
        battle.player_role = "p1"

        battle._team = {f"p1: {p1a.name}": p1a, f"p1: {p1b.name}": p1b}
        battle._opponent_team = {f"p2: {p2a.name}": p2a, f"p2: {p2b.name}": p2b}

        for mon in [p1a, p1b, p2a, p2b]:
            if any(map(lambda x: x is None, mon.stats.values())):
                mon.stats = {
                    k: v
                    for k, v in zip(
                        ["hp", "atk", "def", "spa", "spd", "spe"],
                        compute_raw_stats(
                            mon.species,
                            [0] * 6,
                            [31] * 6,
                            mon.level,
                            "serious",
                            GenData.from_gen(battle.gen),
                        ),
                    )
                }

        for position, mon in zip(["p1a", "p1b", "p2a", "p2b"], [p1a, p1b, p2a, p2b]):
            battle.switch(
                f"{position}: {mon.name}",
                f"{mon.species}, L{mon.level}",
                f"{mon.current_hp}/{mon.max_hp}",
            )

        return battle

    else:
        battle = Battle("tag", "elitefurretai", logging.Logger(""), gen=9)
        battle._format = "gen9ou"
        battle.player_role = "p1"
        battle._team = {f"p1: {p1a.name}": p1a}
        battle._opponent_team = {f"p2: {p2a.name}": p2a}
        for mon in [p1a, p2a]:
            if any(map(lambda x: x is None, mon.stats.values())):
                mon.stats = {
                    k: v
                    for k, v in zip(
                        ["hp", "atk", "def", "spa", "spd", "spe"],
                        compute_raw_stats(
                            mon.species,
                            [0] * 6,
                            [31] * 6,
                            mon.level,
                            "serious",
                            GenData.from_gen(battle.gen),
                        ),
                    )
                }
        for position, mon in zip(["p1", "p2"], [p1a, p2a]):
            battle.switch(
                f"{position}: {mon.name}",
                f"{mon.species}, L{mon.level}",
                f"{mon.current_hp}/{mon.max_hp}",
            )
        return battle


def test_base_cases():
    attacker = Pokemon(9, species="furret", name="mon1")
    attacker._level = 50
    defender = Pokemon(9, species="furret", name="mon2")
    defender._level = 100
    defender2 = Pokemon(9, species="furret", name="mon3")
    defender2._level = 50
    battle = create_battle(p1a=attacker, p2a=defender, p2b=defender2)

    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("doubleedge", gen=9), battle
    ) == (40, 48)
    assert calculate_damage(
        defender_ident, attacker_ident, Move("doubleedge", gen=9), battle
    ) == (288, 340)
    assert calculate_damage(
        attacker_ident,
        defender_ident,
        Move("doubleedge", gen=9),
        battle,
        is_critical=True,
    ) == (60, 72)
    assert calculate_damage(
        attacker_ident, defender_ident, Move("surf", gen=9), battle
    ) == (11, 14)

    defender2.set_hp_status("0 fnt")
    assert calculate_damage(
        attacker_ident, defender_ident, Move("surf", gen=9), battle
    ) == (16, 19)


def test_base_cases_singles():
    attacker = Pokemon(9, species="furret", name="mon1")
    attacker._level = 50
    defender = Pokemon(9, species="furret", name="mon2")
    defender._level = 100
    defender2 = Pokemon(9, species="furret", name="mon3")
    defender2._level = 50
    battle = create_battle(p1a=attacker, p2a=defender, doubles=False)

    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("doubleedge", gen=9), battle
    ) == (40, 48)
    assert calculate_damage(
        defender_ident, attacker_ident, Move("doubleedge", gen=9), battle
    ) == (288, 340)
    assert calculate_damage(
        attacker_ident,
        defender_ident,
        Move("doubleedge", gen=9),
        battle,
        is_critical=True,
    ) == (60, 72)
    assert calculate_damage(
        attacker_ident, defender_ident, Move("surf", gen=9), battle
    ) == (16, 19)


def test_grassknot():
    attacker = Pokemon(9, species="Groudon")
    defender = Pokemon(9, species="Groudon")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("grassknot", gen=9), battle
    ) == (190, 224)


def test_judgment():
    attacker = Pokemon(9, species="Arceus")
    defender = Pokemon(9, species="Blastoise")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("judgment", gen=9), battle
    ) == (121, 144)


def test_seismic_toss_and_night_shade():
    attacker = Pokemon(9, details="Mew, L50, M")
    defender = Pokemon(9, species="Vulpix")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("seismictoss", gen=9), battle
    ) == (50, 50)
    assert calculate_damage(
        attacker_ident, defender_ident, Move("nightshade", gen=9), battle
    ) == (50, 50)


def test_immunity():
    attacker = Pokemon(9, species="Snorlax")
    defender = Pokemon(9, species="Gengar")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("hyperbeam", gen=9), battle
    ) == (0, 0)


def test_non_damaging():
    attacker = Pokemon(9, species="Snorlax")
    defender = Pokemon(9, species="Vulpix")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("barrier", gen=9), battle
    ) == (0, 0)


def test_protect():
    attacker = Pokemon(9, species="Snorlax")
    defender = Pokemon(9, species="Chansey")
    defender.start_effect("protect")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("hyperbeam", gen=9), battle
    ) == (0, 0)


def test_critical_ignore():
    attacker = Pokemon(9, species="mew")
    defender = Pokemon(9, species="vulpix")
    explosion = Move("explosion", gen=9)
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, explosion, battle, is_critical=False
    ) == (273, 322)
    assert calculate_damage(
        attacker_ident, defender_ident, explosion, battle, is_critical=True
    ) == (410, 483)

    attacker.set_hp_status("100/100 brn")
    assert calculate_damage(
        attacker_ident, defender_ident, explosion, battle, is_critical=False
    ) == (136, 161)
    assert calculate_damage(
        attacker_ident, defender_ident, explosion, battle, is_critical=True
    ) == (205, 241)

    battle.parse_message(["", "-sidestart", "p2: Vulpix", "move: Reflect"])
    assert calculate_damage(
        attacker_ident, defender_ident, explosion, battle, is_critical=False
    ) == (91, 107)
    assert calculate_damage(
        attacker_ident, defender_ident, explosion, battle, is_critical=True
    ) == (205, 241)

    attacker.boosts["atk"] = 2
    defender.boosts["def"] = 2
    assert calculate_damage(
        attacker_ident, defender_ident, explosion, battle, is_critical=True
    ) == (409, 481)
    assert calculate_damage(
        attacker_ident, defender_ident, explosion, battle, is_critical=False
    ) == (91, 107)


def test_struggle():
    attacker = Pokemon(9, species="mew")
    defender = Pokemon(9, species="gengar")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("struggle", gen=9), battle
    ) == (55, 65)

    attacker.terastallize("Normal")
    assert calculate_damage(
        attacker_ident, defender_ident, Move("struggle", gen=9), battle
    ) == (55, 65)


def test_weather_ball():
    attacker = Pokemon(9, species="altaria")
    defender = Pokemon(9, species="bulbasaur")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("weatherball", gen=9), battle
    ) == (39, 46)

    battle.parse_message(["", "-weather", "SunnyDay", "[from] move: Sunny Day"])
    assert calculate_damage(
        attacker_ident, defender_ident, Move("weatherball", gen=9), battle
    ) == (230, 272)

    battle.parse_message(["", "-weather", "RainDance", "[from] move: Rain Dance"])
    assert calculate_damage(
        attacker_ident, defender_ident, Move("weatherball", gen=9), battle
    ) == (57, 68)

    battle.parse_message(["", "-weather", "Sandstorm", "[from] move: Sandstorm"])
    assert calculate_damage(
        attacker_ident, defender_ident, Move("weatherball", gen=9), battle
    ) == (77, 91)

    battle.parse_message(["", "-weather", "Snow", "[from] move: Snowscape"])
    assert calculate_damage(
        attacker_ident, defender_ident, Move("weatherball", gen=9), battle
    ) == (154, 182)


def test_flying_press():
    attacker = Pokemon(9, species="hawlucha")
    defender = Pokemon(9, species="cacturne")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("flyingpress", gen=9), battle
    ) == (612, 720)

    defender = Pokemon(9, species="spiritomb")
    battle = create_battle(p1a=attacker, p2a=defender)
    defender_ident = defender.identifier("p2")
    assert calculate_damage(
        attacker_ident, defender_ident, Move("flyingpress", gen=9), battle
    ) == (0, 0)

    attacker.temporary_ability = "scrappy"
    assert calculate_damage(
        attacker_ident, defender_ident, Move("flyingpress", gen=9), battle
    ) == (188, 224)
    defender.item = "ringtarget"
    assert calculate_damage(
        attacker_ident, defender_ident, Move("flyingpress", gen=9), battle
    ) == (188, 224)


def test_thousand_arrows():
    attacker = Pokemon(9, species="zygarde")
    defender = Pokemon(9, species="swellow")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("thousandarrows", gen=9), battle
    ) == (109, 130)


def test_ringtarget_negate_type_nullifiers():
    attacker = Pokemon(9, species="mew")
    defender = Pokemon(9, species="skarmory")
    defender.item = "ringtarget"
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("sludgebomb", gen=9), battle
    ) == (87, 103)
    assert calculate_damage(
        attacker_ident, defender_ident, Move("earthpower", gen=9), battle
    ) == (174, 206)


def test_iron_ball():
    defender = Pokemon(9, species="zapdos")
    defender.item = "ironball"
    attacker = Pokemon(9, species="vibrava")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("earthquake", gen=9), battle
    ) == (69, 82)

    attacker = Pokemon(9, species="poliwrath")
    defender = Pokemon(9, species="mismagius")
    defender.item = "ironball"
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")
    assert calculate_damage(
        attacker_ident, defender_ident, Move("mudshot", gen=9), battle
    ) == (29, 35)


def test_multiscsale_and_shadow_shield():
    defender = Pokemon(9, species="dragonite")
    defender.set_hp_status("100/100")
    defender.ability = "shadowshield"
    attacker = Pokemon(9, species="abomasnow")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("blizzard", gen=9), battle
    ) == (168, 198)

    defender.ability = "multiscale"
    defender.set_hp_status("60/100")
    assert calculate_damage(
        attacker_ident, defender_ident, Move("iceshard", gen=9), battle
    ) == (168, 204)

    defender.set_hp_status("100/100")
    assert calculate_damage(
        attacker_ident, defender_ident, Move("iceshard", gen=9), battle
    ) == (84, 102)


def test_weight():
    attacker = Pokemon(9, species="simisage")
    attacker.ability = "gluttony"
    defender = Pokemon(9, species="simisear")
    defender.ability = "heavymetal"
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert (
        calculate_base_power(
            attacker_ident, defender_ident, Move("grassknot", gen=9), battle, False
        )
        == 80
    )

    attacker.ability = "moldbreaker"
    assert (
        calculate_base_power(
            attacker_ident, defender_ident, Move("grassknot", gen=9), battle, False
        )
        == 60
    )

    attacker.ability = "gluttony"
    defender = Pokemon(9, species="registeel")
    defender.ability = "lightmetal"
    battle = create_battle(p1a=attacker, p2a=defender)
    defender_ident = defender.identifier("p2")
    assert (
        calculate_base_power(
            attacker_ident, defender_ident, Move("grassknot", gen=9), battle, False
        )
        == 100
    )

    attacker.ability = "moldbreaker"
    assert (
        calculate_base_power(
            attacker_ident, defender_ident, Move("grassknot", gen=9), battle, False
        )
        == 120
    )

    attacker.ability = "gluttony"
    defender.ability = "frisk"
    defender.item = "floatstone"
    assert (
        calculate_base_power(
            attacker_ident, defender_ident, Move("grassknot", gen=9), battle, False
        )
        == 100
    )

    defender.ability = "lightmetal"
    assert (
        calculate_base_power(
            attacker_ident, defender_ident, Move("grassknot", gen=9), battle, False
        )
        == 80
    )


def test_psychicterrain_psystrike_and_marvelscale():
    mewtwo = Teambuilder.parse_showdown_team("""
    Mewtwo
    Ability: Pressure
    Level: 100
    Tera Type: Psychic
    EVs: 252 SpA
    Timid Nature
    - Psystrike
    - Sucker Punch
    """)[0]
    attacker = Pokemon(9, teambuilder=mewtwo)
    attacker.boosts["spa"] = 2
    milotic = Teambuilder.parse_showdown_team("""
    Milotic @ Flame Orb
    Ability: Marvel Scale
    Level: 100
    EVs: 248 HP / 184 Def
    Bold Nature
    - Water Pulse
    """)[0]
    defender = Pokemon(9, teambuilder=milotic)
    defender.set_hp_status("100/100 brn")
    defender.boosts["spd"] = 1
    battle = create_battle(p1a=attacker, p2a=defender)
    battle.field_start("psychicterrain")
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("psystrike", gen=9), battle
    ) == (430, 507)
    assert calculate_damage(
        attacker_ident, defender_ident, Move("suckerpunch", gen=9), battle
    ) == (0, 0)


def test_knockoff_vs_klutz():
    attacker = Pokemon(9, species="Weavile")
    defender = Pokemon(9, species="Audino")
    defender._ability = "klutz"
    defender.item = "leftovers"
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("knockoff", gen=9), battle
    ) == (139, 165)


def test_knockoff_vs_zacian_crowned():
    attacker = Pokemon(9, species="Weavile")
    defender = Pokemon(9, species="Zacian-Crowned")
    defender._ability = "intrepidsword"
    defender.item = "rustedsword"
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("knockoff", gen=9), battle
    ) == (36, 43)


def test_moldbreaker():
    attacker = Pokemon(9, species="rampardos")
    attacker._ability = "moldbreaker"
    defender = Pokemon(9, species="blastoise")
    defender._ability = "raindish"
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    battle.parse_message(["", "-weather", "RainDance", "[from] move: Rain Dance"])
    assert calculate_damage(
        attacker_ident, defender_ident, Move("stoneedge", gen=9), battle
    ) == (168, 198)


def test_steely_spirit():
    attacker = Pokemon(9, species="perrserker", name="perserrker1")
    attacker._ability = "battlearmor"
    defender = Pokemon(9, species="perrserker", name="perserrker2")
    defender._ability = "battlearmor"
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    # assert calculate_damage(attacker_ident, defender_ident, Move('ironhead', gen=9), battle) == (46, 55)

    attacker2 = Pokemon(9, species="perrserker", name="perserrker3")
    attacker2._ability = "steelyspirit"
    battle = create_battle(p1a=attacker, p2a=defender, p1b=attacker2)

    assert calculate_damage(
        attacker_ident, defender_ident, Move("ironhead", gen=9), battle
    ) == (70, 83)

    attacker._ability = "steelyspirit"
    assert calculate_damage(
        attacker_ident, defender_ident, Move("ironhead", gen=9), battle
    ) == (105, 124)


def test_supreme_overlord():
    attacker = Pokemon(9, species="kingambit")
    attacker._ability = "supremeoverlord"
    defender = Pokemon(9, species="aggron")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("ironhead", gen=9), battle
    ) == (67, 79)

    for i in range(5):
        mon = Pokemon(9, species="furret", name=f"furret_{i}")
        mon.set_hp_status("0 fnt")
        battle._team[f"p1: {mon.name}"] = mon
    assert calculate_damage(
        attacker_ident, defender_ident, Move("ironhead", gen=9), battle
    ) == (100, 118)

    for i in range(5):
        mon = Pokemon(9, species="furret", name=f"furret_{i + 5}")
        mon.set_hp_status("0 fnt")
        battle._team[f"p1: {mon.name}"] = mon
    assert calculate_damage(
        attacker_ident, defender_ident, Move("ironhead", gen=9), battle
    ) == (100, 118)


def test_electro_drift_collision_course():
    attacker = Pokemon(9, species="Arceus")
    defender = Pokemon(9, species="Mew")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("electrodrift", gen=9), battle
    ) == calculate_damage(
        attacker_ident, defender_ident, Move("fusionbolt", gen=9), battle
    )

    defender2 = Pokemon(9, species="Manaphy")
    battle2 = create_battle(p1a=attacker, p2a=defender2)
    defender_ident2 = defender2.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident2, Move("electrodrift", gen=9), battle2
    ) != calculate_damage(
        attacker_ident, defender_ident, Move("fusionbolt", gen=9), battle
    )

    battle2.parse_message(["", "-terastallize", "p2: Manaphy", "Normal"])
    assert calculate_damage(
        attacker_ident, defender_ident2, Move("electrodrift", gen=9), battle2
    ) == calculate_damage(
        attacker_ident, defender_ident, Move("fusionbolt", gen=9), battle
    )

    defender3 = Pokemon(9, species="Jirachi")
    battle3 = create_battle(p1a=attacker, p2a=defender3)
    defender_ident3 = defender3.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident3, Move("collisioncourse", gen=9), battle3
    ) == calculate_damage(
        attacker_ident, defender_ident, Move("fusionbolt", gen=9), battle
    )

    battle.parse_message(["", "-terastallize", "p2: Jirachi", "Normal"])
    assert calculate_damage(
        attacker_ident, defender_ident3, Move("collisioncourse", gen=9), battle3
    ) == calculate_damage(
        attacker_ident, defender_ident2, Move("electrodrift", gen=9), battle2
    )


def test_poltergeist_knockoff():
    attacker = Pokemon(9, species="smeargle")
    defender = Pokemon(9, species="gougingfire")
    defender._ability = "protosynthesis"
    defender._item = "blunderpolicy"
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    battle.parse_message(["", "-weather", "SunnyDay", "[from] move: Sunny Day"])
    assert (
        calculate_base_power(
            attacker_ident, defender_ident, Move("knockoff", gen=9), battle, False
        )
        == 97
    )
    assert (
        calculate_base_power(
            attacker_ident, defender_ident, Move("poltergeist", gen=9), battle, False
        )
        == 110
    )

    defender = Pokemon(9, species="ironvaliant")
    defender._ability = "quarkdrive"
    defender._item = "blunderpolicy"
    battle = create_battle(p1a=attacker, p2a=defender)
    defender_ident = defender.identifier("p2")

    battle.parse_message(["", "-weather", "SunnyDay", "[from] move: Sunny Day"])
    assert (
        calculate_base_power(
            attacker_ident, defender_ident, Move("knockoff", gen=9), battle, False
        )
        == 97
    )
    assert (
        calculate_base_power(
            attacker_ident, defender_ident, Move("poltergeist", gen=9), battle, False
        )
        == 110
    )


def test_revelation_dance():
    attacker = Pokemon(9, species="oricoriopompom")
    defender = Pokemon(9, species="sandaconda")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")
    assert calculate_damage(
        attacker_ident, defender_ident, Move("revelationdance", gen=9), battle
    ) == (0, 0)

    attacker.terastallize("Water")
    assert (
        calculate_damage(
            attacker_ident, defender_ident, Move("revelationdance", gen=9), battle
        )[0]
        > 0
    )


def test_brick_break():
    attacker = Pokemon(9, species="mew")
    defender = Pokemon(9, species="mew")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("brickbreak", gen=9), battle
    ) == (27, 32)
    assert calculate_damage(
        attacker_ident, defender_ident, Move("drainpunch", gen=9), battle
    ) == (27, 32)

    battle.parse_message(["", "-sidestart", "p2: Mew", "move: Aurora Veil"])
    assert calculate_damage(
        attacker_ident, defender_ident, Move("drainpunch", gen=9), battle
    ) == (18, 21)
    assert calculate_damage(
        attacker_ident, defender_ident, Move("brickbreak", gen=9), battle
    ) == (27, 32)


def test_psychic_fangs():
    attacker = Pokemon(9, species="arceus")
    defender = Pokemon(9, species="arceus")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("psychicfangs", gen=9), battle
    ) == calculate_damage(
        attacker_ident, defender_ident, Move("liquidation", gen=9), battle
    )

    battle.parse_message(["", "-sidestart", "p2: Arceus", "move: Aurora Veil"])
    assert calculate_damage(
        attacker_ident, defender_ident, Move("psychicfangs", gen=9), battle
    ) != calculate_damage(
        attacker_ident, defender_ident, Move("liquidation", gen=9), battle
    )


def test_raging_bull():
    attacker = Pokemon(9, species="taurospaldeaaqua")
    defender = Pokemon(9, species="tauros")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("ragingbull", gen=9), battle
    ) == calculate_damage(
        attacker_ident, defender_ident, Move("aquatail", gen=9), battle
    )

    battle.parse_message(["", "-sidestart", "p2: Tauros", "move: Aurora Veil"])
    assert calculate_damage(
        attacker_ident, defender_ident, Move("ragingbull", gen=9), battle
    ) != calculate_damage(
        attacker_ident, defender_ident, Move("aquatail", gen=9), battle
    )


def test_expanding_force():
    attacker = Pokemon(9, species="mew")
    defender = Pokemon(9, species="mew")
    battle = create_battle(p1a=attacker, p2a=defender)
    attacker_ident = attacker.identifier("p1")
    defender_ident = defender.identifier("p2")

    assert calculate_damage(
        attacker_ident, defender_ident, Move("expandingforce", gen=9), battle
    ) == (43, 51)

    battle.field_start("psychicterrain")
    assert calculate_damage(
        attacker_ident, defender_ident, Move("expandingforce", gen=9), battle
    ) == (63, 75)
