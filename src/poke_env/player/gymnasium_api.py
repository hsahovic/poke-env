"""This module defines a player class with the Gymnasium API on the main thread.
For a black-box implementation consider using the module env_player.
"""

from __future__ import annotations

import asyncio
import copy
import time
from abc import abstractmethod
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import numpy as np
from gymnasium.spaces import Discrete, Space
from pettingzoo.utils.env import ObsType, ParallelEnv  # type: ignore[import-untyped]

from poke_env.concurrency import POKE_LOOP, create_in_poke_loop
from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.player.battle_order import (
    BattleOrder,
    DefaultBattleOrder,
    ForfeitBattleOrder,
)
from poke_env.player.player import Player
from poke_env.ps_client import AccountConfiguration
from poke_env.ps_client.server_configuration import (
    LocalhostServerConfiguration,
    ServerConfiguration,
)
from poke_env.teambuilder.teambuilder import Teambuilder

ItemType = TypeVar("ItemType")


class _AsyncQueue(Generic[ItemType]):
    def __init__(self, queue: asyncio.Queue[ItemType]):
        self.queue = queue

    async def async_get(self) -> ItemType:
        return await self.queue.get()

    def get(
        self, timeout: Optional[float] = None, default: Optional[ItemType] = None
    ) -> ItemType:
        try:
            res = asyncio.run_coroutine_threadsafe(
                asyncio.wait_for(self.async_get(), timeout), POKE_LOOP
            )
            return res.result()
        except asyncio.TimeoutError:
            assert default is not None
            return default

    async def async_put(self, item: ItemType):
        await self.queue.put(item)

    def put(self, item: ItemType):
        task = asyncio.run_coroutine_threadsafe(self.queue.put(item), POKE_LOOP)
        task.result()

    def empty(self):
        return self.queue.empty()

    def join(self):
        task = asyncio.run_coroutine_threadsafe(self.queue.join(), POKE_LOOP)
        task.result()

    async def async_join(self):
        await self.queue.join()


class _EnvPlayer(Player):
    battle_queue: _AsyncQueue[AbstractBattle]
    order_queue: _AsyncQueue[BattleOrder]

    def __init__(
        self,
        username: str,
        **kwargs: Any,
    ):
        self.__class__.__name__ = username
        super().__init__(**kwargs)
        self.__class__.__name__ = "_EnvPlayer"
        self.battle_queue = _AsyncQueue(create_in_poke_loop(asyncio.Queue, 1))
        self.order_queue = _AsyncQueue(create_in_poke_loop(asyncio.Queue, 1))
        self.current_battle: Optional[AbstractBattle] = None
        self.waiting = False

    def choose_move(self, battle: AbstractBattle) -> Awaitable[BattleOrder]:
        return self._env_move(battle)

    async def _env_move(self, battle: AbstractBattle) -> BattleOrder:
        if not self.current_battle or self.current_battle.finished:
            self.current_battle = battle
        if not self.current_battle == battle:
            raise RuntimeError("Using different battles for queues")
        await self.battle_queue.async_put(battle)
        self.waiting = True
        action = await self.order_queue.async_get()
        self.waiting = False
        return action

    def _battle_finished_callback(self, battle: AbstractBattle):
        asyncio.run_coroutine_threadsafe(self.battle_queue.async_put(battle), POKE_LOOP)


class GymnasiumEnv(ParallelEnv[str, ObsType, np.int64]):
    """
    Base class implementing the Gymnasium API on the main thread.
    """

    _INIT_RETRIES = 100
    _TIME_BETWEEN_RETRIES = 0.5
    _SWITCH_CHALLENGE_TASK_RETRIES = 30
    _TIME_BETWEEN_SWITCH_RETIRES = 1

    def __init__(
        self,
        account_configuration1: Optional[AccountConfiguration] = None,
        account_configuration2: Optional[AccountConfiguration] = None,
        *,
        avatar: Optional[int] = None,
        battle_format: str = "gen8randombattle",
        log_level: Optional[int] = None,
        save_replays: Union[bool, str] = False,
        server_configuration: Optional[
            ServerConfiguration
        ] = LocalhostServerConfiguration,
        accept_open_team_sheet: Optional[bool] = False,
        start_timer_on_battle_start: bool = False,
        start_listening: bool = True,
        open_timeout: Optional[float] = 10.0,
        ping_interval: Optional[float] = 20.0,
        ping_timeout: Optional[float] = 20.0,
        team: Optional[Union[str, Teambuilder]] = None,
        start_challenging: bool = False,
    ):
        """
        :param account_configuration: Player configuration. If empty, defaults to an
            automatically generated username with no password. This option must be set
            if the server configuration requires authentication.
        :type account_configuration: AccountConfiguration, optional
        :param avatar: Player avatar id. Optional.
        :type avatar: int, optional
        :param battle_format: Name of the battle format this player plays. Defaults to
            gen8randombattle.
        :type battle_format: Optional, str. Default to randombattles, with specifics
            varying per class.
        :param log_level: The player's logger level.
        :type log_level: int. Defaults to logging's default level.
        :param save_replays: Whether to save battle replays. Can be a boolean, where
            True will lead to replays being saved in a potentially new /replay folder,
            or a string representing a folder where replays will be saved.
        :type save_replays: bool or str
        :param server_configuration: Server configuration. Defaults to Localhost Server
            Configuration.
        :type server_configuration: ServerConfiguration, optional
        :param start_listening: Whether to start listening to the server. Defaults to
            True.
        :type start_listening: bool
        :param accept_open_team_sheet: Whether to automatically start the battle with
            open team sheets on. Defaults to False.
        :param start_timer_on_battle_start: Whether to automatically start the battle
            timer on battle start. Defaults to False.
        :type start_timer_on_battle_start: bool
        :param open_timeout: How long to wait for a timeout when connecting the socket
            (important for backend websockets.
            Increase only if timeouts occur during runtime).
            If None connect will never time out.
        :type open_timeout: float, optional
        :param ping_interval: How long between keepalive pings (Important for backend
            websockets). If None, disables keepalive entirely.
        :type ping_interval: float, optional
        :param ping_timeout: How long to wait for a timeout of a specific ping
            (important for backend websockets.
            Increase only if timeouts occur during runtime).
            If None pings will never time out.
        :type ping_timeout: float, optional
        :param team: The team to use for formats requiring a team. Can be a showdown
            team string, a showdown packed team string, of a ShowdownTeam object.
            Defaults to None.
        :type team: str or Teambuilder, optional
        :param start_challenging: Whether to automatically start the challenge loop or
            leave it inactive.
        :type start_challenging: bool
        """
        self.agent1 = _EnvPlayer(
            username=self.__class__.__name__,  # type: ignore
            account_configuration=account_configuration1,
            avatar=avatar,
            battle_format=battle_format,
            log_level=log_level,
            max_concurrent_battles=1,
            save_replays=save_replays,
            server_configuration=server_configuration,
            accept_open_team_sheet=accept_open_team_sheet,
            start_timer_on_battle_start=start_timer_on_battle_start,
            start_listening=start_listening,
            open_timeout=open_timeout,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            team=team,
        )
        self.agent2 = _EnvPlayer(
            username=self.__class__.__name__,  # type: ignore
            account_configuration=account_configuration2,
            avatar=avatar,
            battle_format=battle_format,
            log_level=log_level,
            max_concurrent_battles=1,
            save_replays=save_replays,
            server_configuration=server_configuration,
            accept_open_team_sheet=accept_open_team_sheet,
            start_timer_on_battle_start=start_timer_on_battle_start,
            start_listening=start_listening,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            team=team,
        )
        self.agents: List[str] = []
        self.possible_agents = [self.agent1.username, self.agent2.username]
        self.observation_spaces = {
            name: self.describe_embedding() for name in self.possible_agents
        }
        self.action_spaces = {
            name: Discrete(self.action_space_size()) for name in self.possible_agents
        }
        self.current_battle1: Optional[AbstractBattle] = None
        self.current_battle2: Optional[AbstractBattle] = None
        self.last_battle1: Optional[AbstractBattle] = None
        self.last_battle2: Optional[AbstractBattle] = None
        self._keep_challenging: bool = False
        self._challenge_task = None
        self._seed_initialized: bool = False
        if start_challenging:
            self._keep_challenging = True
            self._challenge_task = asyncio.run_coroutine_threadsafe(
                self._challenge_loop(), POKE_LOOP
            )

    ###################################################################################
    # PettingZoo API
    # https://pettingzoo.farama.org/api/parallel/#parallelenv

    def step(self, actions: Dict[str, np.int64]) -> Tuple[
        Dict[str, ObsType],
        Dict[str, float],
        Dict[str, bool],
        Dict[str, bool],
        Dict[str, Dict[str, Any]],
    ]:
        assert self.current_battle1 is not None
        assert self.current_battle2 is not None
        if self.current_battle1.finished:
            raise RuntimeError("Battle is already finished, call reset")
        self.last_battle1 = copy.copy(self.current_battle1)
        self.last_battle1.logger = None
        self.last_battle2 = copy.copy(self.current_battle2)
        self.last_battle2.logger = None
        if self.agent1.waiting:
            order1 = self.action_to_order(actions[self.agents[0]], self.current_battle1)
            self.agent1.order_queue.put(order1)
        if self.agent2.waiting:
            order2 = self.action_to_order(actions[self.agents[1]], self.current_battle2)
            self.agent2.order_queue.put(order2)
        battle1 = self.agent1.battle_queue.get(
            timeout=0.01, default=self.current_battle1
        )
        battle2 = self.agent2.battle_queue.get(
            timeout=0.01, default=self.current_battle2
        )
        observations = {
            self.agents[0]: self.embed_battle(battle1),
            self.agents[1]: self.embed_battle(battle2),
        }
        assert self.current_battle1 == self.agent1.current_battle
        reward = {
            self.agents[0]: self.calc_reward(self.last_battle1, self.current_battle1),
            self.agents[1]: self.calc_reward(self.last_battle2, self.current_battle2),
        }
        term1, trunc1 = self.calc_term_trunc(self.current_battle1)
        term2, trunc2 = self.calc_term_trunc(self.current_battle2)
        terminated = {self.agents[0]: term1, self.agents[1]: term2}
        truncated = {self.agents[0]: trunc1, self.agents[1]: trunc2}
        if self.current_battle1.finished:
            self.agents = []
        return observations, reward, terminated, truncated, self.get_additional_info()

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, ObsType], Dict[str, Dict[str, Any]]]:
        self.agents = [self.agent1.username, self.agent2.username]
        # TODO: use the seed
        if not self.agent1.current_battle or not self.agent2.current_battle:
            count = self._INIT_RETRIES
            while not self.agent1.current_battle or not self.agent2.current_battle:
                if count == 0:
                    raise RuntimeError("Agent is not challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_RETRIES)
        if self.current_battle1 and not self.current_battle1.finished:
            if self.current_battle1 == self.agent1.current_battle:
                self.agent1.order_queue.put(ForfeitBattleOrder())
                self.agent2.order_queue.put(DefaultBattleOrder())
                self.agent1.battle_queue.get()
                self.agent2.battle_queue.get()
            else:
                raise RuntimeError(
                    "Environment and agent aren't synchronized. Try to restart"
                )
        while self.current_battle1 == self.agent1.current_battle:
            time.sleep(0.01)
        obs1 = self.agent1.battle_queue.get()
        obs2 = self.agent2.battle_queue.get()
        observations = {
            self.agents[0]: self.embed_battle(obs1),
            self.agents[1]: self.embed_battle(obs2),
        }
        self.current_battle1 = self.agent1.current_battle
        self.current_battle1.logger = None
        self.current_battle2 = self.agent2.current_battle
        self.current_battle2.logger = None
        self.last_battle1 = self.current_battle1
        self.last_battle2 = self.current_battle2
        return observations, self.get_additional_info()

    def render(self, mode: str = "human"):
        if self.current_battle1 is not None:
            print(
                "  Turn %4d. | [%s][%3d/%3dhp] %10.10s - %10.10s [%3d%%hp][%s]"
                % (
                    self.current_battle1.turn,
                    "".join(
                        [
                            "⦻" if mon.fainted else "●"
                            for mon in self.current_battle1.team.values()
                        ]
                    ),
                    self.current_battle1.active_pokemon.current_hp or 0,
                    self.current_battle1.active_pokemon.max_hp or 0,
                    self.current_battle1.active_pokemon.species,
                    self.current_battle1.opponent_active_pokemon.species,
                    self.current_battle1.opponent_active_pokemon.current_hp or 0,
                    "".join(
                        [
                            "⦻" if mon.fainted else "●"
                            for mon in self.current_battle1.opponent_team.values()
                        ]
                    ),
                ),
                end="\n" if self.current_battle1.finished else "\r",
            )

    def close(self, purge: bool = True):
        if self.current_battle1 is None or self.current_battle1.finished:
            time.sleep(1)
            if self.current_battle1 != self.agent1.current_battle:
                self.current_battle1 = self.agent1.current_battle
        if self.current_battle2 is None or self.current_battle2.finished:
            time.sleep(1)
            if self.current_battle2 != self.agent2.current_battle:
                self.current_battle2 = self.agent2.current_battle
        closing_task = asyncio.run_coroutine_threadsafe(
            self._stop_challenge_loop(purge=purge), POKE_LOOP
        )
        closing_task.result()

    def observation_space(self, agent: str) -> Space:
        return self.observation_spaces[agent]

    def action_space(self, agent: str):
        return self.action_spaces[agent]

    ###################################################################################
    # Abstract methods

    @abstractmethod
    def calc_reward(
        self, last_battle: AbstractBattle, current_battle: AbstractBattle
    ) -> float:
        """
        Returns the reward for the current battle state. The battle state in the previous
        turn is given as well and can be used for comparisons.

        :param last_battle: The battle state in the previous turn.
        :type last_battle: AbstractBattle
        :param current_battle: The current battle state.
        :type current_battle: AbstractBattle

        :return: The reward for current_battle.
        :rtype: float
        """
        pass

    @abstractmethod
    def action_to_order(self, action: np.int64, battle: AbstractBattle) -> BattleOrder:
        """
        Returns the BattleOrder relative to the given action.

        :param action: The action to take.
        :type action: int
        :param battle: The current battle state
        :type battle: AbstractBattle

        :return: The battle order for the given action in context of the current battle.
        :rtype: BattleOrder
        """
        pass

    @abstractmethod
    def embed_battle(self, battle: AbstractBattle) -> ObsType:
        """
        Returns the embedding of the current battle state in a format compatible with
        the Gymnasium API.

        :param battle: The current battle state.
        :type battle: AbstractBattle

        :return: The embedding of the current battle state.
        """
        pass

    @abstractmethod
    def describe_embedding(self) -> Space[ObsType]:
        """
        Returns the description of the embedding. It must return a Space specifying
        low bounds and high bounds.

        :return: The description of the embedding.
        :rtype: Space
        """
        pass

    @abstractmethod
    def action_space_size(self) -> int:
        """
        Returns the size of the action space. Given size x, the action space goes
        from 0 to x - 1.

        :return: The action space size.
        :rtype: int
        """
        pass

    ###################################################################################
    # Helper methods

    def get_additional_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns additional info for the reset method.
        Override only if you really need it.

        :return: Additional information as a Dict
        :rtype: Dict
        """
        return {self.possible_agents[0]: {}, self.possible_agents[1]: {}}

    @staticmethod
    def calc_term_trunc(battle: AbstractBattle):
        terminated = False
        truncated = False
        if battle.finished:
            size = battle.team_size
            remaining_mons = size - len(
                [mon for mon in battle.team.values() if mon.fainted]
            )
            remaining_opponent_mons = size - len(
                [mon for mon in battle.opponent_team.values() if mon.fainted]
            )
            if (remaining_mons == 0) != (remaining_opponent_mons == 0):
                terminated = True
            else:
                truncated = True
        return terminated, truncated

    def background_send_challenge(self, username: str):
        """
        Sends a single challenge specified player. The function immediately returns
        to allow use of the Gymnasium API.

        :param username: The username of the player to challenge.
        :type username: str
        """
        if self._challenge_task and not self._challenge_task.done():
            raise RuntimeError(
                "Agent is already challenging opponents with the challenging loop. "
                "Try to specify 'start_challenging=True' during instantiation or call "
                "'await agent.stop_challenge_loop()' to clear the task."
            )
        self._challenge_task = asyncio.run_coroutine_threadsafe(
            self.agent1.send_challenges(username, 1), POKE_LOOP
        )

    def background_accept_challenge(self, username: str):
        """
        Accepts a single challenge specified player. The function immediately returns
        to allow use of the Gymnasium API.

        :param username: The username of the player to challenge.
        :type username: str
        """
        if self._challenge_task and not self._challenge_task.done():
            raise RuntimeError(
                "Agent is already challenging opponents with the challenging loop. "
                "Try to specify 'start_challenging=True' during instantiation or call "
                "'await agent.stop_challenge_loop()' to clear the task."
            )
        self._challenge_task = asyncio.run_coroutine_threadsafe(
            self.agent1.accept_challenges(username, 1, self.agent1.next_team), POKE_LOOP
        )

    async def _challenge_loop(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):
        if not n_challenges:
            while self._keep_challenging:
                await self.agent1.battle_against(self.agent2, n_battles=1)
                if callback and self.current_battle1 is not None:
                    callback(copy.deepcopy(self.current_battle1))
        elif n_challenges > 0:
            for _ in range(n_challenges):
                await self.agent1.battle_against(self.agent2, n_battles=1)
                if callback and self.current_battle1 is not None:
                    callback(copy.deepcopy(self.current_battle1))
        else:
            raise ValueError(f"Number of challenges must be > 0. Got {n_challenges}")

    def start_challenging(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):
        """
        Starts the challenge loop.

        :param n_challenges: The number of challenges to send. If empty it will run until
            stopped.
        :type n_challenges: int, optional
        :param callback: The function to callback after each challenge with a copy of
            the final battle state.
        :type callback: Callable[[AbstractBattle], None], optional
        """
        if self._challenge_task and not self._challenge_task.done():
            count = self._SWITCH_CHALLENGE_TASK_RETRIES
            while not self._challenge_task.done():
                if count == 0:
                    raise RuntimeError("Agent is already challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_SWITCH_RETIRES)
        if not n_challenges:
            self._keep_challenging = True
        self._challenge_task = asyncio.run_coroutine_threadsafe(
            self._challenge_loop(n_challenges, callback), POKE_LOOP
        )

    async def _ladder_loop(
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
                await self.agent1.ladder(1)
                if callback and self.current_battle1 is not None:
                    callback(self.current_battle1)
        else:
            while self._keep_challenging:
                await self.agent1.ladder(1)
                if callback and self.current_battle1 is not None:
                    callback(self.current_battle1)

    def start_laddering(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):
        """
        Starts the laddering loop.

        :param n_challenges: The number of ladder games to play. If empty it
            will run until stopped.
        :type n_challenges: int, optional
        :param callback: The function to callback after each challenge with a
            copy of the final battle state.
        :type callback: Callable[[AbstractBattle], None], optional
        """
        if self._challenge_task and not self._challenge_task.done():
            count = self._SWITCH_CHALLENGE_TASK_RETRIES
            while not self._challenge_task.done():
                if count == 0:
                    raise RuntimeError("Agent is already challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_SWITCH_RETIRES)
        if not n_challenges:
            self._keep_challenging = True
        self._challenge_task = asyncio.run_coroutine_threadsafe(
            self._ladder_loop(n_challenges, callback), POKE_LOOP
        )

    async def _stop_challenge_loop(
        self, force: bool = True, wait: bool = True, purge: bool = False
    ):
        self._keep_challenging = False

        if force:
            if self.current_battle1 and not self.current_battle1.finished:
                if not (
                    self.agent1.order_queue.empty() and self.agent2.order_queue.empty()
                ):
                    await asyncio.sleep(2)
                    if not (
                        self.agent1.order_queue.empty()
                        and self.agent2.order_queue.empty()
                    ):
                        raise RuntimeError(
                            "The agent is still sending actions. "
                            "Use this method only when training or "
                            "evaluation are over."
                        )
                if not self.agent1.battle_queue.empty():
                    await self.agent1.battle_queue.async_get()
                if not self.agent2.battle_queue.empty():
                    await self.agent2.battle_queue.async_get()
                await self.agent1.order_queue.async_put(ForfeitBattleOrder())
                await self.agent2.order_queue.async_put(DefaultBattleOrder())

        if wait and self._challenge_task:
            while not self._challenge_task.done():
                await asyncio.sleep(1)
            self._challenge_task.result()

        self._challenge_task = None
        self.current_battle1 = None
        self.current_battle2 = None
        self.agent1.current_battle = None
        self.agent2.current_battle = None
        while not self.agent1.order_queue.empty():
            await self.agent1.order_queue.async_get()
        while not self.agent2.order_queue.empty():
            await self.agent2.order_queue.async_get()
        while not self.agent1.battle_queue.empty():
            await self.agent1.battle_queue.async_get()
        while not self.agent2.battle_queue.empty():
            await self.agent2.battle_queue.async_get()

        if purge:
            self.reset_battles()

    def reset_battles(self):
        """Resets the player's inner battle tracker."""
        self.agent1.reset_battles()
        self.agent2.reset_battles()

    def done(self, timeout: Optional[int] = None) -> bool:
        """
        Returns True if the task is done or is done after the timeout, false otherwise.

        :param timeout: The amount of time to wait for if the task is not already done.
            If empty it will wait until the task is done.
        :type timeout: int, optional

        :return: True if the task is done or if the task gets completed after the
            timeout.
        :rtype: bool
        """
        if self._challenge_task is None:
            return True
        if timeout is None:
            self._challenge_task.result()
            return True
        if self._challenge_task.done():
            return True
        time.sleep(timeout)
        return self._challenge_task.done()
