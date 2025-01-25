import asyncio
import sys
from io import StringIO

from gymnasium import Space
from pettingzoo.utils.env import ActionType, ObsType

from poke_env.environment import AbstractBattle, Battle, Pokemon
from poke_env.player import BattleOrder, ForfeitBattleOrder, GymnasiumEnv
from poke_env.player.gymnasium_api import _AsyncPlayer, _AsyncQueue


class DummyEnv(GymnasiumEnv[ObsType, ActionType]):
    def __init__(self, *args, **kwargs):
        self.opponent = None
        super().__init__(*args, **kwargs)

    def calc_reward(self, battle: AbstractBattle) -> float:
        return 69.42

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        return ForfeitBattleOrder()

    def embed_battle(self, battle: AbstractBattle) -> ObsType:
        return [0, 1, 2]

    def describe_embedding(self) -> Space:
        return "Space"

    def action_space_size(self) -> int:
        return 1


class UserFuncs:
    def embed_battle(self, battle):
        return "battle"


def test_init_queue():
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
    battle = Battle("bat1", player.username, player.logger, gen=8)
    player.actions.put(-1)
    order = asyncio.get_event_loop().run_until_complete(player._env_move(battle))
    assert isinstance(order, ForfeitBattleOrder)
    assert player.observations.get() == "battle"


def render(battle):
    player = DummyEnv(start_listening=False)
    captured_output = StringIO()
    sys.stdout = captured_output
    player.battle1 = battle
    player.render()
    sys.stdout = sys.__stdout__
    return captured_output.getvalue()


def test_render():
    battle = Battle("bat1", "usr", None, gen=8)
    battle._turn = 3
    active_mon = Pokemon(species="charizard", gen=8)
    active_mon._active = True
    battle._team = {"1": active_mon}
    opponent_mon = Pokemon(species="pikachu", gen=8)
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
    other_mon = Pokemon(species="pichu", gen=8)
    battle._team["2"] = other_mon
    expected = "  Turn    3. | [●●][ 60/120hp]  charizard -    pikachu [ 20%hp][●]\r"
    assert render(battle) == expected
