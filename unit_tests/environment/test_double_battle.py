# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from poke_env.environment.double_battle import DoubleBattle
from poke_env.environment.pokemon import Pokemon


def test_battle_request_parsing(example_doubles_request):
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger)

    battle._parse_request(example_doubles_request)
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


def test_battle_request_parsing_and_interactions(example_doubles_request):
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger)

    battle._parse_request(example_doubles_request)
    mr_rime, klinklang = battle.active_pokemon
    assert isinstance(mr_rime, Pokemon)
    assert isinstance(klinklang, Pokemon)
    assert battle.get_pokemon("p1: Mr. Rime") == mr_rime
    assert battle.get_pokemon("p1: Klinklang") == klinklang

    assert set(battle.available_moves[0]) == set(
        battle.active_pokemon[0].moves.values()
    )
    assert set(battle.available_moves[1]) == set(
        battle.active_pokemon[1].moves.values()
    )

    assert len(battle.available_switches) == 2
    assert all(battle.can_dynamax)
    assert not any(battle.can_z_move)
    assert not any(battle.can_mega_evolve)
    assert not any(battle.trapped)
    assert not battle.force_switch
    assert not any(battle.maybe_trapped)

    mr_rime._boosts = {
        "accuracy": -2,
        "atk": 1,
        "def": -6,
        "evasion": 4,
        "spa": -4,
        "spd": 2,
        "spe": 3,
    }
    klinklang._boosts = {
        "accuracy": -6,
        "atk": 6,
        "def": -1,
        "evasion": 1,
        "spa": 4,
        "spd": -3,
        "spe": 2,
    }

    battle._clear_all_boosts()

    cleared_boosts = {
        "accuracy": 0,
        "atk": 0,
        "def": 0,
        "evasion": 0,
        "spa": 0,
        "spd": 0,
        "spe": 0,
    }

    assert mr_rime.boosts == cleared_boosts
    assert klinklang.boosts == cleared_boosts

    assert battle.active_pokemon == [mr_rime, klinklang]
    battle._swap("p1b: Klinklang", None)
    assert battle.active_pokemon == [klinklang, mr_rime]

    battle._switch("p2a: Milotic", "Milotic, L50, F", "48/48")
    battle._switch("p2b: Tyranitar", "Tyranitar, L50, M", "48/48")

    milotic, tyranitar = battle.opponent_active_pokemon
    assert milotic.species == "Milotic"
    assert tyranitar.species == "Tyranitar"

    assert all(battle.opponent_can_dynamax)
