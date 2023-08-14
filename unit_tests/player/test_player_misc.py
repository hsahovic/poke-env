from collections import namedtuple
from unittest.mock import MagicMock, patch

import pytest

from poke_env.environment import AbstractBattle, Battle, DoubleBattle, Move
from poke_env.player import BattleOrder, Player, RandomPlayer, cross_evaluate


class SimplePlayer(Player):
    def choose_move(self, battle: AbstractBattle) -> BattleOrder:
        return self.choose_random_move(battle)


class FixedWinRatePlayer:
    async def accept_challenges(self, *args, **kwargs):
        pass

    async def send_challenges(self, *args, **kwargs):
        pass

    def reset_battles(self):
        pass

    @property
    def win_rate(self):
        return 0.5

    @property
    def next_team(self):
        return None

    @property
    def ps_client(self):
        return namedtuple("PSClient", "logged_in")(logged_in=None)


def test_player_default_order():
    assert SimplePlayer().choose_default_move().message == "/choose default"


def test_random_teampreview():
    player = SimplePlayer()
    logger = MagicMock()
    battle = Battle("tag", "username", logger, 8)

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
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger, 8)
    player = RandomPlayer()
    battle.parse_request(example_doubles_request)
    battle.switch("p2a: Tyranitar", "Tyranitar, L50, M", "48/48")

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

    battle.switch("p2b: Excadrill", "Excadrill, L50, M", "48/48")

    pseudo_random.side_effect = lambda: 0
    choice = player.choose_random_move(battle)
    assert choice.message == "/choose move psychic -2, move geargrind -1"

    pseudo_random.side_effect = lambda: 0.5
    choice = player.choose_random_move(battle)
    assert choice.message == "/choose move slackoff, move wildcharge dynamax 2"

    pseudo_random.side_effect = lambda: 0.999
    choice = player.choose_random_move(battle)
    assert choice.message == "/choose move slackoff dynamax, switch thundurus"


@patch("poke_env.ps_client.ps_client.PSClient.send_message")
@pytest.mark.asyncio
async def test_start_timer_on_battle_start(send_message_patch):
    # on
    player = SimplePlayer(start_listening=False, start_timer_on_battle_start=True)

    await player._create_battle(["", "gen9randombattle", "uuu"])
    # assert player._sent_messages == ["/timer on", "gen9randombattle-uuu"]

    send_message_patch.assert_called_with("/timer on", "gen9randombattle-uuu")

    # off
    player = SimplePlayer(start_listening=False, start_timer_on_battle_start=False)

    await player._create_battle(["", "gen9randombattle", "uuu"])
    with pytest.raises(AttributeError):
        player._sent_messages


@pytest.mark.asyncio
async def test_basic_challenge_handling():
    player = SimplePlayer(start_listening=False)

    assert player._challenge_queue.empty()
    await player._handle_challenge_request(
        [
            "",
            "pm",
            "Opponent",
            player.username,
            "/challenge gen9randombattle",
            "gen9randombattle",
            "",
            "",
        ]
    )
    assert player._challenge_queue.qsize() == 1

    assert await player._challenge_queue.get() == "Opponent"
    assert player._challenge_queue.empty()

    await player._handle_challenge_request(
        [
            "",
            "pm",
            "Opponent",
            player.username,
            "/challenge anotherformat",
            "anotherformat",
            "",
            "",
        ]
    )
    assert player._challenge_queue.empty()

    await player._handle_challenge_request(
        [
            "",
            "pm",
            player.username,
            "Opponent",
            "/challenge gen9randombattle",
            "gen9randombattle",
            "",
            "",
        ]
    )
    assert player._challenge_queue.empty()

    await player._handle_challenge_request(
        ["", "pm", "Opponent", player.username, "/challenge gen9randombattle"]
    )
    assert player._challenge_queue.empty()


@pytest.mark.asyncio
async def test_cross_evaluate():
    p1 = FixedWinRatePlayer()
    p2 = FixedWinRatePlayer()

    p1.username = "p1"
    p2.username = "p2"
    cross_evaluation = await cross_evaluate([p1, p2], 10)
    assert cross_evaluation == {
        "p1": {"p1": None, "p2": 0.5},
        "p2": {"p1": 0.5, "p2": None},
    }


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


async def return_move():
    return BattleOrder(Move("bite", gen=8))


@patch("poke_env.ps_client.ps_client.PSClient.send_message")
@pytest.mark.asyncio
async def test_awaitable_move(send_message_patch):
    player = SimplePlayer(start_listening=False)
    battle = Battle("bat1", player.username, player.logger, 8)
    battle._teampreview = False

    await player._handle_battle_request(battle)

    send_message_patch.assert_called_with("/choose default", "bat1")
    with patch.object(player, "choose_move", return_value=return_move()):
        await player._handle_battle_request(battle)
        send_message_patch.assert_called_with("/choose move bite", "bat1")
