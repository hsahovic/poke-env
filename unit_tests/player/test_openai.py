import asyncio
import pytest
import sys

from io import StringIO
from queue import Queue
from typing import Union

from gym import Space

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.environment.battle import Battle
from poke_env.environment.pokemon import Pokemon
from poke_env.player.battle_order import ForfeitBattleOrder, BattleOrder
from poke_env.player.openai_api import (
    _AsyncQueue,
    _AsyncPlayer,
    OpenAIGymEnv,
    ObservationType,
)
from poke_env.player.player import Player


class DummyEnv(OpenAIGymEnv):
    def __init__(self, *args, **kwargs):
        self.opponent = None
        super().__init__(*args, **kwargs)

    def calc_reward(self, last_battle, current_battle) -> float:
        pass

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        pass

    def embed_battle(self, battle: AbstractBattle) -> ObservationType:
        pass

    def describe_embedding(self) -> Space:
        return None

    def action_space_size(self) -> int:
        return 1

    def get_opponent(self) -> Union[Player, str]:
        return self.opponent


class UserFuncs:
    def embed_battle(self, battle):
        return "battle"


def test_init_queue():
    q = None
    with pytest.raises(RuntimeError):
        q = _AsyncQueue(Queue())
    assert not q
    q = _AsyncQueue(asyncio.Queue())
    assert isinstance(q, _AsyncQueue)


def test_queue():
    q = _AsyncQueue(asyncio.Queue())
    assert q.empty()
    q.put(1)
    assert q.queue.qsize() == 1
    asyncio.get_event_loop().run_until_complete(q.async_put(2))
    assert q.queue.qsize() == 2
    item = q.get()
    q.queue.task_done()
    assert q.queue.qsize() == 1
    assert item == 1
    item = asyncio.get_event_loop().run_until_complete(q.async_get())
    q.queue.task_done()
    assert q.empty()
    assert item == 2
    asyncio.get_event_loop().run_until_complete(q.async_join())
    q.join()


def test_async_player():
    player = _AsyncPlayer(UserFuncs(), start_listening=False, username="usr")
    battle = Battle("bat1", player.username, player.logger)
    player.actions.put(-1)
    order = asyncio.get_event_loop().run_until_complete(player.env_move(battle))
    assert isinstance(order, ForfeitBattleOrder)
    assert player.observations.get() == "battle"


def render(battle):
    player = DummyEnv(start_listening=False)
    captured_output = StringIO()
    sys.stdout = captured_output
    player.current_battle = battle
    player.render()
    sys.stdout = sys.__stdout__
    return captured_output.getvalue()


def test_render():
    battle = Battle("bat1", "usr", None)
    battle._turn = 3
    active_mon = Pokemon(species="charizard")
    active_mon._active = True
    battle._team = {"1": active_mon}
    opponent_mon = Pokemon(species="pikachu")
    opponent_mon._active = True
    battle._opponent_team = {"1": opponent_mon}
    expected = "  Turn    3. | [●][  0/  0hp]  charizard -    pikachu [  0%hp][●]\r"
    assert render(battle) == expected
    active_mon._max_hp = 120
    active_mon._current_hp = 60
    expected = "  Turn    3. | [●][ 60/120hp]  charizard -    pikachu [  0%hp][●]\r"
    assert render(battle) == expected
    opponent_mon._current_hp = 20
    expected = "  Turn    3. | [●][ 60/120hp]  charizard -    pikachu [ 20%hp][●]\r"
    assert render(battle) == expected
    other_mon = Pokemon(species="pichu")
    battle._team["2"] = other_mon
    expected = "  Turn    3. | [●●][ 60/120hp]  charizard -    pikachu [ 20%hp][●]\r"
    assert render(battle) == expected


def test_get_opponent():
    player = DummyEnv(start_listening=False)
    assert player._get_opponent() is None
    player.opponent = "test"
    assert player._get_opponent() == "test"
    player.opponent = ["test"]
    assert player._get_opponent() == "test"
    opponents = ["test1", "test2", "test3", "test4", "test5"]
    player.opponent = opponents
    for _ in range(100):
        assert player._get_opponent() in opponents
    player.opponent = [0]
    with pytest.raises(RuntimeError):
        player._get_opponent()
