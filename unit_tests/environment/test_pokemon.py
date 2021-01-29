# -*- coding: utf-8 -*-
from poke_env.environment.move import Move
from poke_env.environment.move import SPECIAL_MOVES
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.pokemon_type import PokemonType


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
