from unittest.mock import MagicMock

from poke_env.battle import DoubleBattle, Move, Pokemon, PokemonGender, PokemonType
from poke_env.stats import _raw_hp, _raw_stat
from poke_env.teambuilder.teambuilder import Teambuilder


def test_pokemon_moves():
    mon = Pokemon(species="charizard", gen=8)

    mon.moved("flamethrower")
    assert "flamethrower" in mon.moves

    mon.moved("struggle")
    assert "struggle" not in mon.moves

    assert not mon.preparing
    assert not mon.must_recharge


def test_pokemon_types():
    # single type
    mon = Pokemon(species="pikachu", gen=8)
    assert mon.type_1 == PokemonType.ELECTRIC
    assert mon.type_2 is None

    # dual type
    mon = Pokemon(species="garchomp", gen=8)
    assert mon.type_1 == PokemonType.DRAGON
    assert mon.type_2 == PokemonType.GROUND

    # alolan forms
    mon = Pokemon(species="raichualola", gen=8)
    assert mon.type_1 == PokemonType.ELECTRIC
    assert mon.type_2 == PokemonType.PSYCHIC

    # megas
    mon = Pokemon(species="altaria", gen=8)
    assert mon.type_1 == PokemonType.DRAGON
    assert mon.type_2 == PokemonType.FLYING

    mon.mega_evolve("altariaite")
    assert mon.type_1 == PokemonType.DRAGON
    assert mon.type_2 == PokemonType.FAIRY

    mon = Pokemon(species="charizard", gen=8)
    mon.mega_evolve("charizarditex")
    assert mon.type_1 == PokemonType.FIRE
    assert mon.type_2 == PokemonType.DRAGON

    # primals
    mon = Pokemon(species="groudon", gen=8)
    assert mon.type_1 == PokemonType.GROUND
    assert mon.type_2 is None

    mon.primal()
    assert mon.type_1 == PokemonType.GROUND
    assert mon.type_2 == PokemonType.FIRE


def test_pokemon_damage_multiplier():
    mon = Pokemon(species="pikachu", gen=8)
    assert mon.damage_multiplier(PokemonType.GROUND) == 2
    assert mon.damage_multiplier(PokemonType.ELECTRIC) == 0.5

    mon = Pokemon(species="garchomp", gen=8)
    assert mon.damage_multiplier(Move("icebeam", gen=8)) == 4
    assert mon.damage_multiplier(Move("dracometeor", gen=8)) == 2

    mon = Pokemon(species="linoone", gen=8)
    assert mon.damage_multiplier(Move("closecombat", gen=8)) == 2
    assert mon.damage_multiplier(PokemonType.GHOST) == 0

    mon = Pokemon(species="linoone", gen=8)
    assert mon.damage_multiplier(Move("recharge", gen=8)) == 1


def test_powerherb_ends_move_preparation():
    mon = Pokemon(species="roserade", gen=8)
    mon.item = "powerherb"

    mon.prepare("solarbeam", None)
    assert mon.preparing

    mon.end_item("powerherb")
    assert not mon.preparing


def test_protect_counter_interactions():
    mon = Pokemon(species="xerneas", gen=8)
    mon.moved("protect", failed=False)

    assert mon.protect_counter == 1

    mon.start_effect("feint")
    assert mon.protect_counter == 0

    mon.moved("protect", failed=False)
    mon.moved("protect", failed=False)
    assert mon.protect_counter == 2

    mon.moved("geomancy", failed=False)
    assert mon.protect_counter == 0


def test_pokemon_as_strs():
    mon = Pokemon(species="charizard", gen=8)
    assert str(mon) == mon.__str__() == mon.__repr__()
    assert str(mon) == "charizard (pokemon object) [Active: False, Status: None]"

    mon._active = True
    assert str(mon) == "charizard (pokemon object) [Active: True, Status: None]"

    mon.set_hp_status("100/100 slp")
    assert str(mon) == "charizard (pokemon object) [Active: True, Status: SLP]"

    mon.cure_status()
    assert mon.status is None

    mon.cure_status()
    assert mon.status is None


def test_pokemon_boosts():
    mon = Pokemon(species="blastoise", gen=8)
    assert set(mon.boosts.values()) == {0}

    mon.boost("accuracy", 1)
    assert set(mon.boosts.values()) == {0, 1}
    assert mon.boosts["accuracy"] == 1

    mon.boost("accuracy", 2)
    assert mon.boosts["accuracy"] == 3

    mon.boost("accuracy", 2)
    assert mon.boosts["accuracy"] == 5

    mon.boost("accuracy", 1)
    assert mon.boosts["accuracy"] == 6

    mon.boost("accuracy", -1)
    assert mon.boosts["accuracy"] == 5

    mon.boost("accuracy", 5)
    assert mon.boosts["accuracy"] == 6

    mon.boost("accuracy", -10)
    assert mon.boosts["accuracy"] == -4

    mon.boost("accuracy", -10)
    assert mon.boosts["accuracy"] == -6

    mon.boost("spd", 2)
    mon.clear_negative_boosts()
    assert mon.boosts["accuracy"] == 0
    assert mon.boosts["spd"] == 2


def test_pokemon_base_species():
    charizard = Pokemon(species="charizard", gen=8)
    mega_charizard_x = Pokemon(species="charizardmegax", gen=8)
    mega_charizard_y = Pokemon(species="charizardmegay", gen=8)

    assert charizard.base_species == "charizard"
    assert mega_charizard_x.base_species == "charizard"
    assert mega_charizard_y.base_species == "charizard"

    arceus = Pokemon(species="arceus", gen=8)
    acreus_bug = Pokemon(species="arceusbug", gen=8)

    assert arceus.base_species == "arceus"
    assert acreus_bug.base_species == "arceus"


def test_tera_type():
    charizard = Pokemon(species="charizard", gen=8)
    assert charizard.tera_type is None
    charizard.terastallize("bug")
    assert charizard.tera_type == PokemonType.BUG
    assert charizard.types == [PokemonType.BUG]
    assert PokemonType.FIRE in charizard.original_types
    assert PokemonType.FLYING in charizard.original_types


def test_details():
    details = "furret, L100, F, tera:normal, shiny"
    furret = Pokemon(species="furret", gen=8, details=details)

    assert furret.species == "furret"
    assert furret.level == 100
    assert furret.shiny
    assert furret.gender == PokemonGender.FEMALE
    assert furret.tera_type == PokemonType.NORMAL


def test_teambuilder(showdown_format_teams):
    tb_mons = Teambuilder.parse_showdown_team(
        showdown_format_teams["gen9vgc2025regi"][0]
    )
    mon = Pokemon(9, teambuilder=tb_mons[0])

    assert mon
    assert mon.name == "Iron Hands"
    assert mon.level == 50
    assert mon.ability == "quarkdrive"
    assert mon.item == "assaultvest"
    assert list(mon.moves.keys()) == [
        "fakeout",
        "drainpunch",
        "wildcharge",
        "heavyslam",
    ]
    assert mon.tera_type == PokemonType.WATER
    assert mon.stats["hp"] == _raw_hp(mon.base_stats["hp"], 4, 31, 50)
    assert mon.stats["atk"] == _raw_stat(mon.base_stats["atk"], 156, 31, 50, 1.1)

    tb_mons = Teambuilder.parse_showdown_team(
        "Weezing-Galar\nAbility: Neutralizing Gas\nLevel: 50\n- Clear Smog"
    )
    mon = Pokemon(9, teambuilder=tb_mons[0])
    assert mon
    assert mon.name == "Weezing"
    assert mon.level == 50
    assert mon.ability == "neutralizinggas"
    assert mon.item is None
    assert list(mon.moves.keys()) == ["clearsmog"]
    assert mon.tera_type is None
    assert mon.stats == {
        "hp": 140,
        "atk": 110,
        "def": 140,
        "spa": 105,
        "spd": 90,
        "spe": 80,
    }


def test_name(example_doubles_request):
    charizard = Pokemon(species="charizard", gen=8)
    assert charizard.name == "Charizard"

    chiyu = Pokemon(species="chiyu", gen=9)
    assert chiyu.name == "Chi-Yu"

    furret = Pokemon(species="furret", name="Nickname", gen=9)
    assert furret.name == "Nickname"

    calyrexshadow = Pokemon(species="calyrexshadow", gen=9)
    assert calyrexshadow.name == "Calyrex"

    zamazenta = Pokemon(species="zamazentacrowned", gen=9)
    assert zamazenta.name == "Zamazenta"

    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger, gen=8)
    battle.parse_request(example_doubles_request)

    mon = battle.team["p1: Nickname"]
    assert mon.name == "Nickname"
    assert mon.species == "mrrime"

    tb_mons = Teambuilder.parse_showdown_team(
        "Weezing-Galar\nAbility: Neutralizing Gas\nLevel: 50\n- Clear Smog"
    )
    mon = Pokemon(9, teambuilder=tb_mons[0])
    assert mon.species == "weezinggalar"
    assert mon.name == "Weezing"

    tb_mons = Teambuilder.parse_showdown_team(
        "Nickname (Zamazenta-Crowned)\nAbility: Dauntless Shield\nLevel: 50\n- Behemoth Bash"
    )
    mon = Pokemon(9, teambuilder=tb_mons[0])
    assert mon.species == "zamazentacrowned"
    assert mon.name == "Nickname"

    assert mon.identifier("p1") == "p1: Nickname"


def test_stats(example_request, showdown_format_teams):
    request_mons = example_request["side"]["pokemon"]
    tb_mons = Teambuilder.parse_showdown_team(
        showdown_format_teams["gen9vgc2025regi"][0]
    )

    species_mon = Pokemon(9, species="furret")
    request_mon = Pokemon(9, request_pokemon=request_mons[0])
    tb_mon = Pokemon(9, teambuilder=tb_mons[0])

    assert species_mon.stats == {
        "hp": None,
        "atk": None,
        "def": None,
        "spa": None,
        "spd": None,
        "spe": None,
    }

    assert request_mon.stats == {
        "hp": 265,
        "atk": 139,
        "def": 183,
        "spa": 211,
        "spd": 211,
        "spe": 178,
    }

    assert tb_mon.stats == {
        "hp": 230,
        "atk": 198,
        "def": 129,
        "spa": 63,
        "spd": 120,
        "spe": 82,
    }


def test_temporary():
    furret = Pokemon(species="furret", gen=8)
    furret._ability = "adaptability"

    assert furret.types == [PokemonType.NORMAL]
    assert furret.stab_multiplier == 2

    furret.start_effect("typechange", "???/Fighting")
    furret.start_effect("move: Skill Swap", ["Levitate", "Adaptability"])

    assert furret.types == [PokemonType.THREE_QUESTION_MARKS, PokemonType.FIGHTING]
    assert furret.ability == "levitate"
    assert furret.damage_multiplier(PokemonType.PSYCHIC) == 1
    assert furret.stab_multiplier == 1.5

    furret.start_effect("typechange", "Fighting")
    assert furret.damage_multiplier(PokemonType.PSYCHIC) == 2

    furret.switch_out()
    furret.switch_in()

    assert furret.ability == "adaptability"

    furret.terastallize("dragon")
    assert furret.type_1 == PokemonType.DRAGON
    assert furret.type_2 is None
    assert furret.damage_multiplier(PokemonType.ICE) == 2

    furret.set_temporary_ability("frisk")
    assert furret.ability == "frisk"

    furret.set_temporary_ability(None)
    assert furret.ability is None

    furret.switch_out()
    assert furret.ability == "adaptability"
    assert furret.types == [PokemonType.DRAGON]
