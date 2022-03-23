# -*- coding: utf-8 -*-
"""This module defines a player class with the OpenAI API on the main thread.
For a black-box implementation consider using the module env_player.
"""
import asyncio
import copy
import numpy as np  # pyre-ignore
import time

from abc import ABC, abstractmethod
from logging import Logger
from typing import Union, Awaitable, Optional, Tuple, TypeVar, Callable, Dict, List
from gym.core import Env  # pyre-ignore
from gym.spaces import Space, Discrete  # pyre-ignore

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.player.internals import POKE_LOOP
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


class _AsyncQueue:
    def __init__(self, queue: asyncio.Queue):
        if not isinstance(queue, asyncio.Queue):
            raise RuntimeError(f"Expected asyncio.Queue, got {type(queue)}")
        self.queue = queue

    async def async_get(self):
        return await self.queue.get()

    def get(self):
        res = asyncio.run_coroutine_threadsafe(self.queue.get(), POKE_LOOP)
        return res.result()

    async def async_put(self, item):
        await self.queue.put(item)

    def put(self, item):
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
    def __init__(self, user_funcs, username, **kwargs):
        self.__class__.__name__ = username
        super().__init__(**kwargs)
        self.__class__.__name__ = "_AsyncPlayer"
        self.observations = _AsyncQueue(self._create_class(asyncio.Queue, 1))
        self.actions = _AsyncQueue(self._create_class(asyncio.Queue, 1))
        self.current_battle: Optional[AbstractBattle] = None
        self.user_funcs: OpenAIGymEnv = user_funcs

    def choose_move(
        self, battle: AbstractBattle
    ) -> Union[BattleOrder, Awaitable[BattleOrder]]:
        return self.env_move(battle)

    async def env_move(self, battle: AbstractBattle):
        if not self.current_battle or self.current_battle.finished:
            self.current_battle = battle
        if not self.current_battle == battle:  # pragma: no cover
            raise RuntimeError("Using different battles for queues")
        battle_to_send = self.user_funcs.embed_battle(battle)
        await self.observations.async_put(battle_to_send)
        action = await self.actions.async_get()
        if action == -1:
            return ForfeitBattleOrder()
        return self.user_funcs.action_to_move(action, battle)

    def _battle_finished_callback(
        self, battle: AbstractBattle
    ) -> None:  # pragma: no cover
        to_put = self.user_funcs.embed_battle(battle)
        asyncio.run_coroutine_threadsafe(self.observations.async_put(to_put), POKE_LOOP)


class OpenAIGymEnv(Env, ABC):  # pyre-ignore

    _INIT_RETRIES = 100
    _TIME_BETWEEN_RETRIES = 0.5
    _SWITCH_CHALLENGE_TASK_RETRIES = 30
    _TIME_BETWEEN_SWITCH_RETIRES = 1

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
        start_challenging: bool = False,
    ):
        """
        :param player_configuration: Player configuration. If empty, defaults to an
            automatically generated username with no password. This option must be set
            if the server configuration requires authentication.
        :type player_configuration: PlayerConfiguration, optional
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
            self._keep_challenging = True
            self.challenge_task = asyncio.run_coroutine_threadsafe(
                self._challenge_loop(), POKE_LOOP
            )

    @abstractmethod
    def calc_reward(
        self, last_battle: AbstractBattle, current_battle: AbstractBattle
    ) -> float:  # pragma: no cover
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
    def action_to_move(
        self, action: int, battle: AbstractBattle
    ) -> BattleOrder:  # pragma: no cover
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
    def embed_battle(
        self, battle: AbstractBattle
    ) -> ObservationType:  # pyre-ignore  # pragma: no cover
        """
        Returns the embedding of the current battle state in a format compatible with
        the OpenAI gym API.

        :param battle: The current battle state.
        :type battle: AbstractBattle
        :return: The embedding of the current battle state.
        """
        pass

    @abstractmethod
    def describe_embedding(self) -> Space:  # pyre-ignore  # pragma: no cover
        """
        Returns the description of the embedding. It must return a Space specifying
        low bounds and high bounds.

        :return: The description of the embedding.
        :rtype: Space
        """
        pass

    @abstractmethod
    def action_space_size(self) -> int:  # pragma: no cover
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
    ) -> Union[Player, str, List[Player], List[str]]:  # pragma: no cover
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
        if isinstance(opponent, list):
            opponent = np.random.choice(opponent)
            if not isinstance(opponent, Player) and not isinstance(opponent, str):
                raise RuntimeError(
                    f"Expected List[Player] or List[str]. Got List[{type(opponent)}]"
                )
        return opponent

    def reset(
        self,
        *,
        seed: Optional[int] = None,
    ) -> ObservationType:  # pyre-ignore  # pragma: no cover
        if seed:
            self.seed(seed)
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
        battle = copy.copy(self.current_battle)
        battle.logger = None  # pyre-ignore
        self.last_battle = copy.deepcopy(battle)
        return self.observations.get()

    def step(
        self, action: ActionType
    ) -> Tuple[ObservationType, float, bool, dict]:  # pyre-ignore  # pragma: no cover
        if not self.current_battle:
            return self.reset(), 0.0, False, {}
        if self.current_battle.finished:
            raise RuntimeError("Battle is already finished, call reset")
        battle = copy.copy(self.current_battle)
        battle.logger = None  # pyre-ignore
        self.last_battle = copy.deepcopy(battle)
        self.actions.put(action)
        observation = self.observations.get()
        reward = self.calc_reward(self.last_battle, self.current_battle)  # pyre-ignore
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

    def close(self, purge: bool = True):  # pragma: no cover
        if self.current_battle is None or self.current_battle.finished:
            time.sleep(1)
            if self.current_battle != self.agent.current_battle:
                self.current_battle = self.agent.current_battle
        closing_task = asyncio.run_coroutine_threadsafe(
            self._stop_challenge_loop(purge=purge), POKE_LOOP
        )
        closing_task.result()

    def seed(self, seed=None):  # pragma: no cover
        np.random.seed(seed)

    def play_against(self, username: str):  # pragma: no cover
        """
        Starts a match against the specified player. The function immediately returns
        to allow use of the OpenAI gym API.

        :param username: The username of the player to challenge.
        :type username: str
        """
        if self.challenge_task and not self.challenge_task.done():
            raise RuntimeError(
                "Agent is already challenging opponents with the challenging loop. "
                "Try to specify 'start_challenging=True' during instantiation or call "
                "'await agent.stop_challenge_loop()' to clear the task."
            )
        self.challenge_task = asyncio.run_coroutine_threadsafe(
            self.agent.send_challenges(username, 1), POKE_LOOP
        )

    async def _challenge_loop(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):  # pragma: no cover
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
    ):  # pragma: no cover
        """
        Starts the challenge loop.

        :param n_challenges: The number of challenges to send. If empty it will run until
            stopped.
        :type n_challenges: int, optional
        :param callback: The function to callback after each challenge with a copy of
            the final battle state.
        :type callback: Callable[[AbstractBattle], None], optional
        """
        if self.challenge_task and not self.challenge_task.done():
            count = self._SWITCH_CHALLENGE_TASK_RETRIES
            while not self.challenge_task.done():
                if count == 0:
                    raise RuntimeError("Agent is already challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_SWITCH_RETIRES)
        if not n_challenges:
            self._keep_challenging = True
        self.challenge_task = asyncio.run_coroutine_threadsafe(
            self._challenge_loop(n_challenges, callback), POKE_LOOP
        )

    async def _ladder_loop(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):  # pragma: no cover
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
    ):  # pragma: no cover
        """
        Starts the laddering loop.

        :param n_challenges: The number of ladder games to play. If empty it
            will run until stopped.
        :type n_challenges: int, optional
        :param callback: The function to callback after each challenge with a
            copy of the final battle state.
        :type callback: Callable[[AbstractBattle], None], optional
        """
        if self.challenge_task and not self.challenge_task.done():
            count = self._SWITCH_CHALLENGE_TASK_RETRIES
            while not self.challenge_task.done():
                if count == 0:
                    raise RuntimeError("Agent is already challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_SWITCH_RETIRES)
        if not n_challenges:
            self._keep_challenging = True
        self.challenge_task = asyncio.run_coroutine_threadsafe(
            self._ladder_loop(n_challenges, callback), POKE_LOOP
        )

    async def _stop_challenge_loop(
        self, force: bool = True, wait: bool = True, purge: bool = False
    ):  # pragma: no cover
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

        if wait and self.challenge_task:
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

    def reset_battles(self):  # pragma: no cover
        """Resets the player's inner battle tracker."""
        self.agent.reset_battles()

    def done(self, timeout: Optional[int] = None) -> bool:  # pragma: no cover
        """
        Returns True if the task is done or is done after the timeout, false otherwise.

        :param timeout: The amount of time to wait for if the task is not already done.
            If empty it will wait until the task is done.
        :type timeout: int, optional
        :return: True if the task is done or if the task gets completed after the
            timeout.
        :rtype: bool
        """
        if timeout is None:
            self.challenge_task.result()
            return True
        if self.challenge_task.done():
            return True
        time.sleep(timeout)
        return self.challenge_task.done()

    # Expose properties of Player class

    @property
    def battles(self) -> Dict[str, AbstractBattle]:  # pragma: no cover
        return self.agent.battles

    @property
    def format(self) -> str:  # pragma: no cover
        return self.agent.format

    @property
    def format_is_doubles(self) -> bool:  # pragma: no cover
        return self.agent.format_is_doubles

    @property
    def n_finished_battles(self) -> int:  # pragma: no cover
        return self.agent.n_finished_battles

    @property
    def n_lost_battles(self) -> int:  # pragma: no cover
        return self.agent.n_lost_battles

    @property
    def n_tied_battles(self) -> int:  # pragma: no cover
        return self.agent.n_tied_battles

    @property
    def n_won_battles(self) -> int:  # pragma: no cover
        return self.agent.n_won_battles

    @property
    def win_rate(self) -> float:  # pragma: no cover
        return self.agent.win_rate

    # Expose properties of Player Network Interface Class

    @property
    def logged_in(self) -> asyncio.Event:  # pragma: no cover
        """Event object associated with user login.

        :return: The logged-in event
        :rtype: Event
        """
        return self.agent.logged_in

    @property
    def logger(self) -> Logger:  # pragma: no cover
        """Logger associated with the player.

        :return: The logger.
        :rtype: Logger
        """
        return self.agent.logger

    @property
    def username(self) -> str:  # pragma: no cover
        """The player's username.

        :return: The player's username.
        :rtype: str
        """
        return self.agent.username

    @property
    def websocket_url(self) -> str:  # pragma: no cover
        """The websocket url.

        It is derived from the server url.

        :return: The websocket url.
        :rtype: str
        """
        return self.agent.websocket_url
