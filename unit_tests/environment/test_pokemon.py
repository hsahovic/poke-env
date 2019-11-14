# -*- coding: utf-8 -*-
from poke_env.environment.pokemon import Pokemon


def test_pokemon_moves():
    mon = Pokemon(species="charizard")

    mon._moved("flamethrower")
    assert "flamethrower" in mon.moves

    mon._moved("struggle")
    assert "struggle" not in mon.moves

    assert not mon.preparing
    assert not mon.must_recharge
