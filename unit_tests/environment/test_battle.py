# -*- coding: utf-8 -*-
import pytest

from unittest.mock import MagicMock

from poke_env.environment.battle import Battle
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.side_condition import SideCondition


def test_battle_get_pokemon():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

    #  identifier: str, force_self_team: bool = False, details: str = ""

    battle.get_pokemon("p2: azumarill", force_self_team=True)
    assert "p2: azumarill" in battle.team

    battle._player_role = "p2"

    battle._parse_message(["", "teamsize", "p1", 6])
    battle._parse_message(["", "teamsize", "p2", 6])

    battle.get_pokemon("p2a: tapukoko")
    assert "p2: tapukoko" in battle.team

    battle.get_pokemon("p1: hydreigon", details="Hydreigon, F")
    assert "p1: hydreigon" in battle.opponent_team

    assert battle.get_pokemon("p2: tapufini").species == "tapufini"
    assert battle.get_pokemon("p2: tapubulu").types == (
        PokemonType.GRASS,
        PokemonType.FAIRY,
    )
    assert battle.get_pokemon("p2: tapulele").base_stats == {
        "atk": 85,
        "def": 75,
        "hp": 70,
        "spa": 130,
        "spd": 115,
        "spe": 95,
    }
    battle.get_pokemon("p2: yveltal")

    assert len(battle.team) == 6

    with pytest.raises(ValueError):
        battle.get_pokemon("p2: pikachu")

    assert "p2: pikachu" not in battle.team


def test_battle_side_start_end():
    logger = MagicMock()
    battle = Battle("tag", "username", logger)
    battle._player_role = "p1"

    assert not battle.side_conditions

    condition = "safeguard"
    battle._side_start("p1", condition)

    assert battle.side_conditions == {SideCondition.SAFEGUARD}

    battle._side_end("p1", condition)

    assert not battle.side_conditions
