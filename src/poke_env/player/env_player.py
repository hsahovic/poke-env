# -*- coding: utf-8 -*-
"""This module defines a player class exposing the Open AI Gym API.
"""

from abc import ABC, abstractmethod, abstractproperty
from gym.core import Env  # pyre-ignore
import gym
from poke_env.player.baselines import RandomPlayer

from queue import Queue
from threading import Thread

from typing import Any, Callable, List, Optional, Tuple, Union

from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.environment.battle import Battle
from poke_env.player.battle_order import BattleOrder, ForfeitBattleOrder
from poke_env.player.player import Player
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration
from poke_env.teambuilder.teambuilder import Teambuilder
from poke_env.utils import to_id_str
from poke_env.environment.utils import reward_computing_helper

import asyncio
import numpy as np  # pyre-ignore
import time

LOOP = asyncio.get_event_loop()
asyncio.set_event_loop(LOOP)

class EnvPlayer(Player, Env, ABC):  # pyre-ignore
    """Player exposing the Open AI Gym Env API. Recommended use is with play_against."""

    MAX_BATTLE_SWITCH_RETRY = 10000
    PAUSE_BETWEEN_RETRIES = 0.001

    def __init__(
        self,
        *,
        action_to_move: Callable[[Any], BattleOrder],
        action_space: gym.spaces.Space,
        battle_embedder: Callable[[Battle], Any] = None,
        reward_computer: Callable[[Battle], float] = None,
        battle_format: Optional[str] = "gen8randombattle",
        opponent: Optional[Union[str, Player]] = None,
        **player_kwargs,
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
        self.reward_computer = reward_computer or reward_computing_helper()
        self.action_to_move = action_to_move
        self.action_space = action_space
        self.battle_embedder = battle_embedder or (lambda x: x)
        self._opponent = opponent or RandomPlayer(battle_format=battle_format)

        # This allows for multiprocessing support of environments
        # Must be before super()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        super(EnvPlayer, self).__init__(
            battle_format=battle_format,
            **player_kwargs,
        )
        self._actions = {}
        self._current_battle: AbstractBattle
        self._observations = {}
        self._reward_buffer = {}
        self._start_new_battle = False

        # Setup event loop
        def run(loop: asyncio.BaseEventLoop):
            if loop.is_running():
                # TODO should we raise an exception here?
                loop.create_task(self.launch_battles(self._opponent))
            else:
                loop.run_until_complete(self.launch_battles(self._opponent))
        t = Thread(target=run, args=(asyncio.get_event_loop(),))
        t.start()

    def set_opponent(self, opponent: Union[str, Player]) -> None:
        """Sets the opponent.

        :param opponent: The opponent.
        :type opponent: str or Player
        """
        # TODO add locks here for race conditions
        # TODO by swapping out after games, maybe opponents can be put in different positions?
        self._opponent = opponent


    def _battle_finished_callback(self, battle: AbstractBattle) -> None:
        self._observations[battle].put(self.embed_battle(battle))

    def _init_battle(self, battle: AbstractBattle) -> None:
        self._observations[battle] = Queue()
        self._actions[battle] = Queue()

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
        self._actions[self._current_battle].put(-1)

    def reset(self) -> Any:
        """Resets the internal environment state. The current battle will be set to an
        active unfinished battle.

        :return: The observation of the new current battle.
        :rtype: Any
        :raies: EnvironmentError
        """
        try:
            if self._current_battle.finished is False:
                self.complete_current_battle()
        except AttributeError:
            pass

        for _ in range(self.MAX_BATTLE_SWITCH_RETRY):
            battles = dict(self._actions.items())
            battles = [b for b in battles if not b.finished]
            if battles:
                self._current_battle = battles[0]
                observation = self._observations[self._current_battle].get()
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

    
    def seed(self, seed=None) -> None:
        """Sets the numpy seed."""
        # TODO does this seed ALL random used?
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
            # TODO why does baselines break with this?
            #raise ValueError(
                #"The previous episode is finished. To start a new one, please call reset."
            #)
        else:
            self._actions[self._current_battle].put(action)
            observation = self._observations[self._current_battle].get()
        return (
            observation,
            self.compute_reward(self._current_battle),
            self._current_battle.finished,
            {},
        )

    async def launch_battles(self, opponent: Player):
        self._start_new_battle = True
        while self._start_new_battle:
            battles_coroutine = asyncio.gather(
                self.send_challenges(
                    opponent=to_id_str(opponent.username),
                    n_challenges=1,
                    to_wait=opponent.logged_in,
                ),
                opponent.accept_challenges(
                    opponent=to_id_str(self.username), n_challenges=1
                ),
            )
            await battles_coroutine

Gen4EnvSinglePlayer_action_space = gym.spaces.Discrete(4 + 6)
GEN4_BATTLE_FORMAT = "gen4randombattle"

def gen4_action_to_move(  # pyre-ignore
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
        return Player.create_order(battle.available_switches[action - 4])
    else:
        return Player.choose_random_move(battle)


GEN5_BATTLE_FORMAT = "gen5randombattle"

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
GEN6_ACTION_SPACE = gym.spaces.Discrete(2 * 4 + 6)
GEN6_BATTLE_FORMAT = "gen6randombattle"

def gen6_action_to_move(  # pyre-ignore
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
        return Player.create_order(battle.available_moves[action])
    elif (
        battle.can_mega_evolve
        and 0 <= action - 4 < len(battle.available_moves)
        and not battle.force_switch
    ):
        return Player.create_order(battle.available_moves[action - 4], mega=True)
    elif 0 <= action - 8 < len(battle.available_switches):
        return Player.create_order(battle.available_switches[action - 8])
    else:
        return Player.choose_random_move(battle)

    @property
    def action_space(self) -> List:
        return self._ACTION_SPACE


GEN7_ACTION_SPACE = gym.spaces.Discrete(3 * 4 + 6)
GEN7_BATTLE_FORMAT = "gen7randombattle"

# TODO singles action space
# TODO reuse more code 
def gen7_action_to_move(  # pyre-ignore
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

GEN8_ACTION_SPACE = gym.spaces.Discrete(4 * 4 + 6)
GEN8_BATTLE_FORMAT = "gen8randombattle"

def gen8_action_to_move(  # pyre-ignore
    action: int, battle: Battle
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
        return Player.create_order(battle.available_moves[action])
    elif (
        not battle.force_switch
        and battle.can_z_move
        and battle.active_pokemon
        and 0
        <= action - 4
        < len(battle.active_pokemon.available_z_moves)  # pyre-ignore
    ):
        return Player.create_order(
            battle.active_pokemon.available_z_moves[action - 4], z_move=True
        )
    elif (
        battle.can_mega_evolve
        and 0 <= action - 8 < len(battle.available_moves)
        and not battle.force_switch
    ):
        return Player.create_order(battle.available_moves[action - 8], mega=True)
    elif (
        battle.can_dynamax
        and 0 <= action - 12 < len(battle.available_moves)
        and not battle.force_switch
    ):
        return Player.create_order(battle.available_moves[action - 12], dynamax=True)
    elif 0 <= action - 16 < len(battle.available_switches):
        return Player.create_order(battle.available_switches[action - 16])
    else:
        return Player.choose_random_move(battle)
