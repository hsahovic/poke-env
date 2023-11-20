"""This module defines a player class with the OpenAI API on the main thread.
For a black-box implementation consider using the module env_player.
"""
from __future__ import annotations

import asyncio
import copy
import random
import time
from abc import ABC, abstractmethod
from logging import Logger
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

from gym.core import ActType, Env, ObsType
from gym.spaces import Discrete, Space

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

BattleType = TypeVar("BattleType", bound=AbstractBattle)


class _AsyncQueue:
    def __init__(self, queue: asyncio.Queue[Any]):
        self.queue = queue

    async def async_get(self):
        return await self.queue.get()

    def get(self):
        res = asyncio.run_coroutine_threadsafe(self.queue.get(), POKE_LOOP)
        return res.result()

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


class _AsyncPlayer(Generic[ObsType, ActType], Player):
    actions: _AsyncQueue
    observations: _AsyncQueue

    def __init__(
        self,
        user_funcs: OpenAIGymEnv[ObsType, ActType],
        username: str,
        **kwargs: Any,
    ):
        self.__class__.__name__ = username
        super().__init__(**kwargs)
        self.__class__.__name__ = "_AsyncPlayer"
        self.observations = _AsyncQueue(create_in_poke_loop(asyncio.Queue, 1))
        self.actions = _AsyncQueue(create_in_poke_loop(asyncio.Queue, 1))
        self.current_battle: Optional[AbstractBattle] = None
        self._user_funcs = user_funcs

    def choose_move(
        self, battle: AbstractBattle
    ) -> Union[BattleOrder, Awaitable[BattleOrder]]:
        return self._env_move(battle)

    async def _env_move(self, battle: AbstractBattle):
        if not self.current_battle or self.current_battle.finished:
            self.current_battle = battle
        if not self.current_battle == battle:
            raise RuntimeError("Using different battles for queues")
        battle_to_send = self._user_funcs.embed_battle(battle)
        await self.observations.async_put(battle_to_send)
        action = await self.actions.async_get()
        if action == -1:
            return ForfeitBattleOrder()
        return self._user_funcs.action_to_move(action, battle)

    def _battle_finished_callback(self, battle: AbstractBattle):
        to_put = self._user_funcs.embed_battle(battle)
        asyncio.run_coroutine_threadsafe(self.observations.async_put(to_put), POKE_LOOP)


class _ABCMetaclass(type(ABC)):
    pass


class _EnvMetaclass(type(Env)):
    pass


class _OpenAIGymEnvMetaclass(_EnvMetaclass, _ABCMetaclass):
    pass


class OpenAIGymEnv(
    Env[ObsType, ActType],
    ABC,
    metaclass=_OpenAIGymEnvMetaclass,
):
    """
    Base class implementing the OpenAI Gym API on the main thread.
    """

    _INIT_RETRIES = 100
    _TIME_BETWEEN_RETRIES = 0.5
    _SWITCH_CHALLENGE_TASK_RETRIES = 30
    _TIME_BETWEEN_SWITCH_RETIRES = 1

    def __init__(
        self,
        account_configuration: Optional[AccountConfiguration] = None,
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
        :param start_timer_on_battle_start: Whether to automatically start the battle
            timer on battle start. Defaults to False.
        :type start_timer_on_battle_start: bool
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
        self.agent = _AsyncPlayer(
            self,
            username=self.__class__.__name__,  # type: ignore
            account_configuration=account_configuration,
            avatar=avatar,
            battle_format=battle_format,
            log_level=log_level,
            max_concurrent_battles=1,
            save_replays=save_replays,
            server_configuration=server_configuration,
            start_timer_on_battle_start=start_timer_on_battle_start,
            start_listening=start_listening,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            team=team,
        )
        self._actions = self.agent.actions
        self._observations = self.agent.observations
        self.action_space = Discrete(self.action_space_size())  # type: ignore
        self.observation_space = self.describe_embedding()
        self.current_battle: Optional[AbstractBattle] = None
        self.last_battle: Optional[AbstractBattle] = None
        self._keep_challenging: bool = False
        self._challenge_task = None
        self._seed_initialized: bool = False
        if start_challenging:
            self._keep_challenging = True
            self._challenge_task = asyncio.run_coroutine_threadsafe(
                self._challenge_loop(), POKE_LOOP
            )

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
        the OpenAI gym API.

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

    @abstractmethod
    def get_opponent(
        self,
    ) -> Union[Player, str, List[Player], List[str]]:
        """
        Returns the opponent (or list of opponents) that will be challenged
        on the next iteration of the challenge loop. If a list is returned,
        a random element will be chosen at random during the challenge loop.

        :return: The opponent (or list of opponents).
        :rtype: Player or str or list(Player) or list(str)
        """
        pass

    def _get_opponent(self) -> Union[Player, str]:
        opponent = self.get_opponent()
        random_opponent = (
            random.choice(opponent) if isinstance(opponent, list) else opponent
        )
        return random_opponent

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        return_info: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ObsType, Dict[str, Any]]:
        if seed is not None:
            super().reset(seed=seed)  # type: ignore
            self._seed_initialized = True
        elif not self._seed_initialized:
            super().reset(seed=int(time.time()))  # type: ignore
            self._seed_initialized = True
        if not self.agent.current_battle:
            count = self._INIT_RETRIES
            while not self.agent.current_battle:
                if count == 0:
                    raise RuntimeError("Agent is not challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_RETRIES)
        if self.current_battle and not self.current_battle.finished:
            if self.current_battle == self.agent.current_battle:
                self._actions.put(-1)
                self._observations.get()
            else:
                raise RuntimeError(
                    "Environment and agent aren't synchronized. Try to restart"
                )
        while self.current_battle == self.agent.current_battle:
            time.sleep(0.01)
        self.current_battle = self.agent.current_battle
        battle = copy.copy(self.current_battle)
        battle.logger = None
        self.last_battle = copy.deepcopy(battle)
        return self._observations.get(), self.get_additional_info()

    def get_additional_info(self) -> Dict[str, Any]:
        """
        Returns additional info for the reset method.
        Override only if you really need it.

        :return: Additional information as a Dict
        :rtype: Dict
        """
        return {}

    def step(
        self, action: ActType
    ) -> Tuple[ObsType, float, bool, bool, Dict[str, Any]]:
        """
        Execute the specified action in the environment.

        :param ActType action: The action to be executed.
        :return: A tuple containing the new observation, reward, termination flag, truncation flag, and info dictionary.
        :rtype: Tuple[ObsType, float, bool, bool, Dict[str, Any]]
        """
        if not self.current_battle:
            obs, info = self.reset(return_info=True)
            return obs, 0.0, False, False, info
        if self.current_battle.finished:
            raise RuntimeError("Battle is already finished, call reset")
        battle = copy.copy(self.current_battle)
        battle.logger = None
        self.last_battle = copy.deepcopy(battle)
        self._actions.put(action)
        observation = self._observations.get()
        reward = self.calc_reward(self.last_battle, self.current_battle)
        terminated = False
        truncated = False
        if self.current_battle.finished:
            size = self.current_battle.team_size
            remaining_mons = size - len(
                [mon for mon in self.current_battle.team.values() if mon.fainted]
            )
            remaining_opponent_mons = size - len(
                [
                    mon
                    for mon in self.current_battle.opponent_team.values()
                    if mon.fainted
                ]
            )
            if (remaining_mons == 0) != (remaining_opponent_mons == 0):
                terminated = True
            else:
                truncated = True
        return observation, reward, terminated, truncated, self.get_additional_info()

    def render(self, mode: str = "human"):
        if self.current_battle is not None:
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

    def close(self, purge: bool = True):
        if self.current_battle is None or self.current_battle.finished:
            time.sleep(1)
            if self.current_battle != self.agent.current_battle:
                self.current_battle = self.agent.current_battle
        closing_task = asyncio.run_coroutine_threadsafe(
            self._stop_challenge_loop(purge=purge), POKE_LOOP
        )
        closing_task.result()

    def seed(self, seed: Optional[int] = None):
        random.seed(seed)

    def background_send_challenge(self, username: str):
        """
        Sends a single challenge specified player. The function immediately returns
        to allow use of the OpenAI gym API.

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
            self.agent.send_challenges(username, 1), POKE_LOOP
        )

    def background_accept_challenge(self, username: str):
        """
        Accepts a single challenge specified player. The function immediately returns
        to allow use of the OpenAI gym API.

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
            self.agent.accept_challenges(username, 1, self.agent.next_team), POKE_LOOP
        )

    async def _challenge_loop(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):
        if not n_challenges:
            while self._keep_challenging:
                opponent = self._get_opponent()
                if isinstance(opponent, Player):
                    await self.agent.battle_against(opponent, 1)
                else:
                    await self.agent.send_challenges(opponent, 1)
                if callback and self.current_battle is not None:
                    callback(copy.deepcopy(self.current_battle))
        elif n_challenges > 0:
            for _ in range(n_challenges):
                opponent = self._get_opponent()
                if isinstance(opponent, Player):
                    await self.agent.battle_against(opponent, 1)
                else:
                    await self.agent.send_challenges(opponent, 1)
                if callback and self.current_battle is not None:
                    callback(copy.deepcopy(self.current_battle))
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
                await self.agent.ladder(1)
                if callback and self.current_battle is not None:
                    callback(copy.deepcopy(self.current_battle))
        else:
            while self._keep_challenging:
                await self.agent.ladder(1)
                if callback and self.current_battle is not None:
                    callback(copy.deepcopy(self.current_battle))

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
            if self.current_battle and not self.current_battle.finished:
                if not self._actions.empty():
                    await asyncio.sleep(2)
                    if not self._actions.empty():
                        raise RuntimeError(
                            "The agent is still sending actions. "
                            "Use this method only when training or "
                            "evaluation are over."
                        )
                if not self._observations.empty():
                    await self._observations.async_get()
                await self._actions.async_put(-1)

        if wait and self._challenge_task:
            while not self._challenge_task.done():
                await asyncio.sleep(1)
            self._challenge_task.result()

        self._challenge_task = None
        self.current_battle = None
        self.agent.current_battle = None
        while not self._actions.empty():
            await self._actions.async_get()
        while not self._observations.empty():
            await self._observations.async_get()

        if purge:
            self.agent.reset_battles()

    def reset_battles(self):
        """Resets the player's inner battle tracker."""
        self.agent.reset_battles()

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
        """Event object associated with user login.

        :return: The logged-in event
        :rtype: Event
        """
        return self.agent.ps_client.logged_in

    @property
    def logger(self) -> Logger:
        """Logger associated with the player.

        :return: The logger.
        :rtype: Logger
        """
        return self.agent.logger

    @property
    def username(self) -> str:
        """The player's username.

        :return: The player's username.
        :rtype: str
        """
        return self.agent.username

    @property
    def websocket_url(self) -> str:
        """The websocket url.

        It is derived from the server url.

        :return: The websocket url.
        :rtype: str
        """
        return self.agent.ps_client.websocket_url

    def __getattr__(self, item: str):
        return getattr(self.agent, item)


class LegacyOpenAIGymEnv(OpenAIGymEnv[ObsType, ActType], ABC):
    """
    Subclass of OpenAIGymEnv compatible with the old gym API.
    If you need compatibility with the old gym API you should use the
    `wrap_for_old_gym_api` function.
    """

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        return_info: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ObsType, Dict[str, Any]]:
        obs, info = super().reset(seed=seed, return_info=True, options=options)
        return obs, info

    def step(
        self, action: ActType
    ) -> Tuple[ObsType, float, bool, bool, Dict[str, Any]]:
        """
        Execute the specified action in the environment.

        :param ActType action: The action to be executed.
        :return: A tuple containing the new observation, reward, termination flag, truncation flag, and info dictionary.
        :rtype: Tuple[ObsType, float, bool, bool, Dict[str, Any]]
        """
        obs, reward, terminated, truncated, info = super().step(action)
        return obs, reward, terminated, truncated, info


class _OpenAIGymEnvWrapper(LegacyOpenAIGymEnv[ObsType, ActType]):
    def __init__(self, environment: OpenAIGymEnv[ObsType, ActType]):
        self._wrapped = environment
        self.step = super().step.__get__(self._wrapped, self._wrapped.__class__)
        self.reset = super().reset.__get__(self._wrapped, self._wrapped.__class__)
        self._instantiated = True

    def calc_reward(
        self, last_battle: AbstractBattle, current_battle: AbstractBattle
    ) -> float:
        return self._wrapped.calc_reward(last_battle, current_battle)

    def action_to_move(self, action: int, battle: AbstractBattle) -> BattleOrder:
        return self._wrapped.action_to_move(action, battle)

    def embed_battle(self, battle: AbstractBattle) -> ObsType:
        return self._wrapped.embed_battle(battle)

    def describe_embedding(self) -> Space[ObsType]:
        return self._wrapped.describe_embedding()

    def action_space_size(self) -> int:
        return self._wrapped.action_space_size()

    def get_opponent(self) -> Union[Player, str, List[Player], List[str]]:
        return self._wrapped.get_opponent()

    def __getattr__(self, item: str):
        if item == "_instantiated":
            return False
        return getattr(self._wrapped, item)

    def __setattr__(self, key: str, value: Any):
        if not self._instantiated:
            return super().__setattr__(key, value)
        return setattr(self._wrapped, key, value)


def wrap_for_old_gym_api(
    env: OpenAIGymEnv[ObsType, ActType]
) -> LegacyOpenAIGymEnv[ObsType, ActType]:
    """
    Wraps an OpenAIGymEnv in order to support the old gym API.

    :param env: the environment to wrap.
    :type env: OpenAIGymEnv

    :return: The wrapped environment
    :rtype: OpenAIGymEnv
    """
    return _OpenAIGymEnvWrapper(env)
