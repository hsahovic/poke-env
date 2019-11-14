# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from poke_env.environment.battle import Battle
from poke_env.environment.side_condition import SideCondition


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
