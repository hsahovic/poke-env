"""This module defines a player class with the Gymnasium API on the main thread.
For a black-box implementation consider using the module env_player.
"""

import asyncio
import time
from abc import abstractmethod
from concurrent.futures import Future
from typing import Any, Awaitable, Dict, Generic, List, Optional, Tuple, TypeVar, Union
from weakref import WeakKeyDictionary

from gymnasium.spaces import Space
from gymnasium.utils import seeding
from numpy.random import Generator
from pettingzoo.utils.env import ParallelEnv  # type: ignore[import-untyped]

from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.battle.battle import Battle
from poke_env.battle.double_battle import DoubleBattle
from poke_env.battle.pokemon import Pokemon
from poke_env.concurrency import POKE_LOOP, create_in_poke_loop
from poke_env.player.battle_order import (
    BattleOrder,
    DoubleBattleOrder,
    ForfeitBattleOrder,
    _EmptyBattleOrder,
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
    def __init__(self, queue: asyncio.Queue[ItemType]):
        self.queue = queue

    async def async_get(self) -> ItemType:
        return await self.queue.get()

    def get(self, timeout: Optional[float] = None) -> ItemType:
        res = asyncio.run_coroutine_threadsafe(
            asyncio.wait_for(self.async_get(), timeout), POKE_LOOP
        )
        return res.result()

    def race_get(self, *events: asyncio.Event) -> Optional[ItemType]:
        async def _race_get() -> Optional[ItemType]:
            get_task = asyncio.create_task(self.async_get())
            wait_tasks = [asyncio.create_task(e.wait()) for e in events]
            done, pending = await asyncio.wait(
                {get_task, *wait_tasks}, return_when=asyncio.FIRST_COMPLETED
            )
            for p in pending:
                p.cancel()
            if get_task in done:
                return get_task.result()
            else:
                return None

        res = asyncio.run_coroutine_threadsafe(_race_get(), POKE_LOOP)
        return res.result()

    async def async_put(self, item: ItemType):
        await self.queue.put(item)

    def put(self, item: ItemType):
        task = asyncio.run_coroutine_threadsafe(self.queue.put(item), POKE_LOOP)
        task.result()

    def empty(self):
        return self.queue.empty()


class _EnvPlayer(Player):
    battle_queue: _AsyncQueue[AbstractBattle]
    order_queue: _AsyncQueue[BattleOrder]

    def __init__(
        self, *args: Any, choose_on_teampreview: bool | None = None, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        if choose_on_teampreview is None:
            self.logger.warning(
                "choose_on_teampreview arg was not set in environment - by default, teampreview decisions will be made randomly."
            )
        self._choose_on_teampreview = choose_on_teampreview or False
        self.battle_queue = _AsyncQueue(create_in_poke_loop(asyncio.Queue, 1))
        self.order_queue = _AsyncQueue(create_in_poke_loop(asyncio.Queue, 1))
        self.battle: Optional[AbstractBattle] = None

    def choose_move(self, battle: AbstractBattle) -> Awaitable[BattleOrder]:
        return self._choose_move(battle)

    async def _choose_move(self, battle: AbstractBattle) -> BattleOrder:
        if not self.battle or self.battle.finished:
            self.battle = battle
        assert self.battle.battle_tag == battle.battle_tag
        await self.battle_queue.async_put(battle)
        order = await self.order_queue.async_get()
        return order

    def teampreview(self, battle: AbstractBattle) -> Awaitable[str]:
        return self._teampreview(battle)

    async def _teampreview(self, battle: AbstractBattle) -> str:
        if not self._choose_on_teampreview:
            return self.random_teampreview(battle)
        elif isinstance(battle, Battle):
            return self.random_teampreview(battle)
        elif isinstance(battle, DoubleBattle):
            if battle.format is None or "vgc" not in battle.format:
                return self.random_teampreview(battle)
            species = [p.base_species for p in battle.team.values()]
            # derive first pair of teampreview selections from first order
            order1 = await self._choose_move(battle)
            if isinstance(order1, (ForfeitBattleOrder, _EmptyBattleOrder)):
                return order1.message
            assert isinstance(order1, DoubleBattleOrder)
            assert isinstance(order1.first_order.order, Pokemon)
            assert isinstance(order1.second_order.order, Pokemon)
            action1 = species.index(order1.first_order.order.base_species) + 1
            action2 = species.index(order1.second_order.order.base_species) + 1
            list(battle.team.values())[action1 - 1]._selected_in_teampreview = True
            list(battle.team.values())[action2 - 1]._selected_in_teampreview = True
            # derive second pair of teampreview selections from second order
            order2 = await self._choose_move(battle)
            if isinstance(order2, (ForfeitBattleOrder, _EmptyBattleOrder)):
                return order2.message
            assert isinstance(order2, DoubleBattleOrder)
            assert isinstance(order2.first_order.order, Pokemon)
            assert isinstance(order2.second_order.order, Pokemon)
            action3 = species.index(order2.first_order.order.base_species) + 1
            action4 = species.index(order2.second_order.order.base_species) + 1
            list(battle.team.values())[action3 - 1]._selected_in_teampreview = True
            list(battle.team.values())[action4 - 1]._selected_in_teampreview = True
            return f"/team {action1}{action2}{action3}{action4}"
        else:
            raise TypeError()

    def _battle_finished_callback(self, battle: AbstractBattle):
        asyncio.run_coroutine_threadsafe(self.battle_queue.async_put(battle), POKE_LOOP)


class PokeEnv(ParallelEnv[str, ObsType, ActionType]):
    """
    Base class implementing the PettingZoo API on the main thread.
    """

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
        challenge_timeout: Optional[float] = 60.0,
        team: Optional[Union[str, Teambuilder]] = None,
        choose_on_teampreview: bool | None = None,
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
        :type challenge_timeout: float, optional
        :param challenge_timeout: How long to wait for agents to challenge.
            If None agent challenging will never time out.
        :type ping_timeout: float, optional
        :param team: The team to use for formats requiring a team. Can be a showdown
            team string, a showdown packed team string, of a ShowdownTeam object.
            Defaults to None.
        :type team: str or Teambuilder, optional
        :param choose_on_teampreview: Controls switch-action-based team preview
            selection in formats that support it. If True, team preview uses
            environment actions to pick leads. If False, team preview defaults to
            a random order. If None, it behaves as False (with a warning).
        :type choose_on_teampreview: bool | None
        :param fake: If true, action-order converters will try to avoid returning a default
            output if at all possible, even if the output isn't a legal decision. Defaults
            to False.
        :type fake: bool
        :param strict: If true, action-order converters will throw an error if the move is
            illegal. Otherwise, it will return default. Defaults to True.
        :type: strict: bool
        """
        self._challenge_timeout = challenge_timeout
        self.agent1 = _EnvPlayer(
            account_configuration=account_configuration1
            or AccountConfiguration.generate(self.__class__.__name__, rand=True),
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
            choose_on_teampreview=choose_on_teampreview,
        )
        self.agent2 = _EnvPlayer(
            account_configuration=account_configuration2
            or AccountConfiguration.generate(self.__class__.__name__, rand=True),
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
            choose_on_teampreview=choose_on_teampreview,
        )
        self.agents: List[str] = []
        self.possible_agents = [self.agent1.username, self.agent2.username]
        self.battle1: Optional[AbstractBattle] = None
        self.battle2: Optional[AbstractBattle] = None
        self.agent1_to_move = False
        self.agent2_to_move = False
        self.fake = fake
        self.strict = strict
        self._np_random: Optional[Generator] = None
        self._reward_buffer: WeakKeyDictionary[AbstractBattle, float] = (
            WeakKeyDictionary()
        )
        self._challenge_task: Optional[Future[Any]] = None

    ###################################################################################
    # PettingZoo API
    # https://pettingzoo.farama.org/api/parallel/#parallelenv

    def step(
        self, actions: Dict[str, ActionType]
    ) -> Tuple[
        Dict[str, ObsType],
        Dict[str, float],
        Dict[str, bool],
        Dict[str, bool],
        Dict[str, Dict[str, Any]],
    ]:
        assert self.battle1 is not None
        assert self.battle2 is not None
        assert not self.battle1.finished
        assert not self.battle2.finished
        if self.agent1_to_move:
            self.agent1_to_move = False
            order1 = self.action_to_order(
                actions[self.agents[0]],
                self.battle1,
                fake=self.fake,
                strict=self.strict,
            )
            self.agent1.order_queue.put(order1)
        if self.agent2_to_move:
            self.agent2_to_move = False
            order2 = self.action_to_order(
                actions[self.agents[1]],
                self.battle2,
                fake=self.fake,
                strict=self.strict,
            )
            self.agent2.order_queue.put(order2)
        battle1 = self.agent1.battle_queue.race_get(
            self.agent1._waiting, self.agent2._trying_again
        )
        battle2 = self.agent2.battle_queue.race_get(
            self.agent2._waiting, self.agent1._trying_again
        )
        self.agent1_to_move = battle1 is not None
        self.agent2_to_move = battle2 is not None
        if battle1 is None:
            self.agent1._waiting.clear()
            self.agent2._trying_again.clear()
            battle1 = self.battle1
        if battle2 is None:
            self.agent2._waiting.clear()
            self.agent1._trying_again.clear()
            battle2 = self.battle2
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
        self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, ObsType], Dict[str, Dict[str, Any]]]:
        self.agents = [self.agent1.username, self.agent2.username]
        if seed is not None:
            self._np_random, seed = seeding.np_random(seed)
        if self.battle1 and not self.battle1.finished:
            assert self.battle2 is not None
            if self.battle1 == self.agent1.battle:
                if self.agent1_to_move:
                    self.agent1_to_move = False
                    self.agent1.order_queue.put(ForfeitBattleOrder())
                    if self.agent2_to_move:
                        self.agent2_to_move = False
                        self.agent2.order_queue.put(_EmptyBattleOrder())
                else:
                    assert self.agent2_to_move
                    self.agent2_to_move = False
                    self.agent2.order_queue.put(ForfeitBattleOrder())
                self.agent1.battle_queue.get()
                self.agent2.battle_queue.get()
            else:
                raise RuntimeError(
                    "Environment and agent aren't synchronized. Try to restart"
                )
        self.reset_battles()
        self._challenge_task = asyncio.run_coroutine_threadsafe(
            self.agent1.battle_against(self.agent2, n_battles=1), POKE_LOOP
        )
        try:
            self.battle1 = self.agent1.battle_queue.get(timeout=self._challenge_timeout)
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError("Agent is not challenging")
        self.battle2 = self.agent2.battle_queue.get()
        self.agent1_to_move = True
        self.agent2_to_move = True
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

    def close(self, force: bool = True, wait: bool = True):
        if force:
            if self.battle1 and not self.battle1.finished:
                assert self.battle2 is not None
                if not self.agent1.battle_queue.empty():
                    self.agent1.battle_queue.get()
                if not self.agent2.battle_queue.empty():
                    self.agent2.battle_queue.get()
                if self.agent1_to_move:
                    self.agent1_to_move = False
                    self.agent1.order_queue.put(ForfeitBattleOrder())
                    if self.agent2_to_move:
                        self.agent2_to_move = False
                        self.agent2.order_queue.put(_EmptyBattleOrder())
                else:
                    assert self.agent2_to_move
                    self.agent2_to_move = False
                    self.agent2.order_queue.put(ForfeitBattleOrder())
        if wait and self._challenge_task is not None:
            self._challenge_task.result()
        if self._challenge_task is None or self._challenge_task.done():
            self.reset_battles()
        self._challenge_task = None
        self.battle1 = None
        self.battle2 = None
        self.agent1.battle = None
        self.agent2.battle = None
        while not self.agent1.order_queue.empty():
            self.agent1.order_queue.get()
        while not self.agent2.order_queue.empty():
            self.agent2.order_queue.get()
        while not self.agent1.battle_queue.empty():
            self.agent1.battle_queue.get()
        while not self.agent2.battle_queue.empty():
            self.agent2.battle_queue.get()

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
        :param fake: If true, action-order converters will try to avoid returning a default
            output if at all possible, even if the output isn't a legal decision. Defaults
            to False.
        :type fake: bool
        :param strict: If true, action-order converters will throw an error if the move is
            illegal. Otherwise, it will return default. Defaults to True.
        :type strict: bool

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
        :param fake: If true, action-order converters will try to avoid returning a default
            output if at all possible, even if the output isn't a legal decision. Defaults
            to False.
        :type fake: bool
        :param strict: If true, action-order converters will throw an error if the move is
            illegal. Otherwise, it will return default. Defaults to True.
        :type strict: bool

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
