# -*- coding: utf-8 -*-
"""This module defines a player class exposing the Open AI Gym API on the main thread.
"""
import asyncio
import atexit
import copy
import numpy as np  # pyre-ignore
import sys
import time

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from logging import disable, Logger, CRITICAL
from threading import Thread
from typing import Union, Awaitable, Optional, Tuple, TypeVar, Callable, Dict
from gym.core import Env  # pyre-ignore
from gym.spaces import Space, Discrete  # pyre-ignore

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.player.battle_order import BattleOrder, ForfeitBattleOrder
from poke_env.player.player import Player
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import (
    ServerConfiguration,
    LocalhostServerConfiguration,
)
from poke_env.teambuilder.teambuilder import Teambuilder

ObservationType = TypeVar("ObservationType")
ActionType = TypeVar("ActionType")


def __run_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def __stop_loop(loop: asyncio.AbstractEventLoop, thread: Thread):
    disable(CRITICAL)
    tasks = []
    py_ver = sys.version_info
    if py_ver.major == 3 and py_ver.minor >= 7:
        all_tasks = asyncio.all_tasks
    else:
        all_tasks = asyncio.Task.all_tasks
    for task in all_tasks(loop):
        task.cancel()
        tasks.append(task)
    cancelled = False
    shutdown = asyncio.run_coroutine_threadsafe(loop.shutdown_asyncgens(), loop)
    shutdown.result()
    while not cancelled:
        cancelled = True
        for task in tasks:
            if not task.done():
                cancelled = False
    loop.call_soon_threadsafe(loop.stop)
    thread.join()
    loop.call_soon_threadsafe(loop.close)


def __clear_loop():
    __stop_loop(THREAD_LOOP, _t)


MAIN_LOOP = asyncio.get_event_loop()
THREAD_LOOP = asyncio.new_event_loop()
_t = Thread(target=__run_loop, args=(THREAD_LOOP,), daemon=True)
_t.start()
atexit.register(__clear_loop)


class EnvLoop(AbstractContextManager):
    def __enter__(self):
        global MAIN_LOOP
        MAIN_LOOP = asyncio.get_event_loop()
        asyncio.set_event_loop(THREAD_LOOP)

    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.set_event_loop(MAIN_LOOP)


class _AsyncQueue:
    def __init__(self, queue: asyncio.Queue):
        if not isinstance(queue, asyncio.Queue):
            raise RuntimeError(f"Expected asyncio.Queue, got {type(queue)}")
        self.queue = queue

    async def async_get(self):
        return await self.queue.get()

    def get(self):
        res = asyncio.run_coroutine_threadsafe(
            self.queue.get(), asyncio.get_event_loop()
        )
        return res.result()

    async def async_put(self, item):
        await self.queue.put(item)

    def put(self, item):
        task = asyncio.run_coroutine_threadsafe(
            self.queue.put(item), asyncio.get_event_loop()
        )
        task.result()

    def empty(self):
        return self.queue.empty()

    def join(self):
        task = asyncio.run_coroutine_threadsafe(
            self.queue.join(), asyncio.get_event_loop()
        )
        task.result()

    async def async_join(self):
        await self.queue.join()


class _AsyncPlayer(Player):
    def __init__(self, user_funcs, username, **kwargs):
        self.__class__.__name__ = username
        super().__init__(**kwargs)
        self.__class__.__name__ = "_AsyncPlayer"
        self.observations = _AsyncQueue(asyncio.Queue(1))
        self.actions = _AsyncQueue(asyncio.Queue(1))
        self.current_battle: Optional[AbstractBattle] = None
        self.user_funcs: OpenAIGymEnv = user_funcs

    def choose_move(
        self, battle: AbstractBattle
    ) -> Union[BattleOrder, Awaitable[BattleOrder]]:
        return self.env_move(battle)

    async def env_move(self, battle: AbstractBattle):
        if not self.current_battle or self.current_battle.finished:
            self.current_battle = battle
        if not self.current_battle == battle:
            raise RuntimeError("Using different battles for queues")
        battle_to_send = self.user_funcs.embed_battle(battle)
        await self.observations.async_put(battle_to_send)
        action = await self.actions.async_get()
        if action == -1:
            return ForfeitBattleOrder()
        return self.user_funcs.action_to_move(action, battle)

    def _battle_finished_callback(self, battle: AbstractBattle) -> None:
        to_put = self.user_funcs.embed_battle(battle)
        asyncio.run_coroutine_threadsafe(
            self.observations.async_put(to_put), asyncio.get_event_loop()
        )


class OpenAIGymEnv(Env, ABC):  # pyre-ignore

    _INIT_RETRIES = 100
    _TIME_BETWEEN_RETRIES = 0.5

    def __init__(
        self,
        player_configuration: Optional[PlayerConfiguration] = None,
        *,
        avatar: Optional[int] = None,
        battle_format: str = "gen8randombattle",
        log_level: Optional[int] = None,
        save_replays: Union[bool, str] = False,
        server_configuration: Optional[
            ServerConfiguration
        ] = LocalhostServerConfiguration,
        start_timer_on_battle_start: bool = False,
        start_listening: bool = True,
        team: Optional[Union[str, Teambuilder]] = None,
        start_challenging: bool = True,
    ):
        if not asyncio.get_event_loop() == THREAD_LOOP:
            raise RuntimeError(
                "You are attempting to create an OpenAI agent without "
                "the required context. "
                "Remember to create all the players you will use "
                "with the OpenAI API inside the context "
                "EnvLoop. If unsure, use the following:\n"
                "if __name__ == '__main__':\n"
                "\twith EnvLoop():\n"
                "\t\tmain()"
            )
        self.agent = _AsyncPlayer(
            self,
            username=self.__class__.__name__,
            player_configuration=player_configuration,
            avatar=avatar,
            battle_format=battle_format,
            log_level=log_level,
            max_concurrent_battles=1,
            save_replays=save_replays,
            server_configuration=server_configuration,
            start_timer_on_battle_start=start_timer_on_battle_start,
            start_listening=start_listening,
            team=team,
        )
        self.battle_format = battle_format
        self.actions = self.agent.actions
        self.observations = self.agent.observations
        self.action_space = Discrete(self.action_space_size())
        self.observation_space = self.describe_embedding()
        self.current_battle: Optional[AbstractBattle] = None
        self.last_battle: Optional[AbstractBattle] = None
        self._keep_challenging: bool = False
        self.challenge_task = None
        if start_challenging:
            self.challenge_task = asyncio.run_coroutine_threadsafe(
                self.challenge_loop(), asyncio.get_event_loop()
            )

    @abstractmethod
    def calc_reward(self, last_battle, current_battle) -> float:
        pass

    @abstractmethod
    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        pass

    @abstractmethod
    def embed_battle(self, battle: AbstractBattle) -> ObservationType:  # pyre-ignore
        pass

    @abstractmethod
    def describe_embedding(self) -> Space:  # pyre-ignore
        pass

    @abstractmethod
    def action_space_size(self) -> int:
        pass

    @abstractmethod
    def get_opponent(self) -> Union[Player, str]:
        pass

    def _get_opponent(self) -> Union[Player, str]:
        opponent = self.get_opponent()
        if isinstance(opponent, Player):
            if not opponent._listening_coroutine.get_loop() == THREAD_LOOP:
                raise RuntimeError(
                    "The opponent is listening on a wrong event loop. "
                    "Remember to create all the players you will use "
                    "with the OpenAI API inside the context "
                    "EnvLoop. If unsure, use the following:\n"
                    "if __name__ == '__main__':\n"
                    "\twith EnvLoop():\n"
                    "\t\tmain()"
                )
        return opponent

    def reset(self) -> ObservationType:  # pyre-ignore
        if not self.agent.current_battle:
            count = self._INIT_RETRIES
            while not self.agent.current_battle:
                if count == 0:
                    raise RuntimeError("Agent is not challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_RETRIES)
        if self.current_battle and not self.current_battle.finished:
            if self.current_battle == self.agent.current_battle:
                self.actions.put(-1)
                self.observations.get()
            else:
                raise RuntimeError(
                    "Environment and agent aren't synchronized. Try to restart"
                )
        while self.current_battle == self.agent.current_battle:
            time.sleep(0.01)
        self.current_battle = self.agent.current_battle
        self.last_battle = copy.deepcopy(self.current_battle)
        return self.embed_battle(self.current_battle)  # pyre-ignore

    def step(
        self, action: ActionType
    ) -> Tuple[ObservationType, float, bool, dict]:  # pyre-ignore
        if not self.current_battle:
            return self.reset(), 0.0, False, {}
        if self.current_battle.finished:
            raise RuntimeError("Battle is already finished, call reset")
        self.last_battle = copy.deepcopy(self.current_battle)
        self.actions.put(action)
        observation = self.observations.get()
        reward = self.calc_reward(self.last_battle, self.current_battle)
        return observation, reward, self.current_battle.finished, {}  # pyre-ignore

    def render(self, mode="human"):
        print(
            "  Turn %4d. | [%s][%3d/%3dhp] %10.10s - %10.10s [%3d%%hp][%s]"
            % (
                self.current_battle.turn,
                "".join(
                    [
                        "⦻" if mon.fainted else "●"
                        for mon in self.current_battle.team.values()
                    ]
                ),
                self.current_battle.active_pokemon.current_hp or 0,
                self.current_battle.active_pokemon.max_hp or 0,
                self.current_battle.active_pokemon.species,
                self.current_battle.opponent_active_pokemon.species,
                self.current_battle.opponent_active_pokemon.current_hp or 0,
                "".join(
                    [
                        "⦻" if mon.fainted else "●"
                        for mon in self.current_battle.opponent_team.values()
                    ]
                ),
            ),
            end="\n" if self.current_battle.finished else "\r",
        )

    def close(self):
        closing_task = asyncio.run_coroutine_threadsafe(
            self.stop_challenge_loop(), asyncio.get_event_loop()
        )
        closing_task.result()

    def seed(self, seed=None):
        np.random.seed(seed)

    async def challenge(self, username: str):
        if self.challenge_task and not self.challenge_task.done():
            raise RuntimeError(
                "Agent is already challenging opponents with the challenging loop. "
                "Try to specify 'start_challenging=True' during instantiation or call "
                "'await agent.stop_challenge_loop()' to clear the task."
            )
        await self.agent.send_challenges(username, 1)

    async def challenge_loop(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):
        if not n_challenges:
            while self._keep_challenging:
                opponent = self._get_opponent()
                if isinstance(opponent, Player):
                    await self.agent.battle_against(opponent, 1)
                elif isinstance(opponent, str):
                    await self.agent.send_challenges(opponent, 1)
                else:
                    raise ValueError(
                        f"Expected opponent of type List[Player] or string. "
                        f"Got {type(opponent)}"
                    )
                if callback:
                    callback(copy.deepcopy(self.current_battle))  # pyre-ignore
        elif n_challenges > 0:
            for _ in range(n_challenges):
                opponent = self._get_opponent()
                if isinstance(opponent, Player):
                    await self.agent.battle_against(opponent, 1)
                elif isinstance(opponent, str):
                    await self.agent.send_challenges(opponent, 1)
                else:
                    raise ValueError(
                        f"Expected opponent of type List[Player] or string. "
                        f"Got {type(opponent)}"
                    )
                if callback:
                    callback(copy.deepcopy(self.current_battle))  # pyre-ignore
        else:
            raise ValueError(f"Number of challenges must be > 0. Got {n_challenges}")

    def start_challenging(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):
        if self.challenge_task and not self.challenge_task.done():
            raise RuntimeError("Agent is already challenging")
        if not n_challenges:
            self._keep_challenging = True
        self.challenge_task = asyncio.run_coroutine_threadsafe(
            self.challenge_loop(n_challenges, callback), asyncio.get_event_loop()
        )

    async def ladder_loop(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):
        if n_challenges:
            if n_challenges <= 0:
                raise ValueError(
                    f"Number of challenges must be > 0. Got {n_challenges}"
                )
            for _ in range(n_challenges):
                await self.agent.ladder(1)
                if callback:
                    callback(copy.deepcopy(self.current_battle))  # pyre-ignore
        else:
            while self._keep_challenging:
                await self.agent.ladder(1)
                if callback:
                    callback(copy.deepcopy(self.current_battle))  # pyre-ignore

    def start_laddering(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):
        if self.challenge_task and not self.challenge_task.done():
            raise RuntimeError("Agent is already challenging")
        if not n_challenges:
            self._keep_challenging = True
        self.challenge_task = asyncio.run_coroutine_threadsafe(
            self.ladder_loop(n_challenges, callback), asyncio.get_event_loop()
        )

    async def stop_challenge_loop(
        self, force: bool = True, wait: bool = True, purge: bool = False
    ):
        self._keep_challenging = False

        if force:
            if not self.current_battle.finished:  # pyre-ignore
                if not self.actions.empty():
                    await asyncio.sleep(2)
                    if not self.actions.empty():
                        raise RuntimeError(
                            "The agent is still sending actions. "
                            "Use this method only when training or "
                            "evaluation are over."
                        )
                if not self.observations.empty():
                    await self.observations.async_get()
                await self.actions.async_put(-1)

        if wait:
            while not self.challenge_task.done():
                await asyncio.sleep(1)
            self.challenge_task.result()

        self.challenge_task = None
        self.current_battle = None
        self.agent.current_battle = None
        while not self.actions.empty():
            await self.actions.async_get()
        while not self.observations.empty():
            await self.observations.async_get()

        if purge:
            self.agent.reset_battles()

    # Expose properties of Player class

    @property
    def battles(self) -> Dict[str, AbstractBattle]:
        return self.agent.battles

    @property
    def format(self) -> str:
        return self.agent.format

    @property
    def format_is_doubles(self) -> bool:
        return self.agent.format_is_doubles

    @property
    def n_finished_battles(self) -> int:
        return self.agent.n_finished_battles

    @property
    def n_lost_battles(self) -> int:
        return self.agent.n_lost_battles

    @property
    def n_tied_battles(self) -> int:
        return self.agent.n_tied_battles

    @property
    def n_won_battles(self) -> int:
        return self.agent.n_won_battles

    @property
    def win_rate(self) -> float:
        return self.agent.win_rate

    # Expose properties of Player Network Interface Class

    @property
    def logged_in(self) -> asyncio.Event:
        return self.agent.logged_in

    @property
    def logger(self) -> Logger:
        return self.agent.logger

    @property
    def username(self) -> str:
        return self.agent.username

    @property
    def websocket_url(self) -> str:
        return self.agent.websocket_url
