"""This module defines a player class with the Gymnasium API on the main thread.
For a black-box implementation consider using the module env_player.
"""

from __future__ import annotations

import asyncio
import time
from abc import abstractmethod
from typing import Any, Awaitable, Dict, Generic, List, Optional, Tuple, TypeVar, Union
from weakref import WeakKeyDictionary

import numpy as np
import numpy.typing as npt
from gymnasium.spaces import Discrete, MultiDiscrete, Space
from pettingzoo.utils.env import (  # type: ignore[import-untyped]
    ActionType,
    ObsType,
    ParallelEnv,
)

from poke_env.concurrency import POKE_LOOP, create_in_poke_loop
from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.environment.battle import Battle
from poke_env.environment.double_battle import DoubleBattle
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.player.battle_order import (
    BattleOrder,
    DefaultBattleOrder,
    DoubleBattleOrder,
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
        self, timeout: Optional[float] = None, default: ItemType | None = None
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
    order_queue: _AsyncQueue[BattleOrder]
    battle_queue: _AsyncQueue[AbstractBattle]

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
        self.battle: Optional[AbstractBattle] = None
        self.waiting = False

    def choose_move(self, battle: AbstractBattle) -> Awaitable[BattleOrder]:
        return self._env_move(battle)

    async def _env_move(self, battle: AbstractBattle) -> BattleOrder:
        if not self.battle or self.battle.finished:
            self.battle = battle
        if not self.battle == battle:
            raise RuntimeError("Using different battles for queues")
        await self.battle_queue.async_put(battle)
        self.waiting = True
        action = await self.order_queue.async_get()
        self.waiting = False
        return action

    def _battle_finished_callback(self, battle: AbstractBattle):
        asyncio.run_coroutine_threadsafe(self.battle_queue.async_put(battle), POKE_LOOP)


class PokeEnv(ParallelEnv[str, ObsType, ActionType]):
    """
    Base class implementing the Gymnasium API on the main thread.
    """

    _SWITCH_CHALLENGE_TASK_RETRIES = 30
    _TIME_BETWEEN_SWITCH_RETRIES = 1

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
        self.action_spaces: Dict[str, Space]
        act_size = self.get_action_space_size(battle_format)
        if self.agent1.format_is_doubles:
            self.action_spaces = {
                agent: MultiDiscrete([act_size, act_size])
                for agent in self.possible_agents
            }
        else:
            self.action_spaces = {
                agent: Discrete(act_size) for agent in self.possible_agents
            }
        self._reward_buffer: WeakKeyDictionary[AbstractBattle, float] = (
            WeakKeyDictionary()
        )
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
            order1 = self.action_to_order(actions[self.agents[0]], self.battle1)
            self.agent1.order_queue.put(order1)
        if self.agent2.waiting:
            order2 = self.action_to_order(actions[self.agents[1]], self.battle2)
            self.agent2.order_queue.put(order2)
        battle1 = self.agent1.battle_queue.get(timeout=0.01, default=self.battle1)
        battle2 = self.agent2.battle_queue.get(timeout=0.01, default=self.battle2)
        observations = {
            self.agents[0]: self.embed_battle(battle1),
            self.agents[1]: self.embed_battle(battle2),
        }
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
        # forfeit any still-running battle between agent1 and agent2
        if self.battle1 and not self.battle1.finished:
            if self.battle1 == self.agent1.battle:
                self.agent1.order_queue.put(ForfeitBattleOrder())
                self.agent2.order_queue.put(DefaultBattleOrder())
                self.agent1.battle_queue.get()
                self.agent2.battle_queue.get()
            else:
                raise RuntimeError(
                    "Environment and agent aren't synchronized. Try to restart"
                )
        obs1 = self.agent1.battle_queue.get()
        obs2 = self.agent2.battle_queue.get()
        observations = {
            self.agents[0]: self.embed_battle(obs1),
            self.agents[1]: self.embed_battle(obs2),
        }
        self.battle1 = self.agent1.battle
        self.battle2 = self.agent2.battle
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

    def action_space(self, agent: str) -> Space:
        return self.action_spaces[agent]

    ###################################################################################
    # Abstract methods

    @abstractmethod
    def calc_reward(self, battle: AbstractBattle) -> float:
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
    def embed_battle(self, battle: AbstractBattle) -> ObsType:
        """
        Returns the embedding of the current battle state in a format compatible with
        the Gymnasium API.

        :param battle: The current battle state.
        :type battle: AbstractBattle

        :return: The embedding of the current battle state.
        """
        pass

    ###################################################################################
    # Action -> Order methods

    # TODO: add mega evolving, z-moves, and dynamaxing for doubles
    @staticmethod
    def action_to_order(action: ActionType, battle: AbstractBattle) -> BattleOrder:
        """
        SINGLES:

        action = -1: forfeit
        0 <= action < 6: switch
        6 <= action < 10: move
        10 <= action < 14: move + mega evolve
        14 <= action < 18: move + z-move
        18 <= action < 22: move + dynamax
        22 <= action < 26: move + terastallize

        DOUBLES:

        The action is a list here, and every element follows the following rules:
        element = -1: forfeit
        element = 0: pass
        1 <= element <= 6: switch
        7 <= element <= 10: move with target = -2
        11 <= element <= 14: move with target = -1
        15 <= element <= 18: move with target = 0
        19 <= element <= 22: move with target = 1
        23 <= element <= 26: move with target = 2
        27 <= element <= 30: move with target = -2 and terastallize
        31 <= element <= 34: move with target = -1 and terastallize
        35 <= element <= 38: move with target = 0 and terastallize
        39 <= element <= 42: move with target = 1 and terastallize
        43 <= element <= 46: move with target = 2 and terastallize
        """
        try:
            if isinstance(battle, Battle):
                assert isinstance(action, (int, np.integer))
                a = action.item() if isinstance(action, np.integer) else action
                return PokeEnv._singles_action_to_order(a, battle)
            elif isinstance(battle, DoubleBattle):
                assert isinstance(action, (List, np.ndarray))
                [a1, a2] = action
                return PokeEnv._doubles_action_to_order(a1, a2, battle)
            else:
                raise TypeError()
        except IndexError:
            return Player.choose_random_move(battle)
        except AssertionError as e:
            if str(e) == "invalid pick":
                return Player.choose_random_move(battle)
            else:
                raise e

    @staticmethod
    def _singles_action_to_order(action: int, battle: Battle) -> BattleOrder:
        if action == -1:
            return ForfeitBattleOrder()
        elif action < 6:
            order = Player.create_order(list(battle.team.values())[action])
            assert order.order in battle.available_switches, "invalid pick"
        else:
            assert not battle.force_switch, "invalid pick"
            active_mon = battle.active_pokemon
            assert active_mon is not None
            mvs = (
                battle.available_moves
                if len(battle.available_moves) == 1
                and battle.available_moves[0].id in ["struggle", "recharge"]
                else list(active_mon.moves.values())
            )
            order = Player.create_order(
                mvs[(action - 6) % 4],
                mega=battle.can_mega_evolve and 10 <= action < 14,
                z_move=battle.can_z_move and 14 <= action < 18,
                dynamax=battle.can_dynamax and 18 <= action < 22,
                terastallize=battle.can_tera is not None and 22 <= action < 26,
            )
            assert order.order in battle.available_moves, "invalid pick"
            assert not order.mega or battle.can_mega_evolve, "invalid pick"
            assert not order.z_move or (
                battle.can_z_move and order.order in active_mon.available_z_moves
            ), "invalid pick"
            assert not order.dynamax or battle.can_dynamax, "invalid pick"
            assert not order.terastallize or battle.can_tera is not None, "invalid pick"
        return order

    @staticmethod
    def _doubles_action_to_order(
        action1: int, action2: int, battle: DoubleBattle
    ) -> BattleOrder:
        if action1 == -1 or action2 == -1:
            return ForfeitBattleOrder()
        must_respond1 = not (any(battle.force_switch) and not battle.force_switch[0])
        must_respond2 = not (any(battle.force_switch) and not battle.force_switch[0])
        order1 = (
            PokeEnv._doubles_action_to_order_individual(action1, battle, 0)
            if must_respond1
            else None
        )
        order2 = (
            PokeEnv._doubles_action_to_order_individual(action2, battle, 1)
            if must_respond2
            else None
        )
        return DoubleBattleOrder.join_orders(
            [order1] if order1 is not None else [],
            [order2] if order2 is not None else [],
        )[0]

    @staticmethod
    def _doubles_action_to_order_individual(
        action: int, battle: DoubleBattle, pos: int
    ) -> BattleOrder | None:
        if action == 0:
            order = None
        elif action < 7:
            order = Player.create_order(list(battle.team.values())[action - 1])
            assert order.order in battle.available_switches[pos], "invalid pick"
        else:
            assert not battle.force_switch[pos], "invalid pick"
            active_mon = battle.active_pokemon[pos]
            assert active_mon is not None, "invalid pick"
            mvs = (
                battle.available_moves[pos]
                if len(battle.available_moves[pos]) == 1
                and battle.available_moves[pos][0].id in ["struggle", "recharge"]
                else list(active_mon.moves.values())
            )
            order = Player.create_order(
                mvs[(action - 7) % 4],
                terastallize=battle.can_tera[pos] is not None
                and bool((action - 7) // 20),
                move_target=(action - 7) % 20 // 4 - 2,
            )
            assert order.order in battle.available_moves[pos], "invalid pick"
            assert (
                not order.terastallize or battle.can_tera[pos] is not False
            ), "invalid pick"
            assert isinstance(order.order, Move)
            assert order.move_target in battle.get_possible_showdown_targets(
                order.order, active_mon
            ), "invalid pick"
        return order

    ###################################################################################
    # Order -> Action methods

    @staticmethod
    def order_to_action(order: BattleOrder, battle: AbstractBattle) -> ActionType:
        if isinstance(battle, Battle):
            assert not isinstance(order, DoubleBattleOrder)
            return PokeEnv._singles_order_to_action(order, battle)  # type: ignore
        elif isinstance(battle, DoubleBattle):
            assert isinstance(order, DoubleBattleOrder)
            return PokeEnv._doubles_order_to_action(order, battle)  # type: ignore
        else:
            raise TypeError()

    @staticmethod
    def _singles_order_to_action(order: BattleOrder, battle: Battle) -> np.int64:
        assert order.order is not None
        if isinstance(order, ForfeitBattleOrder):
            action = -1
        elif isinstance(order.order, Pokemon):
            action = [p.base_species for p in battle.team.values()].index(
                order.order.base_species
            )
        else:
            assert not battle.force_switch, "invalid pick"
            active_mon = battle.active_pokemon
            assert active_mon is not None
            mvs = (
                battle.available_moves
                if len(battle.available_moves) == 1
                and battle.available_moves[0].id in ["struggle", "recharge"]
                else list(active_mon.moves.values())
            )
            action = mvs.index(order.order)
            if order.mega:
                gimmick = 1
            elif order.z_move:
                gimmick = 2
            elif order.dynamax:
                gimmick = 3
            elif order.terastallize:
                gimmick = 4
            else:
                gimmick = 0
            action = 6 + action + 4 * gimmick
            assert order.order in battle.available_moves, "invalid pick"
            assert not order.mega or battle.can_mega_evolve, "invalid pick"
            assert not order.z_move or (
                battle.can_z_move and order.order in active_mon.available_z_moves
            ), "invalid pick"
            assert not order.dynamax or battle.can_dynamax, "invalid pick"
            assert not order.terastallize or battle.can_tera is not None, "invalid pick"
        return np.int64(action)

    @staticmethod
    def _doubles_order_to_action(
        order: DoubleBattleOrder, battle: DoubleBattle
    ) -> npt.NDArray[np.int64]:
        action1 = PokeEnv._doubles_order_to_action_individual(
            order.first_order, battle, 0
        )
        action2 = PokeEnv._doubles_order_to_action_individual(
            order.second_order, battle, 1
        )
        return np.array([action1, action2])

    @staticmethod
    def _doubles_order_to_action_individual(
        order: Optional[BattleOrder], battle: DoubleBattle, pos: int
    ) -> np.int64:
        if order is None:
            return np.int64(0)
        assert order.order is not None
        if isinstance(order, ForfeitBattleOrder):
            action = -1
        elif isinstance(order.order, Pokemon):
            action = [p.base_species for p in battle.team.values()].index(
                order.order.base_species
            ) + 1
        else:
            assert not battle.force_switch[pos], "invalid pick"
            active_mon = battle.active_pokemon[pos]
            assert active_mon is not None, "invalid pick"
            mvs = (
                battle.available_moves[pos]
                if len(battle.available_moves[pos]) == 1
                and battle.available_moves[pos][0].id in ["struggle", "recharge"]
                else list(active_mon.moves.values())
            )
            action = mvs.index(order.order)
            target = order.move_target + 2
            if order.terastallize:
                gimmick = 1
            else:
                gimmick = 0
            action = 6 + action + 4 * target + 20 * gimmick
            assert order.order in battle.available_moves[pos], "invalid pick"
            assert (
                not order.terastallize or battle.can_tera[pos] is not False
            ), "invalid pick"
            assert order.move_target in battle.get_possible_showdown_targets(
                order.order, active_mon
            ), "invalid pick"
        return np.int64(action)

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
    def get_action_space_size(battle_format: str):
        format_lowercase = battle_format.lower()
        num_switches = 6
        num_moves = 4
        if (
            "vgc" in format_lowercase
            or "double" in format_lowercase
            or "metronome" in format_lowercase
        ):
            num_targets = 5
            if format_lowercase.startswith("gen9"):
                num_gimmicks = 1
            else:
                num_gimmicks = 0
        else:
            num_targets = 1
            if format_lowercase.startswith("gen6"):
                num_gimmicks = 1
            elif format_lowercase.startswith("gen7"):
                num_gimmicks = 2
            elif format_lowercase.startswith("gen8"):
                num_gimmicks = 3
            elif format_lowercase.startswith("gen9"):
                num_gimmicks = 4
            else:
                num_gimmicks = 0
        return num_switches + num_moves * num_targets * (num_gimmicks + 1)

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
                time.sleep(self._TIME_BETWEEN_SWITCH_RETRIES)
        if not n_challenges:
            self._keep_challenging = True
        self._challenge_task = asyncio.run_coroutine_threadsafe(
            self._challenge_loop(n_challenges), POKE_LOOP
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
                time.sleep(self._TIME_BETWEEN_SWITCH_RETRIES)
        if not n_challenges:
            self._keep_challenging = True
        self._challenge_task = asyncio.run_coroutine_threadsafe(
            self._ladder_loop(n_challenges), POKE_LOOP
        )

    async def _stop_challenge_loop(
        self, force: bool = True, wait: bool = True, purge: bool = False
    ):
        self._keep_challenging = False

        if force:
            if self.battle1 and not self.battle1.finished:
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
