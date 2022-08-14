# -*- coding: utf-8 -*-
from poke_env.environment import Move, SPECIAL_MOVES, Pokemon, PokemonType


def test_pokemon_moves():
    mon = Pokemon(species="charizard")

    mon._moved("flamethrower")
    assert "flamethrower" in mon.moves

    mon._moved("struggle")
    assert "struggle" not in mon.moves

    assert not mon.preparing
    assert not mon.must_recharge


def test_pokemon_types():
    # single type
    mon = Pokemon(species="pikachu")
    assert mon.type_1 == PokemonType.ELECTRIC
    assert mon.type_2 is None

    # dual type
    mon = Pokemon(species="garchomp")
    assert mon.type_1 == PokemonType.DRAGON
    assert mon.type_2 == PokemonType.GROUND

    # alolan forms
    mon = Pokemon(species="raichualola")
    assert mon.type_1 == PokemonType.ELECTRIC
    assert mon.type_2 == PokemonType.PSYCHIC

    # megas
    mon = Pokemon(species="altaria")
    assert mon.type_1 == PokemonType.DRAGON
    assert mon.type_2 == PokemonType.FLYING

    mon._mega_evolve("altariaite")
    assert mon.type_1 == PokemonType.DRAGON
    assert mon.type_2 == PokemonType.FAIRY

    mon = Pokemon(species="charizard")
    mon._mega_evolve("charizarditex")
    assert mon.type_1 == PokemonType.FIRE
    assert mon.type_2 == PokemonType.DRAGON

    # primals
    mon = Pokemon(species="groudon")
    assert mon.type_1 == PokemonType.GROUND
    assert mon.type_2 is None

    mon._primal()
    assert mon.type_1 == PokemonType.GROUND
    assert mon.type_2 == PokemonType.FIRE


def test_pokemon_damage_multiplier():
    mon = Pokemon(species="pikachu")
    assert mon.damage_multiplier(PokemonType.GROUND) == 2
    assert mon.damage_multiplier(PokemonType.ELECTRIC) == 0.5

    mon = Pokemon(species="garchomp")
    assert mon.damage_multiplier(Move("icebeam")) == 4
    assert mon.damage_multiplier(Move("dracometeor")) == 2

    mon = Pokemon(species="linoone")
    assert mon.damage_multiplier(Move("closecombat")) == 2
    assert mon.damage_multiplier(PokemonType.GHOST) == 0

    mon = Pokemon(species="linoone")
    assert mon.damage_multiplier(SPECIAL_MOVES["recharge"]) == 1


def test_powerherb_ends_move_preparation():
    mon = Pokemon(species="roserade")
    mon.item = "powerherb"

    mon._prepare("solarbeam", "talonflame")
    assert mon.preparing

    mon._end_item("powerherb")
    assert not mon.preparing


def test_protect_counter_interactions():
    mon = Pokemon(species="xerneas")
    mon._moved("protect", failed=False)

    assert mon.protect_counter == 1

    mon._start_effect("feint")
    assert mon.protect_counter == 0

    mon._moved("protect", failed=False)
    mon._moved("protect", failed=False)
    assert mon.protect_counter == 2

    mon._moved("geomancy", failed=False)
    assert mon.protect_counter == 0


def test_pokemon_as_strs():
    mon = Pokemon(species="charizard")
    assert str(mon) == mon.__str__() == mon.__repr__()
    assert str(mon) == "charizard (pokemon object) [Active: False, Status: None]"

    mon._active = True
    assert str(mon) == "charizard (pokemon object) [Active: True, Status: None]"

    mon._set_hp_status("100/100 slp")
    assert str(mon) == "charizard (pokemon object) [Active: True, Status: SLP]"

    mon._cure_status()
    assert mon.status is None

    mon._cure_status()
    assert mon.status is None


def test_pokemon_boosts():
    mon = Pokemon(species="blastoise")
    assert set(mon.boosts.values()) == {0}

    mon._boost("accuracy", 1)
    assert set(mon.boosts.values()) == {0, 1}
    assert mon.boosts["accuracy"] == 1

    mon._boost("accuracy", 2)
    assert mon.boosts["accuracy"] == 3

    mon._boost("accuracy", 2)
    assert mon.boosts["accuracy"] == 5

    mon._boost("accuracy", 1)
    assert mon.boosts["accuracy"] == 6

    mon._boost("accuracy", -1)
    assert mon.boosts["accuracy"] == 5

    mon._boost("accuracy", 5)
    assert mon.boosts["accuracy"] == 6

    mon._boost("accuracy", -10)
    assert mon.boosts["accuracy"] == -4

    mon._boost("accuracy", -10)
    assert mon.boosts["accuracy"] == -6

    mon._boost("spd", 2)
    mon._clear_negative_boosts()
    assert mon.boosts["accuracy"] == 0
    assert mon.boosts["spd"] == 2
