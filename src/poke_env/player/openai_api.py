"""This module defines a player class with the OpenAI API on the main thread.
For a black-box implementation consider using the module env_player.
"""

from __future__ import annotations

import asyncio
import time
from abc import abstractmethod
from logging import Logger
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

from gymnasium.core import ObsType
from gymnasium.spaces import Discrete
from pettingzoo.utils.env import ActionType, ParallelEnv

from poke_env.concurrency import POKE_LOOP, create_in_poke_loop
from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.environment.battle import Battle
from poke_env.environment.double_battle import DoubleBattle
from poke_env.player.battle_order import (
    BattleOrder,
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


class AsyncPlayer(Player):
    battle_queue: _AsyncQueue
    order_queue: _AsyncQueue
    current_battle: AbstractBattle | None = None

    def __init__(self, *args, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.battle_queue = _AsyncQueue(create_in_poke_loop(asyncio.Queue, 1))
        self.order_queue = _AsyncQueue(create_in_poke_loop(asyncio.Queue, 1))

    def choose_move(self, battle: AbstractBattle) -> Awaitable[BattleOrder]:
        self.current_battle = battle
        return self._choose_move(battle)

    async def _choose_move(self, battle: AbstractBattle) -> BattleOrder:
        await self.battle_queue.async_put(battle)
        order = await self.order_queue.async_get()
        return order

    def _battle_finished_callback(self, battle: AbstractBattle):
        asyncio.run_coroutine_threadsafe(self.battle_queue.async_put(battle), POKE_LOOP)


class PokeEnv(ParallelEnv[str, ObsType, ActionType]):
    """
    Base class implementing the OpenAI Gym API on the main thread.
    """

    _SWITCH_CHALLENGE_TASK_RETRIES = 30
    _TIME_BETWEEN_SWITCH_RETRIES = 1

    _ACTION_SPACE: list[int]

    def __init__(
        self,
        acct_config1: AccountConfiguration | None = None,
        acct_config2: AccountConfiguration | None = None,
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
        self.agent1 = AsyncPlayer(
            account_configuration=acct_config1,
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
        self.agent2 = AsyncPlayer(
            account_configuration=acct_config2,
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
        self.agents = [self.agent1.username, self.agent2.username]
        self.action_spaces = {
            name: Discrete(len(self._ACTION_SPACE)) for name in self.agents
        }
        self.possible_agents = [f"AsyncPlayer {i}" for i in range(100)]
        self.current_battle: AbstractBattle | None = None
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
        Dict[str, dict],
    ]:
        battle1 = self.agent1.current_battle
        battle2 = self.agent2.current_battle
        assert battle1 is not None and battle2 is not None
        order1 = self.action_to_move(actions[self.agents[0]], battle1)
        order2 = self.action_to_move(actions[self.agents[1]], battle2)
        self.agent1.order_queue.put(order1)
        self.agent2.order_queue.put(order2)
        battle1 = self.agent1.battle_queue.get()
        battle2 = self.agent2.battle_queue.get()
        obs = {
            self.agents[0]: self.embed_battle(battle1),
            self.agents[1]: self.embed_battle(battle2),
        }
        reward = {
            self.agents[0]: self.calc_reward(battle1),
            self.agents[1]: self.calc_reward(battle2),
        }
        term1, trunc1 = self.get_term_trunc(battle1)
        term2, trunc2 = self.get_term_trunc(battle2)
        terminated = {
            self.agents[0]: term1,
            self.agents[1]: term2,
        }
        truncated = {
            self.agents[0]: trunc1,
            self.agents[1]: trunc2,
        }
        return obs, reward, terminated, truncated, self.get_additional_info()

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, ObsType], Dict[str, Dict[str, Any]]]:
        obs1 = self.embed_battle(self.agent1.battle_queue.get())
        obs2 = self.embed_battle(self.agent2.battle_queue.get())
        return {self.agents[0]: obs1, self.agents[1]: obs2}, self.get_additional_info()

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
            if self.current_battle != self.agent1.current_battle:
                self.current_battle = self.agent1.current_battle
        closing_task = asyncio.run_coroutine_threadsafe(
            self._stop_challenge_loop(purge=purge), POKE_LOOP
        )
        closing_task.result()

    def observation_space(self, agent: str):
        return self.observation_spaces[agent]

    def action_space(self, agent: str):
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
        the OpenAI gym API.

        :param battle: The current battle state.
        :type battle: AbstractBattle

        :return: The embedding of the current battle state.
        """
        pass

    ###################################################################################
    # Action space methods

    @staticmethod
    def get_action_space(battle: AbstractBattle) -> List[int]:
        if isinstance(battle, Battle):
            return PokeEnv.get_singles_action_space(battle)
        elif isinstance(battle, DoubleBattle):
            return PokeEnv.get_doubles_action_space(battle)
        else:
            raise TypeError()

    @staticmethod
    def get_singles_action_space(battle: Battle) -> List[int]:
        switch_space = [
            i
            for i, pokemon in enumerate(battle.team.values())
            if not battle.maybe_trapped
            and pokemon.species in [p.species for p in battle.available_switches]
        ]
        if battle.active_pokemon is None:
            return switch_space
        else:
            move_space = [
                i + 6
                for i, move in enumerate(battle.active_pokemon.moves.values())
                if move.id in [m.id for m in battle.available_moves]
            ]
            # mega_space = [i + 4 for i in move_space if battle.can_mega_evolve]
            zmove_space = [
                i + 8
                for i, move in enumerate(battle.active_pokemon.moves.values())
                if move.id in [m.id for m in battle.active_pokemon.available_z_moves]
                and battle.can_z_move
            ]
            dynamax_space = [i + 12 for i in move_space if battle.can_dynamax]
            tera_space = [i + 16 for i in move_space if battle.can_tera]
            if (
                not move_space
                and len(battle.available_moves) == 1
                and battle.available_moves[0].id in ["struggle", "recharge"]
            ):
                move_space = [6]
            if battle._wait:
                return [0]
            else:
                return (
                    switch_space
                    + move_space
                    # + mega_space
                    + zmove_space
                    + dynamax_space
                    + tera_space
                )

    @staticmethod
    def get_doubles_action_space(battle: DoubleBattle) -> List[int]:
        action_space1 = PokeEnv.get_doubles_action_space_(battle, pos=0)
        action_space2 = PokeEnv.get_doubles_action_space_(battle, pos=1)
        return action_space1 + action_space2

    @staticmethod
    def get_doubles_action_space_(battle: DoubleBattle, pos: int) -> List[int]:
        assert pos is not None
        if battle.finished:
            return []
        switch_space = [
            i + 1
            for i, pokemon in enumerate(battle.team.values())
            if not battle.maybe_trapped[pos]
            and battle.force_switch != [[False, True], [True, False]][pos]
            and not (
                len(battle.available_switches[0]) == 1
                and battle.force_switch == [True, True]
                and pos == 1
            )
            and not pokemon.active
            and pokemon.species in [p.species for p in battle.available_switches[pos]]
        ]
        active_mon = battle.active_pokemon[pos]
        if battle.teampreview:
            return switch_space
        elif active_mon is None:
            return switch_space or [0]
        else:
            move_spaces = [
                [
                    7 + 5 * i + j + 2
                    for j in battle.get_possible_showdown_targets(move, active_mon)
                ]
                for i, move in enumerate(active_mon.moves.values())
                if move.id in [m.id for m in battle.available_moves[pos]]
            ]
            move_space = [i for s in move_spaces for i in s]
            tera_space = [i + 20 for i in move_space if battle.can_tera[pos]]
            if (
                not move_space
                and len(battle.available_moves[pos]) == 1
                and battle.available_moves[pos][0].id in ["struggle", "recharge"]
            ):
                move_space = [9]
            return (switch_space + move_space + tera_space) or [0]

    ###################################################################################
    # Action-move conversion methods

    @staticmethod
    def action_to_move(action: ActionType, battle: AbstractBattle) -> BattleOrder:
        if isinstance(action, int) and isinstance(battle, Battle):
            return PokeEnv.singles_action_to_move(action, battle)
        elif isinstance(action, List) and isinstance(battle, DoubleBattle):
            return PokeEnv.doubles_action_to_move(action[0], action[1], battle)
        else:
            raise TypeError()

    @staticmethod
    def singles_action_to_move(action: int, battle: Battle) -> BattleOrder:
        if action == -1:
            return ForfeitBattleOrder()
        elif action < 6:
            order = Player.create_order(list(battle.team.values())[action])
        else:
            active_mon = battle.active_pokemon
            assert active_mon is not None
            order = Player.create_order(
                list(active_mon.moves.values())[(action - 6) % 4],
                mega=10 <= action < 14,
                z_move=14 <= action < 18,
                dynamax=18 <= action < 22,
                terastallize=22 <= action < 26,
            )
        return order

    @staticmethod
    def doubles_action_to_move(
        action1: int, action2: int, battle: DoubleBattle
    ) -> BattleOrder:
        if action1 == -1 or action2 == -1:
            return ForfeitBattleOrder()
        order1 = PokeEnv.doubles_action_to_move_(action1, battle, 0)
        order2 = PokeEnv.doubles_action_to_move_(action2, battle, 1)
        return DoubleBattleOrder(order1, order2)

    @staticmethod
    def doubles_action_to_move_(
        action: int, battle: DoubleBattle, pos: int
    ) -> BattleOrder | None:
        """
        Currently this works for gen 9 VGC format
        action = 0: pass
        1 <= action <= 6: switch
        7 <= action <= 26 (refer to below table):

            target  -2   -1    0    1    2
        move
        0           7    8    9    10   11
        1           12   13   14   15   16
        2           17   18   19   20   21
        3           22   23   24   25   26

        27 <= action <= 46: same as above, but terastallized
        """
        if action == 0:
            order = None
        elif action < 7:
            order = Player.create_order(list(battle.team.values())[action - 1])
        else:
            active_mon = battle.active_pokemon[pos]
            assert active_mon is not None
            mvs = (
                battle.available_moves[pos]
                if len(battle.available_moves[pos]) == 1
                and battle.available_moves[pos][0].id in ["struggle", "recharge"]
                else list(active_mon.moves.values())
            )
            order = Player.create_order(
                mvs[(action - 7) % 20 // 5],
                terastallize=bool((action - 7) // 20),
                move_target=(int(action) - 7) % 5 - 2,
            )
        return order

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

    @staticmethod
    def get_term_trunc(battle: AbstractBattle) -> tuple[bool, bool]:
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

    def get_additional_info(self) -> Dict[str, Any]:
        """
        Returns additional info for the reset method.
        Override only if you really need it.

        :return: Additional information as a Dict
        :rtype: Dict
        """
        battle1 = self.agent1.current_battle
        battle2 = self.agent2.current_battle
        assert battle1 is not None and battle2 is not None
        return {
            self.agents[0]: {"action_space": self.get_action_space(battle1)},
            self.agents[1]: {"action_space": self.get_action_space(battle2)},
        }

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
            self.agent1.send_challenges(username, 1), POKE_LOOP
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
            self.agent1.accept_challenges(username, 1, self.agent1.next_team), POKE_LOOP
        )

    async def _challenge_loop(
        self,
        n_challenges: Optional[int] = None,
        callback: Optional[Callable[[AbstractBattle], None]] = None,
    ):
        if not n_challenges:
            while self._keep_challenging:
                await self.agent1.battle_against(self.agent2, 1)
        elif n_challenges > 0:
            for _ in range(n_challenges):
                await self.agent1.battle_against(self.agent2, 1)
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
                time.sleep(self._TIME_BETWEEN_SWITCH_RETRIES)
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
        else:
            while self._keep_challenging:
                await self.agent1.ladder(1)

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
                time.sleep(self._TIME_BETWEEN_SWITCH_RETRIES)
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
        self.agent1.current_battle = None
        self.agent2.current_battle = None
        while not self._actions.empty():
            await self._actions.async_get()
        while not self._observations.empty():
            await self._observations.async_get()

        if purge:
            self.agent1.reset_battles()
            self.agent2.reset_battles()

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

    ###################################################################################
    # Expose properties of Player class

    @property
    def battles(self) -> Dict[str, AbstractBattle]:
        return self.agent1.battles

    @property
    def format(self) -> str:
        return self.agent1.format

    @property
    def format_is_doubles(self) -> bool:
        return self.agent1.format_is_doubles

    @property
    def n_finished_battles(self) -> int:
        return self.agent1.n_finished_battles

    @property
    def n_lost_battles(self) -> int:
        return self.agent1.n_lost_battles

    @property
    def n_tied_battles(self) -> int:
        return self.agent1.n_tied_battles

    @property
    def n_won_battles(self) -> int:
        return self.agent1.n_won_battles

    @property
    def win_rate(self) -> float:
        return self.agent1.win_rate

    ###################################################################################
    # Expose properties of Player Network Interface Class

    @property
    def logged_in(self) -> asyncio.Event:
        """Event object associated with user login.

        :return: The logged-in event
        :rtype: Event
        """
        return self.agent1.ps_client.logged_in

    @property
    def logger(self) -> Logger:
        """Logger associated with the player.

        :return: The logger.
        :rtype: Logger
        """
        return self.agent1.logger

    @property
    def username(self) -> str:
        """The player's username.

        :return: The player's username.
        :rtype: str
        """
        return self.agent1.username

    @property
    def websocket_url(self) -> str:
        """The websocket url.

        It is derived from the server url.

        :return: The websocket url.
        :rtype: str
        """
        return self.agent1.ps_client.websocket_url

    def __getattr__(self, item: str):
        return getattr(self.agent1, item)
