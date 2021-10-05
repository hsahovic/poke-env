# -*- coding: utf-8 -*-
"""This module defines a player class exposing the Open AI Gym API.
"""
#register with gyn

from abc import ABC, abstractmethod, abstractproperty
from gym.core import Env  # pyre-ignore
import gym

from queue import Queue
from threading import Thread
from multiprocessing import Process

from typing import Any, Callable, List, Optional, Tuple, Union

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.environment.battle import Battle
from poke_env.player.battle_order import BattleOrder, ForfeitBattleOrder
from poke_env.player.player import Player
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration
from poke_env.teambuilder.teambuilder import Teambuilder
from poke_env.utils import to_id_str

import asyncio
import numpy as np  # pyre-ignore
import time

LOOP = asyncio.get_event_loop()
#LOOP = asyncio.new_event_loop()
#LOOP.set_debug(True)
#asyncio.set_event_loop(LOOP)

def background_loop(loop):
    print("Starting background loop")
    #asyncio.set_event_loop(loop)
    loop.run_forever()

#battle_thread = Thread(
    #target=background_loop, args=(LOOP,), daemon=True
#)
#battle_thread.start()

class DummyPlayer(Player):
    def __init__(
        self, 
        *args, 
        policy: Optional[Callable[[Battle], BattleOrder]] = None, 
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._policy = policy if policy is not None else self.choose_random_move

    def set_policy(self, policy: Callable[[Battle], BattleOrder]):
        self._policy = policy

    def choose_move(self, battle: Battle) -> BattleOrder:
        return self._policy(battle)


class EnvPlayer(Player, Env, ABC):  # pyre-ignore
    """Player exposing the Open AI Gym Env API."""

    _ACTION_SPACE = None
    _DEFAULT_BATTLE_FORMAT = "gen8randombattle"
    MAX_BATTLE_SWITCH_RETRY = 10000
    PAUSE_BETWEEN_RETRIES = 0.001

    def __init__(
        self,
        player_configuration: Optional[PlayerConfiguration] = None,
        *,
        opponent: Optional[DummyPlayer] = None,
        avatar: Optional[int] = None,
        battle_format: Optional[str] = None,
        log_level: Optional[int] = None,
        server_configuration: Optional[ServerConfiguration] = None,
        start_listening: bool = True,
        start_timer_on_battle_start: bool = False,
        team: Optional[Union[str, Teambuilder]] = None,
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
        """
        super(EnvPlayer, self).__init__(
            player_configuration=player_configuration,
            avatar=avatar,
            battle_format=battle_format
            if battle_format is not None
            else self._DEFAULT_BATTLE_FORMAT,
            log_level=log_level,
            max_concurrent_battles=1,
            server_configuration=server_configuration,
            start_listening=start_listening,
            start_timer_on_battle_start=start_timer_on_battle_start,
            team=team,
        )
        self._actions = {}
        self._current_battle: AbstractBattle
        self._observations = {}
        self._reward_buffer = {}
        self._start_new_battle = False

        self._opponent = opponent if opponent is not None else DummyPlayer(battle_format=battle_format)


        #asyncio.run_coroutine_threadsafe(self._opponent.accept_challenges(None, n_challenges=0), LOOP)
        #asyncio.run_coroutine_threadsafe(self.accept_challenges(None, n_challenges=0), LOOP)




        #asyncio.create_task(self._opponent.accept_challenges(None, n_challenges=0))


        from time import sleep


        self.stop_battling = False
        self.is_battling = False
        #async def launch_battles(player: EnvPlayer, opponent: Player):
        def wrapper(player: EnvPlayer, opponent: Player, loop: asyncio.BaseEventLoop):

            #asyncio.set_event_loop(loop)
            while not player.stop_battling:
                asyncio.run(battle_launcher(player, opponent))
                pass
                #asyncio.get_event_loop().run_until_complete(battle_launcher(player, opponent))
                #asyncio.run(battle_launcher(player, opponent))


                #yield loop.create_task(battle_launcher(player, opponent))
                #asyncio.wait_for(task, timeout=None)
                #asyncio.run(battle_launcher(player, opponent)=loop)
                #if loop.is_running():
                    #asyncio.run(battle_launcher(player, opponent))
                    #task = loop.create_task(battle_launcher(player, opponent))
                    #asyncio.wait_for(task, timeout=None)
                #else:
                    #loop.run_until_complete(battle_launcher(player, opponent))
                    #sleep(0.1)


                #task = loop.create_task(battle_launcher(player, opponent))
                #await task
                #loop.wait_for(task, timeout=None)
                #ic('looping')

        async def battle_launcher(player: EnvPlayer, opponent: Player):
            # TODO why can't I just pass n_challenges=0?
            while True:
                idx = 0
                #while not self.stop_battling:
                #ic(f'launching battle {idx}')
                battles_coroutine = asyncio.gather(
                    player.send_challenges(
                        opponent=to_id_str(opponent.username),
                        n_challenges=1,
                        to_wait=opponent.logged_in,
                    ),
                    #asyncio.sleep(0.1),
                    opponent.accept_challenges(
                        opponent=to_id_str(player.username), 
                        n_challenges=1,
                    ),
                )
                #results = asyncio.run_coroutine_threadsafe(battles_coroutine, LOOP)
                #await results
                #ic('wait sleep')
                #ic('wait battles_co')
                await battles_coroutine
                #yield battles_coroutine
                #ic('wait battles_co done')

        #self.loop = asyncio.new_event_loop()
        #self.loop = LOOP
        #asyncio.set_event_loop(self.loop)
        #asyncio.run_coroutine_threadsafe(launch_battles(self, self._opponent), self.loop)
        #asyncio.get_event_loop().create_task(launch_battles(self, self._opponent))
        # NOTE have to run gather to make both run together, other wise, they hang each other
        # NOTE this causes 
        #loop = asyncio.new_event_loop()
        #loo
        #loop.c(launch_battles(self, self._opponent))
        #battle_thread = Thread(
            #target=background_loop, args=(loop,), daemon=True
        #)
        #Process(target=lambda: self._opponent.accept_challenges(None, n_challenges=0)).start()
        #battle_thread.start()

        #LOOP.create_task(battle_launcher(self, self._opponent))
        #asyncio.get_event_loop().create_task(battle_launcher(self, self._opponent))
        #asyncio.run_coroutine_threadsafe(battle_launcher(self, self._opponent), LOOP)


        #Thread(target=wrapper, args=(self, self._opponent, asyncio.get_event_loop())).start()
        Thread(target=wrapper, args=(self, self._opponent, asyncio.get_event_loop())).start()
        #Thread(target=wrapper, args=(self, self._opponent, asyncio.new_event_loop())).start()



        # TODO cancel future in del

        #asyncio.run_coroutine_threadsafe
        #asyncio.create_subprocess_exec(launch_battles(self, self._opponent))
        #LOOP.create_task(launch_battles(self, self._opponent))
        #ic(self._actions)
        #ic('init reset')
        #self.reset()
        #ic('init reset done')

    @abstractmethod
    def _action_to_move(
        self, action: int, battle: AbstractBattle
    ) -> BattleOrder:  # pragma: no cover
        """Abstract method converting elements of the action space to move orders."""

    def _battle_finished_callback(self, battle: AbstractBattle) -> None:
        self._observations[battle].put(self.embed_battle(battle))

    def _init_battle(self, battle: AbstractBattle) -> None:
        self._observations[battle] = Queue()
        self._actions[battle] = Queue()

    # TODO take policy or opponent as argument
    # TODO since there's a wrapper, maybe use functools stuff for documentation help
    def set_opponent_policy(self, policy: Callable[[Any], int]) -> None:
        """Sets the policy of the opponent.

        :param policy: The policy to use.
        :type policy: Callable
        """
        def policy_wrapper(battle: AbstractBattle) -> BattleOrder:
            battle_encoding = self.embed_battle(battle)
            action = policy(battle_encoding)
            return self._action_to_move(action, battle)

        self._opponent.set_policy(policy_wrapper)
    
    def set_opponent(self, opponent: Player) -> None:
        self._opponent = opponent

    def choose_move(self, battle: AbstractBattle) -> BattleOrder:
        if battle not in self._observations or battle not in self._actions:
            self._init_battle(battle)
        self._observations[battle].put(self.embed_battle(battle))
        action = self._actions[battle].get()

        return self._action_to_move(action, battle)

    def close(self) -> None:
        """Unimplemented. Has no effect."""

    def complete_current_battle(self) -> None:
        """Completes the current battle by forfeiting."""
        #ic('-------------------------------')
        self._actions[self._current_battle].put(-1)

    def compute_reward(self, battle: AbstractBattle) -> float:
        """Returns a reward for the given battle.

        The default implementation corresponds to the default parameters of the
        reward_computing_helper method.

        :param battle: The battle for which to compute the reward.
        :type battle: AbstractBattle
        :return: The computed reward.
        :rtype: float
        """
        return self.reward_computing_helper(battle)

    def embed_battle(self, battle: AbstractBattle) -> Any:  # pragma: no cover
        """Abstract method for embedding battles.

        :param battle: The battle whose state is being embedded
        :type battle: AbstractBattle
        :return: The computed embedding
        :rtype: Any
        """
        return battle

    def reset(self) -> Any:
        """Resets the internal environment state. The current battle will be set to an
        active unfinished battle.

        :return: The observation of the new current battle.
        :rtype: Any
        :raies: EnvironmentError
        """
        #ic(self._actions)
        try:
            #ic(self._current_battle)
            if self._current_battle.finished is False:
                #ic("forfeting")
                self.complete_current_battle()
                #ic('forfeted')
        except AttributeError:
            #ic('no current battle')
            pass

        for _ in range(self.MAX_BATTLE_SWITCH_RETRY):
            battles = dict(self._actions.items())
            battles = [b for b in battles if not b.finished]
            if battles:
                #ic(battles)
                self._current_battle = battles[0]
                #ic('waiting on get')
                observation = self._observations[self._current_battle].get()
                #ic('get done')
                return observation
            time.sleep(self.PAUSE_BETWEEN_RETRIES)
        else:
            raise EnvironmentError("User %s has no active battle." % self.username)

    def render(self, mode="human") -> None:
        """A one line rendering of the current state of the battle."""
        print(
            "  Turn %4d. | [%s][%3d/%3dhp] %10.10s - %10.10s [%3d%%hp][%s]"
            % (
                self._current_battle.turn,
                "".join(
                    [
                        "⦻" if mon.fainted else "●"
                        for mon in self._current_battle.team.values()
                    ]
                ),
                self._current_battle.active_pokemon.current_hp or 0,
                self._current_battle.active_pokemon.max_hp or 0,
                self._current_battle.active_pokemon.species,
                self._current_battle.opponent_active_pokemon.species,
                self._current_battle.opponent_active_pokemon.current_hp or 0,
                "".join(
                    [
                        "⦻" if mon.fainted else "●"
                        for mon in self._current_battle.opponent_team.values()
                    ]
                ),
            ),
            end="\n" if self._current_battle.finished else "\r",
        )

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
        current_value = 0

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

    def seed(self, seed=None) -> None:
        """Sets the numpy seed."""
        np.random.seed(seed)

    def step(self, action: int) -> Tuple:
        """Performs action in the current battle.

        :param action: The action to perform.
        :type action: int
        :return: A tuple containing the next observation, the reward, a boolean
            indicating wheter the episode is finished, and additional information
        :rtype: tuple
        """
        if self._current_battle.finished:
            observation = self.reset()
        else:
            self._actions[self._current_battle].put(action)
            observation = self._observations[self._current_battle].get()
        return (
            observation,
            self.compute_reward(self._current_battle),
            self._current_battle.finished,
            {},
        )

    def play_against(
        self, env_algorithm: Callable, opponent: Player, env_algorithm_kwargs=None
    ):
        """Executes a function controlling the player while facing opponent.

        The env_algorithm function is executed with the player environment as first
        argument. It exposes the open ai gym API.

        Additional arguments can be passed to the env_algorithm function with
        env_algorithm_kwargs.

        Battles against opponent will be launched as long as env_algorithm is running.
        When env_algorithm returns, the current active battle will be finished randomly
        if it is not already.

        :param env_algorithm: A function that controls the player. It must accept the
            player as first argument. Additional arguments can be passed with the
            env_algorithm_kwargs argument.
        :type env_algorithm: callable
        :param opponent: A player against with the env player will player.
        :type opponent: Player
        :param env_algorithm_kwargs: Optional arguments to pass to the env_algorithm.
            Defaults to None.
        """
        # TODO why is this a member of object?
        self._start_new_battle = True

        async def launch_battles(player: EnvPlayer, opponent: Player):
            battles_coroutine = asyncio.gather(
                player.send_challenges(
                    opponent=to_id_str(opponent.username),
                    n_challenges=1,
                    to_wait=opponent.logged_in,
                ),
                opponent.accept_challenges(
                    opponent=to_id_str(player.username), 
                    n_challenges=1
                ),
            )
            await battles_coroutine

        def env_algorithm_wrapper(player, kwargs):
            env_algorithm(player, **kwargs)

            player._start_new_battle = False
            while True:
                try:
                    player.complete_current_battle()
                    player.reset()
                except OSError:
                    break

        loop = asyncio.get_event_loop()

        if env_algorithm_kwargs is None:
            env_algorithm_kwargs = {}

        thread = Thread(
            target=lambda: env_algorithm_wrapper(self, env_algorithm_kwargs)
        )
        thread.start()

        while self._start_new_battle:
            loop.run_until_complete(launch_battles(self, opponent))
        thread.join()

    @abstractproperty
    def action_space(self) -> List:
        """Returns the action space of the player. Must be implemented by subclasses."""
        pass


class Gen4EnvSinglePlayer(EnvPlayer):  # pyre-ignore
    _ACTION_SPACE = list(range(4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen4randombattle"

    def _action_to_move(  # pyre-ignore
        self, action: int, battle: Battle
    ) -> BattleOrder:
        """Converts actions to move orders.

        The conversion is done as follows:
        action = -1:
            The battle will be forfeited.
        0 <= action < 4:
            The actionth available move in battle.available_moves is executed.
        4 <= action < 10
            The action - 4th available switch in battle.available_switches is executed.

        If the proposed action is illegal, a random legal move is performed.

        :param action: The action to convert.
        :type action: int
        :param battle: The battle in which to act.
        :type battle: Battle
        :return: the order to send to the server.
        :rtype: str
        """
        if action == -1:
            return ForfeitBattleOrder()
        elif (
            action < 4
            and action < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.create_order(battle.available_moves[action])
        elif 0 <= action - 4 < len(battle.available_switches):
            return self.create_order(battle.available_switches[action - 4])
        else:
            return self.choose_random_move(battle)

    @property
    def action_space(self) -> List:
        """The action space for gen 7 single battles.

        The conversion to moves is done as follows:

        0 <= action < 4:
            The action - 0th available move in battle.available_moves is executed.
        4 <= action < 10
            The action - 4th available switch in battle.available_switches is executed.
        """
        return self._ACTION_SPACE


class Gen5EnvSinglePlayer(Gen4EnvSinglePlayer):  # pyre-ignore
    _DEFAULT_BATTLE_FORMAT = "gen5randombattle"


class Gen6EnvSinglePlayer(EnvPlayer):  # pyre-ignore
    _ACTION_SPACE = list(range(2 * 4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen6randombattle"

    def _action_to_move(  # pyre-ignore
        self, action: int, battle: Battle
    ) -> BattleOrder:
        """Converts actions to move orders.

        The conversion is done as follows:

        action = -1:
            The battle will be forfeited.
        0 <= action < 4:
            The actionth available move in battle.available_moves is executed.
        4 <= action < 8:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        8 <= action < 14
            The action - 8th available switch in battle.available_switches is executed.

        If the proposed action is illegal, a random legal move is performed.

        :param action: The action to convert.
        :type action: int
        :param battle: The battle in which to act.
        :type battle: Battle
        :return: the order to send to the server.
        :rtype: str
        """
        if action == -1:
            return ForfeitBattleOrder()
        elif (
            action < 4
            and action < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.create_order(battle.available_moves[action])
        elif (
            battle.can_mega_evolve
            and 0 <= action - 4 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.create_order(battle.available_moves[action - 4], mega=True)
        elif 0 <= action - 8 < len(battle.available_switches):
            return self.create_order(battle.available_switches[action - 8])
        else:
            return self.choose_random_move(battle)

    @property
    def action_space(self) -> List:
        """The action space for gen 7 single battles.

        The conversion to moves is done as follows:

        0 <= action < 4:
            The actionth available move in battle.available_moves is executed.
        4 <= action < 8:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        8 <= action < 14
            The action - 8th available switch in battle.available_switches is executed.
        """
        return self._ACTION_SPACE


class Gen7EnvSinglePlayer(EnvPlayer):  # pyre-ignore
    _ACTION_SPACE = list(range(3 * 4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen7randombattle"

    def _action_to_move(  # pyre-ignore
        self, action: int, battle: Battle
    ) -> BattleOrder:
        """Converts actions to move orders.

        The conversion is done as follows:

        action = -1:
            The battle will be forfeited.
        0 <= action < 4:
            The actionth available move in battle.available_moves is executed.
        4 <= action < 8:
            The action - 4th available move in battle.available_moves is executed, with
            z-move.
        8 <= action < 12:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        12 <= action < 18
            The action - 12th available switch in battle.available_switches is executed.

        If the proposed action is illegal, a random legal move is performed.

        :param action: The action to convert.
        :type action: int
        :param battle: The battle in which to act.
        :type battle: Battle
        :return: the order to send to the server.
        :rtype: str
        """
        if action == -1:
            return ForfeitBattleOrder()
        elif (
            action < 4
            and action < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.create_order(battle.available_moves[action])
        elif (
            not battle.force_switch
            and battle.can_z_move
            and battle.active_pokemon
            and 0
            <= action - 4
            < len(battle.active_pokemon.available_z_moves)  # pyre-ignore
        ):
            return self.create_order(
                battle.active_pokemon.available_z_moves[action - 4], z_move=True
            )
        elif (
            battle.can_mega_evolve
            and 0 <= action - 8 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.create_order(battle.available_moves[action - 8], mega=True)
        elif 0 <= action - 12 < len(battle.available_switches):
            return self.create_order(battle.available_switches[action - 12])
        else:
            return self.choose_random_move(battle)

    @property
    def action_space(self) -> List:
        """The action space for gen 7 single battles.

        The conversion to moves is done as follows:

            0 <= action < 4:
                The actionth available move in battle.available_moves is executed.
            4 <= action < 8:
                The action - 4th available move in battle.available_moves is executed,
                with z-move.
            8 <= action < 12:
                The action - 8th available move in battle.available_moves is executed,
                with mega-evolution.
            12 <= action < 18
                The action - 12th available switch in battle.available_switches is
                executed.
        """
        return self._ACTION_SPACE


class Gen8EnvSinglePlayer(EnvPlayer):  # pyre-ignore
    _ACTION_SPACE = list(range(4 * 4 + 6))
    _DEFAULT_BATTLE_FORMAT = "gen8randombattle"

    def _action_to_move(  # pyre-ignore
        self, action: int, battle: Battle
    ) -> BattleOrder:
        """Converts actions to move orders.

        The conversion is done as follows:
        # TODO reduce action space. Hint: how are volt switches handled?
        action = -1:
            The battle will be forfeited.
        0 <= action < 4:
            The action - 0th available move in battle.available_moves is executed.
        4 <= action < 8:
            The action - 4th available move in battle.available_moves is executed, with
            z-move.
        8 <= action < 12:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        8 <= action < 12:
            The action - 8th available move in battle.available_moves is executed, with
            mega-evolution.
        12 <= action < 16:
            The action - 12th available move in battle.available_moves is executed,
            while dynamaxing.
        16 <= action < 22
            The action - 16th available switch in battle.available_switches is executed.

        If the proposed action is illegal, a random legal move is performed.

        :param action: The action to convert.
        :type action: int
        :param battle: The battle in which to act.
        :type battle: Battle
        :return: the order to send to the server.
        :rtype: str
        """
        if action == -1:
            return ForfeitBattleOrder()
        elif (
            action < 4
            and action < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.create_order(battle.available_moves[action])
        elif (
            not battle.force_switch
            and battle.can_z_move
            and battle.active_pokemon
            and 0
            <= action - 4
            < len(battle.active_pokemon.available_z_moves)  # pyre-ignore
        ):
            return self.create_order(
                battle.active_pokemon.available_z_moves[action - 4], z_move=True
            )
        elif (
            battle.can_mega_evolve
            and 0 <= action - 8 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.create_order(battle.available_moves[action - 8], mega=True)
        elif (
            battle.can_dynamax
            and 0 <= action - 12 < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.create_order(battle.available_moves[action - 12], dynamax=True)
        elif 0 <= action - 16 < len(battle.available_switches):
            return self.create_order(battle.available_switches[action - 16])
        else:
            return self.choose_random_move(battle)

    @property
    def action_space(self) -> List:
        """The action space for gen 7 single battles.

        The conversion to moves is done as follows:

            0 <= action < 4:
                The actionth available move in battle.available_moves is executed.
            4 <= action < 8:
                The action - 4th available move in battle.available_moves is executed,
                with z-move.
            8 <= action < 12:
                The action - 8th available move in battle.available_moves is executed,
                with mega-evolution.
            12 <= action < 16:
                The action - 12th available move in battle.available_moves is executed,
                while dynamaxing.
            16 <= action < 22
                The action - 16th available switch in battle.available_switches is
                executed.
        """
        return self._ACTION_SPACE
