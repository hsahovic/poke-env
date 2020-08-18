# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from poke_env.environment.double_battle import DoubleBattle
from poke_env.environment.pokemon import Pokemon


def test_battle_request(example_doubles_request):
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger)

    battle._parse_request(example_doubles_request)
    mr_rime, klinklang = battle.active_pokemon
    assert isinstance(mr_rime, Pokemon)
    assert isinstance(klinklang, Pokemon)
    assert battle.get_pokemon("p1: Mr. Rime") == mr_rime
    assert battle.get_pokemon("p1: Klinklang") == klinklang
    assert len(battle.team) == 6

    pokemon_names = set(map(lambda pokemon: pokemon.species, battle.team.values()))
    assert "Thundurus" in pokemon_names
    assert "Raichu" in pokemon_names
    assert "Maractus" in pokemon_names
    assert "Zamazenta" in pokemon_names

    zamazenta = battle.get_pokemon("p1: Zamazenta")
    zamazenta_moves = zamazenta.moves
    assert (
        len(zamazenta_moves) == 4
        and "closecombat" in zamazenta_moves
        and "crunch" in zamazenta_moves
        and "psychicfangs" in zamazenta_moves
        and "behemothbash" in zamazenta_moves
    )
