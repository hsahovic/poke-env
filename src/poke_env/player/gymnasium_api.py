"""This module defines a player class with the Gymnasium API on the main thread.
For a black-box implementation consider using the module env_player.
"""

from __future__ import annotations

import asyncio
import copy
import time
from abc import abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

from gymnasium.spaces import Discrete, Space
from pettingzoo.utils.env import (  # type: ignore[import-untyped]
    ActionType,
    ObsType,
    ParallelEnv,
)

from poke_env.concurrency import POKE_LOOP, create_in_poke_loop
from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.player.battle_order import BattleOrder, ForfeitBattleOrder
from poke_env.player.player import Player
from poke_env.ps_client import AccountConfiguration
from poke_env.ps_client.server_configuration import (
    LocalhostServerConfiguration,
    ServerConfiguration,
)
from poke_env.teambuilder.teambuilder import Teambuilder


class _AsyncQueue:
    def __init__(self, queue: asyncio.Queue[Any]):
        self.queue = queue

    async def async_get(self):
        return await self.queue.get()

    def get(self, timeout: Optional[float] = None, default: Any = None):
        try:
            res = asyncio.run_coroutine_threadsafe(
                asyncio.wait_for(self.async_get(), timeout), POKE_LOOP
            )
            return res.result()
        except asyncio.TimeoutError:
            return default

    async def async_put(self, item: Any):
        await self.queue.put(item)

    def put(self, item: Any):
        task = asyncio.run_coroutine_threadsafe(self.queue.put(item), POKE_LOOP)
        task.result()

    def empty(self):
        return self.queue.empty()

    def join(self):
        task = asyncio.run_coroutine_threadsafe(self.queue.join(), POKE_LOOP)
        task.result()

    async def async_join(self):
        await self.queue.join()


class _AsyncPlayer(Player):
    actions: _AsyncQueue
    observations: _AsyncQueue

    def __init__(
        self,
        user_funcs: GymnasiumEnv,
        username: str,
        **kwargs: Any,
    ):
        self.__class__.__name__ = username
        super().__init__(**kwargs)
        self.__class__.__name__ = "_AsyncPlayer"
        self.observations = _AsyncQueue(create_in_poke_loop(asyncio.Queue, 1))
        self.actions = _AsyncQueue(create_in_poke_loop(asyncio.Queue, 1))
        self.battle: Optional[AbstractBattle] = None
        self.waiting = False
        self._user_funcs = user_funcs

    def choose_move(self, battle: AbstractBattle) -> Awaitable[BattleOrder]:
        return self._env_move(battle)

    async def _env_move(self, battle: AbstractBattle) -> BattleOrder:
        if not self.battle or self.battle.finished:
            self.battle = battle
        if not self.battle == battle:
            raise RuntimeError("Using different battles for queues")
        battle_to_send = self._user_funcs.embed_battle(battle)
        await self.observations.async_put(battle_to_send)
        self.waiting = True
        action = await self.actions.async_get()
        self.waiting = False
        if action == -1:
            return ForfeitBattleOrder()
        return self._user_funcs.action_to_move(action, battle)

    def _battle_finished_callback(self, battle: AbstractBattle):
        to_put = self._user_funcs.embed_battle(battle)
        asyncio.run_coroutine_threadsafe(self.observations.async_put(to_put), POKE_LOOP)


class GymnasiumEnv(ParallelEnv[str, ObsType, ActionType]):
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
        self.agent1 = _AsyncPlayer(
            self,
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
        self.agent2 = _AsyncPlayer(
            self,
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
        self._actions1 = self.agent1.actions
        self._observations1 = self.agent1.observations
        self._actions2 = self.agent2.actions
        self._observations2 = self.agent2.observations
        self.battle1: Optional[AbstractBattle] = None
        self.battle2: Optional[AbstractBattle] = None
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

    def step(self, actions: Dict[str, ActionType]) -> Tuple[
        Dict[str, ObsType],
        Dict[str, float],
        Dict[str, bool],
        Dict[str, bool],
        Dict[str, Dict[str, Any]],
    ]:
        assert self.battle1 is not None
        assert self.battle2 is not None
        if self.battle1.finished:
            raise RuntimeError("Battle is already finished, call reset")
        if self.agent1.waiting:
            self._actions1.put(actions[self.agents[0]])
        if self.agent2.waiting:
            self._actions2.put(actions[self.agents[1]])
        observations = {
            self.agents[0]: self._observations1.get(
                timeout=0.1, default=self.embed_battle(self.battle1)
            ),
            self.agents[1]: self._observations2.get(
                timeout=0.1, default=self.embed_battle(self.battle2)
            ),
        }
        assert self.battle1 == self.agent1.battle
        reward = {
            self.agents[0]: self.calc_reward(self.battle1),
            self.agents[1]: self.calc_reward(self.battle2),
        }
        term1, trunc1 = self.calc_term_trunc(self.battle1)
        term2, trunc2 = self.calc_term_trunc(self.battle2)
        terminated = {self.agents[0]: term1, self.agents[1]: term2}
        truncated = {self.agents[0]: trunc1, self.agents[1]: trunc2}
        if self.battle1.finished:
            self.agents = []
        return observations, reward, terminated, truncated, self.get_additional_info()

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, ObsType], Dict[str, Dict[str, Any]]]:
        self.agents = [self.agent1.username, self.agent2.username]
        # TODO: use the seed
        if not self.agent1.battle or not self.agent2.battle:
            count = self._INIT_RETRIES
            while not self.agent1.battle or not self.agent2.battle:
                if count == 0:
                    raise RuntimeError("Agent is not challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_RETRIES)
        if self.battle1 and not self.battle1.finished:
            if self.battle1 == self.agent1.battle:
                self._actions1.put(-1)
                self._actions2.put(0)
                self._observations1.get()
                self._observations2.get()
            else:
                raise RuntimeError(
                    "Environment and agent aren't synchronized. Try to restart"
                )
        while self.battle1 == self.agent1.battle:
            time.sleep(0.01)
        observations = {
            self.agents[0]: self._observations1.get(),
            self.agents[1]: self._observations2.get(),
        }
        self.battle1 = self.agent1.battle
        self.battle1.logger = None
        self.battle2 = self.agent2.battle
        self.battle2.logger = None
        return observations, self.get_additional_info()

    def render(self, mode: str = "human"):
        if self.battle1 is not None:
            print(
                "  Turn %4d. | [%s][%3d/%3dhp] %10.10s - %10.10s [%3d%%hp][%s]"
                % (
                    self.battle1.turn,
                    "".join(
                        [
                            "⦻" if mon.fainted else "●"
                            for mon in self.battle1.team.values()
                        ]
                    ),
                    self.battle1.active_pokemon.current_hp or 0,
                    self.battle1.active_pokemon.max_hp or 0,
                    self.battle1.active_pokemon.species,
                    self.battle1.opponent_active_pokemon.species,
                    self.battle1.opponent_active_pokemon.current_hp or 0,
                    "".join(
                        [
                            "⦻" if mon.fainted else "●"
                            for mon in self.battle1.opponent_team.values()
                        ]
                    ),
                ),
                end="\n" if self.battle1.finished else "\r",
            )

    def close(self, purge: bool = True):
        if self.battle1 is None or self.battle1.finished:
            time.sleep(1)
            if self.battle1 != self.agent1.battle:
                self.battle1 = self.agent1.battle
        if self.battle2 is None or self.battle2.finished:
            time.sleep(1)
            if self.battle2 != self.agent2.battle:
                self.battle2 = self.agent2.battle
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
    def calc_reward(self, battle: AbstractBattle) -> float:
        """
        Returns the reward for the current battle state.

        :param battle: The current battle state.
        :type battle: AbstractBattle

        :return: The reward for battle.
        :rtype: float
        """
        pass

    @abstractmethod
    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
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
                if callback and self.battle1 is not None:
                    callback(copy.deepcopy(self.battle1))
        elif n_challenges > 0:
            for _ in range(n_challenges):
                await self.agent1.battle_against(self.agent2, n_battles=1)
                if callback and self.battle1 is not None:
                    callback(copy.deepcopy(self.battle1))
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
                if callback and self.battle1 is not None:
                    callback(self.battle1)
        else:
            while self._keep_challenging:
                await self.agent1.ladder(1)
                if callback and self.battle1 is not None:
                    callback(self.battle1)

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
            if self.battle1 and not self.battle1.finished:
                if not (self._actions1.empty() and self._actions2.empty()):
                    await asyncio.sleep(2)
                    if not (self._actions1.empty() and self._actions2.empty()):
                        raise RuntimeError(
                            "The agent is still sending actions. "
                            "Use this method only when training or "
                            "evaluation are over."
                        )
                if not self._observations1.empty():
                    await self._observations1.async_get()
                if not self._observations2.empty():
                    await self._observations2.async_get()
                await self._actions1.async_put(-1)
                await self._actions2.async_put(0)

        if wait and self._challenge_task:
            while not self._challenge_task.done():
                await asyncio.sleep(1)
            self._challenge_task.result()

        self._challenge_task = None
        self.battle1 = None
        self.battle2 = None
        self.agent1.battle = None
        self.agent2.battle = None
        while not self._actions1.empty():
            await self._actions1.async_get()
        while not self._actions2.empty():
            await self._actions2.async_get()
        while not self._observations1.empty():
            await self._observations1.async_get()
        while not self._observations2.empty():
            await self._observations2.async_get()

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
