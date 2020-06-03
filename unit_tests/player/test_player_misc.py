# -*- coding: utf-8 -*-
from poke_env.environment.battle import Battle
from poke_env.player.player import Player

from unittest.mock import MagicMock


class SimplePlayer(Player):
    def choose_move(self, battle):
        return self.choose_random_move(battle)


def test_player_default_order():
    assert SimplePlayer().choose_default_move() == "/choose default"


def test_random_teampreview():
    player = SimplePlayer()
    logger = MagicMock()
    battle = Battle("tag", "username", logger)

    battle._team = [None for _ in range(6)]

    teampreview_orders = [player.random_teampreview(battle) for _ in range(1000)]
    for order in teampreview_orders:
        assert len(order) == len("/team 123456")
        assert order.startswith("/team")
        assert set(order[-6:]) == set([str(n) for n in range(1, 7)])

    teampreview_orders = [player.teampreview(battle) for _ in range(1000)]
    for order in teampreview_orders:
        assert len(order) == len("/team 123456")
        assert order.startswith("/team")
        assert set(order[-6:]) == set([str(n) for n in range(1, 7)])

    battle._team = [None for _ in range(4)]

    teampreview_orders = [player.random_teampreview(battle) for _ in range(1000)]
    for order in teampreview_orders:
        assert len(order) == len("/team 1234")
        assert order.startswith("/team")
        assert set(order[-4:]) == set([str(n) for n in range(1, 5)])

    teampreview_orders = [player.teampreview(battle) for _ in range(1000)]
    for order in teampreview_orders:
        assert len(order) == len("/team 1234")
        assert order.startswith("/team")
        assert set(order[-4:]) == set([str(n) for n in range(1, 5)])

    battle._team = [None for _ in range(2)]

    teampreview_orders = [player.random_teampreview(battle) for _ in range(1000)]
    for order in teampreview_orders:
        assert len(order) == len("/team 12")
        assert order.startswith("/team")
        assert set(order[-2:]) == set([str(n) for n in range(1, 3)])

    teampreview_orders = [player.teampreview(battle) for _ in range(1000)]
    for order in teampreview_orders:
        assert len(order) == len("/team 12")
        assert order.startswith("/team")
        assert set(order[-2:]) == set([str(n) for n in range(1, 3)])
