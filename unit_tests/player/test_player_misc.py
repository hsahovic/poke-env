# -*- coding: utf-8 -*-
from poke_env.environment.battle import Battle
from poke_env.environment.double_battle import DoubleBattle
from poke_env.player.player import Player
from poke_env.player.random_player import RandomPlayer

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


def test_choose_random_move_doubles(example_doubles_request):
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger)
    battle._parse_request(example_doubles_request)
    battle._switch("p2a: Tyranitar", "Tyranitar, L50, M", "48/48")

    player = RandomPlayer()
    active_pokemon_1, active_pokemon_2 = battle.active_pokemon
    choice_1 = player.choose_random_move(battle)
    assert (
        any([move in choice_1 for move in active_pokemon_1.moves])
        or "/choose switch" in choice_1
    )
    assert (
        any([move in choice_1 for move in active_pokemon_2.moves])
        or ",switch" in choice_1
    )

    choices_100 = [player.choose_random_move(battle) for _ in range(100)]
    assert not any([" 2" in choice for choice in choices_100])
    assert any(["1" in choice for choice in choices_100])
    assert any(["-1" in choice for choice in choices_100])
    assert any(["-2" in choice for choice in choices_100])
    assert any(["dynamax" in choice for choice in choices_100])
    assert not any([choice.count("dynamax") == 2 for choice in choices_100])
    assert any([choice.count("switch") == 2 for choice in choices_100])

    battle._switch("p2b: Charizard", "Charizard, L50, M", "48/48")
    choices_100 = [player.choose_random_move(battle) for _ in range(100)]
    assert any([" 2" in choice for choice in choices_100])
