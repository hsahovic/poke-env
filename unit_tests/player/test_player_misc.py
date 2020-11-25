# -*- coding: utf-8 -*-
from poke_env.environment.battle import Battle
from poke_env.environment.double_battle import DoubleBattle
from poke_env.player.player import Player
from poke_env.player.random_player import RandomPlayer

from unittest.mock import MagicMock
from unittest.mock import patch


class SimplePlayer(Player):
    def choose_move(self, battle):
        return self.choose_random_move(battle)


def test_player_default_order():
    assert SimplePlayer().choose_default_move().message == "/choose default"


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


@patch("poke_env.player.player.random.random")
def test_choose_random_move_doubles(pseudo_random, example_doubles_request):
    # possible_choices_memo = (
    #     []
    # )  # this needs to be reset at each start of Player.choose_random_move

    # def count_substrings(substring: str, in_: List[str]) -> int:
    #     return sum(map(lambda el: substring in el, in_))

    # def choose_non_dynamax(first_orders,) -> str:
    #     joined = DoubleBattleOrder.join_orders(possible_choices)
    #     possible_choices_memo.append(possible_choices.copy())
    #     for possible_choice in possible_choices:
    #         if " dynamax" not in possible_choice:
    #             return possible_choice
    #     raise ValueError(f"Only max moves are available in {possible_choices}")

    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger)
    player = RandomPlayer()
    battle._parse_request(example_doubles_request)
    battle._switch("p2a: Tyranitar", "Tyranitar, L50, M", "48/48")

    pseudo_random.side_effect = lambda: 0
    choice = player.choose_random_move(battle)
    assert choice.message == "/choose move psychic -2, move geargrind -1"

    pseudo_random.side_effect = lambda: 0.5
    choice = player.choose_random_move(battle)
    assert (
        choice.message == "/choose switch zamazentacrowned, move geargrind dynamax -1"
    )

    pseudo_random.side_effect = lambda: 0.999
    choice = player.choose_random_move(battle)
    assert choice.message == "/choose move slackoff dynamax, switch thundurus"

    battle._switch("p2b: Excadrill", "Excadrill, L50, M", "48/48")

    pseudo_random.side_effect = lambda: 0
    choice = player.choose_random_move(battle)
    assert choice.message == "/choose move psychic -2, move geargrind -1"

    pseudo_random.side_effect = lambda: 0.5
    choice = player.choose_random_move(battle)
    assert choice.message == "/choose move slackoff, move wildcharge dynamax 2"

    pseudo_random.side_effect = lambda: 0.999
    choice = player.choose_random_move(battle)
    assert choice.message == "/choose move slackoff dynamax, switch thundurus"
