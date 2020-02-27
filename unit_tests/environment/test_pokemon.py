# -*- coding: utf-8 -*-
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
