# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from poke_env.environment.battle import Battle
from poke_env.environment.pokemon import Pokemon


def test_dynamax():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)
    battle._player_role = "p1"

    hydreigon = Pokemon(species="hydreigon")
    hydreigon._active = True
    battle._team = {"p1: Hydreigon": hydreigon}
    assert battle.active_pokemon.is_dynamaxed is not True

    battle._parse_message(["", "-start", "p1: Hydreigon", "dynamax"])

    assert battle.active_pokemon.is_dynamaxed
    assert battle.dynamax_turns_left == 3

    battle._parse_message(["", "-end", "p1: Hydreigon", "dynamax"])

    assert not battle.active_pokemon.is_dynamaxed
    assert battle.dynamax_turns_left is None
    assert not battle.can_dynamax
