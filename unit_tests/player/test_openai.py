import asyncio
import sys
from io import StringIO
from typing import Union

from gymnasium import Space

from poke_env.environment import AbstractBattle, Battle, Pokemon
from poke_env.player import (
    ActType,
    BattleOrder,
    ForfeitBattleOrder,
    ObsType,
    OpenAIGymEnv,
    Player,
)
from poke_env.player.openai_api import (
    LegacyOpenAIGymEnv,
    _AsyncPlayer,
    _AsyncQueue,
    wrap_for_old_gym_api,
)


class DummyEnv(OpenAIGymEnv[ObsType, ActType]):
    def __init__(self, *args, **kwargs):
        self.opponent = None
        super().__init__(*args, **kwargs)

    def calc_reward(
        self, last_battle: AbstractBattle, current_battle: AbstractBattle
    ) -> float:
        return 69.42

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        return ForfeitBattleOrder()

    def embed_battle(self, battle: AbstractBattle) -> ObsType:
        return [0, 1, 2]

    def describe_embedding(self) -> Space:
        return "Space"

    def action_space_size(self) -> int:
        return 1

    def get_opponent(self) -> Union[Player, str]:
        return self.opponent


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
    player.current_battle = battle
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


def test_legacy_wrapper():
    dummy = DummyEnv(start_listening=False)
    wrapped = wrap_for_old_gym_api(dummy)
    assert dummy.reset.__func__ is OpenAIGymEnv.reset
    assert dummy.step.__func__ is OpenAIGymEnv.step
    assert wrapped.reset.__func__ is LegacyOpenAIGymEnv.reset
    assert wrapped.step.__func__ is LegacyOpenAIGymEnv.step
    assert id(dummy._keep_challenging) == id(wrapped._keep_challenging)
    wrapped._keep_challenging = True
    assert id(dummy._keep_challenging) == id(wrapped._keep_challenging)
    dummy._keep_challenging = False
    assert id(dummy._keep_challenging) == id(wrapped._keep_challenging)


def test_legacy_wrapper_calc_reward():
    dummy = DummyEnv(start_listening=False)
    wrapped = wrap_for_old_gym_api(dummy)
    assert wrapped.calc_reward(None, None) == 69.42


def test_legacy_wrapper_action_to_move():
    dummy = DummyEnv(start_listening=False)
    wrapped = wrap_for_old_gym_api(dummy)
    assert isinstance(wrapped.action_to_move(2, None), ForfeitBattleOrder)


def test_legacy_wrapper_embed_battle():
    dummy = DummyEnv(start_listening=False)
    wrapped = wrap_for_old_gym_api(dummy)
    assert wrapped.embed_battle(None) == [0, 1, 2]


def test_legacy_wrapper_describe_embedding():
    dummy = DummyEnv(start_listening=False)
    wrapped = wrap_for_old_gym_api(dummy)
    assert wrapped.describe_embedding() == "Space"


def test_legacy_wrapper_action_space_size():
    dummy = DummyEnv(start_listening=False)
    wrapped = wrap_for_old_gym_api(dummy)
    assert wrapped.action_space_size() == 1


def test_legacy_wrapper_get_opponent():
    dummy = DummyEnv(start_listening=False)
    dummy.opponent = "Opponent"
    wrapped = wrap_for_old_gym_api(dummy)
    assert wrapped.get_opponent() == "Opponent"
