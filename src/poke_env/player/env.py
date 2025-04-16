"""This module defines a player class with the Gymnasium API on the main thread.
For a black-box implementation consider using the module env_player.
"""

import asyncio
import time
from abc import abstractmethod
from threading import Thread
from typing import Any, Awaitable, Dict, Generic, List, Optional, Tuple, TypeVar, Union
from weakref import WeakKeyDictionary

from gymnasium.spaces import Space
from gymnasium.utils import seeding
from numpy.random import Generator
from pettingzoo.utils.env import ParallelEnv  # type: ignore[import-untyped]

from poke_env.concurrency import create_in_poke_loop
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
ObsType = TypeVar("ObsType")
ActionType = TypeVar("ActionType")


class _AsyncQueue(Generic[ItemType]):
    def __init__(
        self,
        queue: asyncio.Queue[ItemType],
        loop: asyncio.AbstractEventLoop,
    ):
        self.queue = queue
        self.loop = loop

    async def async_get(self) -> ItemType:
        return await self.queue.get()

    def get(self) -> ItemType:
        res = asyncio.run_coroutine_threadsafe(self.async_get(), self.loop)
        return res.result()

    def race_get(self, *events: asyncio.Event) -> Optional[ItemType]:
        async def _race_get() -> Optional[ItemType]:
            get_task = asyncio.create_task(self.async_get())
            wait_tasks = [asyncio.create_task(e.wait()) for e in events]
            done, pending = await asyncio.wait(
                {get_task, *wait_tasks},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for p in pending:
                p.cancel()
            if get_task in done:
                return get_task.result()
            else:
                return None

        res = asyncio.run_coroutine_threadsafe(_race_get(), self.loop)
        return res.result()

    async def async_put(self, item: ItemType):
        await self.queue.put(item)

    def put(self, item: ItemType):
        task = asyncio.run_coroutine_threadsafe(self.queue.put(item), self.loop)
        task.result()

    def empty(self):
        return self.queue.empty()

    def join(self):
        task = asyncio.run_coroutine_threadsafe(self.queue.join(), self.loop)
        task.result()

    async def async_join(self):
        await self.queue.join()


class _EnvPlayer(Player):
    battle_queue: _AsyncQueue[AbstractBattle]
    order_queue: _AsyncQueue[BattleOrder]

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.battle_queue = _AsyncQueue(
            create_in_poke_loop(asyncio.Queue, self.ps_client.loop, 1),
            self.ps_client.loop,
        )
        self.order_queue = _AsyncQueue(
            create_in_poke_loop(asyncio.Queue, self.ps_client.loop, 1),
            self.ps_client.loop,
        )
        self.battle: Optional[AbstractBattle] = None

    def choose_move(self, battle: AbstractBattle) -> Awaitable[BattleOrder]:
        return self._env_move(battle)

    async def _env_move(self, battle: AbstractBattle) -> BattleOrder:
        if not self.battle or self.battle.finished:
            self.battle = battle
        assert self.battle.battle_tag == battle.battle_tag
        await self.battle_queue.async_put(battle)
        order = await self.order_queue.async_get()
        return order

    def _battle_finished_callback(self, battle: AbstractBattle):
        asyncio.run_coroutine_threadsafe(
            self.battle_queue.async_put(battle), self.ps_client.loop
        )


class PokeEnv(ParallelEnv[str, ObsType, ActionType]):
    """
    Base class implementing the Gymnasium API on the main thread.
    """

    _INIT_RETRIES = 100
    _TIME_BETWEEN_RETRIES = 0.5
    _SWITCH_CHALLENGE_TASK_RETRIES = 30
    _TIME_BETWEEN_SWITCH_RETRIES = 1

    def __init__(
        self,
        *,
        account_configuration1: Optional[AccountConfiguration] = None,
        account_configuration2: Optional[AccountConfiguration] = None,
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
        fake: bool = False,
        strict: bool = True,
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
        :param fake: If true, action-order converters will try to avoid returning a default
            output if at all possible, even if the output isn't a legal decision. Defaults
            to False.
        :type fake: bool
        :param strict: If true, action-order converters will throw an error if the move is
            illegal. Otherwise, it will return default. Defaults to True.
        :type: strict: bool
        """
        self._account_configuration1 = account_configuration1
        self._account_configuration2 = account_configuration2
        self._avatar = avatar
        self._battle_format = battle_format
        self._log_level = log_level
        self._save_replays = save_replays
        self._server_configuration = server_configuration
        self._accept_open_team_sheet = accept_open_team_sheet
        self._start_timer_on_battle_start = start_timer_on_battle_start
        self._start_listening = start_listening
        self._open_timeout = open_timeout
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._team = team
        self._start_challenging = start_challenging
        self._fake = fake
        self._strict = strict
        self.loop = asyncio.new_event_loop()
        Thread(target=self.loop.run_forever, daemon=True).start()
        self.agent1 = _EnvPlayer(
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
            loop=self.loop,
            team=team,
        )
        self.agent2 = _EnvPlayer(
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
            open_timeout=open_timeout,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            loop=self.loop,
            team=team,
        )
        self.agents: List[str] = []
        self.possible_agents = [self.agent1.username, self.agent2.username]
        self.battle1: Optional[AbstractBattle] = None
        self.battle2: Optional[AbstractBattle] = None
        self._np_random: Optional[Generator] = None
        self._reward_buffer: WeakKeyDictionary[AbstractBattle, float] = (
            WeakKeyDictionary()
        )
        self._keep_challenging: bool = False
        self._challenge_task = None
        if start_challenging:
            self._keep_challenging = True
            self._challenge_task = asyncio.run_coroutine_threadsafe(
                self._challenge_loop(), self.loop
            )

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        state["loop"] = None
        state["agent1"] = None
        state["agent2"] = None
        state["_reward_buffer"] = None
        state["_challenge_task"] = None
        return state

    def __setstate__(self, state: Dict[str, Any]):
        self.__dict__.update(state)
        self.loop = asyncio.new_event_loop()
        Thread(target=self.loop.run_forever, daemon=True).start()
        self.agent1 = _EnvPlayer(
            account_configuration=self._account_configuration1,
            avatar=self._avatar,
            battle_format=self._battle_format,
            log_level=self._log_level,
            max_concurrent_battles=1,
            save_replays=self._save_replays,
            server_configuration=self._server_configuration,
            accept_open_team_sheet=self._accept_open_team_sheet,
            start_timer_on_battle_start=self._start_timer_on_battle_start,
            start_listening=self._start_listening,
            open_timeout=self._open_timeout,
            ping_interval=self._ping_interval,
            ping_timeout=self._ping_timeout,
            loop=self.loop,
            team=self._team,
        )
        self.agent2 = _EnvPlayer(
            account_configuration=self._account_configuration2,
            avatar=self._avatar,
            battle_format=self._battle_format,
            log_level=self._log_level,
            max_concurrent_battles=1,
            save_replays=self._save_replays,
            server_configuration=self._server_configuration,
            accept_open_team_sheet=self._accept_open_team_sheet,
            start_timer_on_battle_start=self._start_timer_on_battle_start,
            start_listening=self._start_listening,
            ping_interval=self._ping_interval,
            ping_timeout=self._ping_timeout,
            loop=self.loop,
            team=self._team,
        )
        self.agents = [self.agent1.username, self.agent2.username]
        self.possible_agents = [self.agent1.username, self.agent2.username]
        self.observation_spaces: Dict[str, Space[ObsType]] = {
            self.possible_agents[i]: list(self.observation_spaces.values())[i]
            for i in range(len(self.possible_agents))
        }
        self.action_spaces: Dict[str, Space[ActionType]] = {
            self.possible_agents[i]: list(self.action_spaces.values())[i]
            for i in range(len(self.possible_agents))
        }
        self._reward_buffer = WeakKeyDictionary()
        self._challenge_task = asyncio.run_coroutine_threadsafe(
            self._challenge_loop(), self.loop
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
        assert not self.battle1.finished
        assert self.battle2 is not None
        assert not self.battle2.finished
        agent1_waiting = self.agent1._waiting.is_set()
        agent2_waiting = self.agent2._waiting.is_set()
        agent1_trying_again = self.agent1._trying_again.is_set()
        agent2_trying_again = self.agent2._trying_again.is_set()
        self.agent1._waiting.clear()
        self.agent2._waiting.clear()
        self.agent1._trying_again.clear()
        self.agent2._trying_again.clear()
        if not agent1_waiting and (agent1_trying_again or not agent2_trying_again):
            order1 = self.action_to_order(
                actions[self.agents[0]],
                self.battle1,
                fake=self._fake,
                strict=self._strict,
            )
            self.agent1.order_queue.put(order1)
        if not agent2_waiting and (agent2_trying_again or not agent1_trying_again):
            order2 = self.action_to_order(
                actions[self.agents[1]],
                self.battle2,
                fake=self._fake,
                strict=self._strict,
            )
            self.agent2.order_queue.put(order2)
        battle1 = self.agent1.battle_queue.race_get(
            self.agent1._waiting, self.agent2._trying_again
        )
        battle2 = self.agent2.battle_queue.race_get(
            self.agent2._waiting, self.agent1._trying_again
        )
        if battle1 is None:
            battle1 = (
                self.agent1.battle_queue.get()
                if self.agent1._trying_again.is_set()
                else self.battle1
            )
        if battle2 is None:
            battle2 = (
                self.agent2.battle_queue.get()
                if self.agent2._trying_again.is_set()
                else self.battle2
            )
        observations = {
            self.agents[0]: self.embed_battle(battle1),
            self.agents[1]: self.embed_battle(battle2),
        }
        reward = {
            self.agents[0]: self.calc_reward(battle1),
            self.agents[1]: self.calc_reward(battle2),
        }
        term1, trunc1 = self.calc_term_trunc(battle1)
        term2, trunc2 = self.calc_term_trunc(battle2)
        terminated = {self.agents[0]: term1, self.agents[1]: term2}
        truncated = {self.agents[0]: trunc1, self.agents[1]: trunc2}
        if battle1.finished:
            self.agents = []
        return observations, reward, terminated, truncated, self.get_additional_info()

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, ObsType], Dict[str, Dict[str, Any]]]:
        self.agents = [self.agent1.username, self.agent2.username]
        if seed is not None:
            self._np_random, seed = seeding.np_random(seed)
        if not self.agent1.battle or not self.agent2.battle:
            count = self._INIT_RETRIES
            while not self.agent1.battle or not self.agent2.battle:
                if count == 0:
                    raise RuntimeError("Agent is not challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_RETRIES)
        if self.battle1 and not self.battle1.finished:
            assert self.battle2 is not None
            if self.battle1 == self.agent1.battle:
                agent1_waiting = self.agent1._waiting.is_set()
                agent2_waiting = self.agent2._waiting.is_set()
                agent1_trying_again = self.agent1._trying_again.is_set()
                agent2_trying_again = self.agent2._trying_again.is_set()
                self.agent1._waiting.clear()
                self.agent2._waiting.clear()
                self.agent1._trying_again.clear()
                self.agent2._trying_again.clear()
                if not agent1_waiting and (
                    agent1_trying_again or not agent2_trying_again
                ):
                    self.agent1.order_queue.put(ForfeitBattleOrder())
                    if not agent2_waiting and (
                        agent2_trying_again or not agent1_trying_again
                    ):
                        self.agent2.order_queue.put(DefaultBattleOrder())
                else:
                    self.agent2.order_queue.put(ForfeitBattleOrder())
                self.agent1.battle_queue.get()
                self.agent2.battle_queue.get()
            else:
                raise RuntimeError(
                    "Environment and agent aren't synchronized. Try to restart"
                )
        self.battle1 = self.agent1.battle_queue.get()
        self.battle2 = self.agent2.battle_queue.get()
        observations = {
            self.agents[0]: self.embed_battle(self.battle1),
            self.agents[1]: self.embed_battle(self.battle2),
        }
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
            self._stop_challenge_loop(purge=purge), self.loop
        )
        closing_task.result()

    def observation_space(self, agent: str) -> Space[ObsType]:
        return self.observation_spaces[agent]

    def action_space(self, agent: str) -> Space[ActionType]:
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
    def embed_battle(self, battle: AbstractBattle) -> ObsType:
        """
        Returns the embedding of the current battle state in a format compatible with
        the Gymnasium API.

        :param battle: The current battle state.
        :type battle: AbstractBattle

        :return: The embedding of the current battle state.
        """
        pass

    @staticmethod
    @abstractmethod
    def action_to_order(
        action: ActionType, battle: Any, fake: bool = False, strict: bool = True
    ) -> BattleOrder:
        """
        Returns the BattleOrder relative to the given action.

        :param action: The action to take.
        :type action: ActionType
        :param battle: The current battle state
        :type battle: AbstractBattle

        :return: The battle order for the given action in context of the current battle.
        :rtype: BattleOrder
        """
        pass

    @staticmethod
    @abstractmethod
    def order_to_action(
        order: BattleOrder, battle: Any, fake: bool = False, strict: bool = True
    ) -> ActionType:
        """
        Returns the action relative to the given BattleOrder.

        :param order: The order to take.
        :type order: BattleOrder
        :param battle: The current battle state
        :type battle: AbstractBattle

        :return: The action for the given battle order in context of the current battle.
        :rtype: ActionType
        """
        pass

    ###################################################################################
    # Helper methods

    def reward_computing_helper(
        self,
        battle: AbstractBattle,
        *,
        fainted_value: float = 0.0,
        hp_value: float = 0.0,
        number_of_pokemons: int = 6,
        starting_value: float = 0.0,
        status_value: float = 0.0,
        victory_value: float = 1.0,
    ) -> float:
        """A helper function to compute rewards.

        The reward is computed by computing the value of a game state, and by comparing
        it to the last state.

        State values are computed by weighting different factor. Fainted pokemons,
        their remaining HP, inflicted statuses and winning are taken into account.

        For instance, if the last time this function was called for battle A it had
        a state value of 8 and this call leads to a value of 9, the returned reward will
        be 9 - 8 = 1.

        Consider a single battle where each player has 6 pokemons. No opponent pokemon
        has fainted, but our team has one fainted pokemon. Three opposing pokemons are
        burned. We have one pokemon missing half of its HP, and our fainted pokemon has
        no HP left.

        The value of this state will be:

        - With fainted value: 1, status value: 0.5, hp value: 1:
            = - 1 (fainted) + 3 * 0.5 (status) - 1.5 (our hp) = -1
        - With fainted value: 3, status value: 0, hp value: 1:
            = - 3 + 3 * 0 - 1.5 = -4.5

        :param battle: The battle for which to compute rewards.
        :type battle: AbstractBattle
        :param fainted_value: The reward weight for fainted pokemons. Defaults to 0.
        :type fainted_value: float
        :param hp_value: The reward weight for hp per pokemon. Defaults to 0.
        :type hp_value: float
        :param number_of_pokemons: The number of pokemons per team. Defaults to 6.
        :type number_of_pokemons: int
        :param starting_value: The default reference value evaluation. Defaults to 0.
        :type starting_value: float
        :param status_value: The reward value per non-fainted status. Defaults to 0.
        :type status_value: float
        :param victory_value: The reward value for winning. Defaults to 1.
        :type victory_value: float
        :return: The reward.
        :rtype: float
        """
        if battle not in self._reward_buffer:
            self._reward_buffer[battle] = starting_value
        current_value = 0.0

        for mon in battle.team.values():
            current_value += mon.current_hp_fraction * hp_value
            if mon.fainted:
                current_value -= fainted_value
            elif mon.status is not None:
                current_value -= status_value

        current_value += (number_of_pokemons - len(battle.team)) * hp_value

        for mon in battle.opponent_team.values():
            current_value -= mon.current_hp_fraction * hp_value
            if mon.fainted:
                current_value += fainted_value
            elif mon.status is not None:
                current_value += status_value

        current_value -= (number_of_pokemons - len(battle.opponent_team)) * hp_value

        if battle.won:
            current_value += victory_value
        elif battle.lost:
            current_value -= victory_value

        to_return = current_value - self._reward_buffer[battle]
        self._reward_buffer[battle] = current_value

        return to_return

    def reset_env(self, restart: bool = True):
        """
        Resets the environment to an inactive state: it will forfeit all unfinished
        battles, reset the internal battle tracker and optionally change the next
        opponent and restart the challenge loop.

        :param opponent: The opponent to use for the next battles. If empty it
            will not change opponent.
        :type opponent: Player or str, optional
        :param restart: If True the challenge loop will be restarted before returning,
            otherwise the challenge loop will be left inactive and can be
            started manually.
        :type restart: bool
        """
        self.close(purge=False)
        self.reset_battles()
        if restart:
            self.start_challenging()

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
            self.agent1.send_challenges(username, 1), self.loop
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
            self.agent1.accept_challenges(username, 1, self.agent1.next_team),
            self.loop,
        )

    async def _challenge_loop(self, n_challenges: Optional[int] = None):
        if not n_challenges:
            while self._keep_challenging:
                await self.agent1.battle_against(self.agent2, n_battles=1)
        elif n_challenges > 0:
            for _ in range(n_challenges):
                await self.agent1.battle_against(self.agent2, n_battles=1)
        else:
            raise ValueError(f"Number of challenges must be > 0. Got {n_challenges}")

    def start_challenging(self, n_challenges: Optional[int] = None):
        """
        Starts the challenge loop.
        :param n_challenges: The number of challenges to send. If empty it will run until
            stopped.
        :type n_challenges: int, optional
        """
        if self._challenge_task and not self._challenge_task.done():
            count = self._SWITCH_CHALLENGE_TASK_RETRIES
            while not self._challenge_task.done():
                if count == 0:
                    raise RuntimeError("Agent is already challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_SWITCH_RETRIES)
        if not n_challenges:
            self._keep_challenging = True
        self._challenge_task = asyncio.run_coroutine_threadsafe(
            self._challenge_loop(n_challenges), self.loop
        )

    async def _ladder_loop(self, n_challenges: Optional[int] = None):
        if n_challenges:
            if n_challenges <= 0:
                raise ValueError(
                    f"Number of challenges must be > 0. Got {n_challenges}"
                )
            for _ in range(n_challenges):
                await self.agent1.ladder(1)
        else:
            while self._keep_challenging:
                await self.agent1.ladder(1)

    def start_laddering(self, n_challenges: Optional[int] = None):
        """
        Starts the laddering loop.

        :param n_challenges: The number of ladder games to play. If empty it
            will run until stopped.
        :type n_challenges: int, optional
        """
        if self._challenge_task and not self._challenge_task.done():
            count = self._SWITCH_CHALLENGE_TASK_RETRIES
            while not self._challenge_task.done():
                if count == 0:
                    raise RuntimeError("Agent is already challenging")
                count -= 1
                time.sleep(self._TIME_BETWEEN_SWITCH_RETRIES)
        if not n_challenges:
            self._keep_challenging = True
        self._challenge_task = asyncio.run_coroutine_threadsafe(
            self._ladder_loop(n_challenges), self.loop
        )

    async def _stop_challenge_loop(
        self, force: bool = True, wait: bool = True, purge: bool = False
    ):
        self._keep_challenging = False

        if force:
            if self.battle1 and not self.battle1.finished:
                assert self.battle2 is not None
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
                agent1_waiting = self.agent1._waiting.is_set()
                agent2_waiting = self.agent2._waiting.is_set()
                agent1_trying_again = self.agent1._trying_again.is_set()
                agent2_trying_again = self.agent2._trying_again.is_set()
                self.agent1._waiting.clear()
                self.agent2._waiting.clear()
                self.agent1._trying_again.clear()
                self.agent2._trying_again.clear()
                if not agent1_waiting and (
                    agent1_trying_again or not agent2_trying_again
                ):
                    await self.agent1.order_queue.async_put(ForfeitBattleOrder())
                    if not agent2_waiting and (
                        agent2_trying_again or not agent1_trying_again
                    ):
                        await self.agent2.order_queue.async_put(DefaultBattleOrder())
                else:
                    await self.agent2.order_queue.async_put(ForfeitBattleOrder())

        if wait and self._challenge_task:
            while not self._challenge_task.done():
                await asyncio.sleep(1)
            self._challenge_task.result()

        self._challenge_task = None
        self.battle1 = None
        self.battle2 = None
        self.agent1.battle = None
        self.agent2.battle = None
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
