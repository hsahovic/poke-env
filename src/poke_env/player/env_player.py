# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod, abstractproperty
from gym.core import Env  # pyre-ignore

from queue import Queue
from threading import Thread

from typing import Callable, List, Optional, Tuple

from poke_env.environment.battle import Battle
from poke_env.player.player import Player
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration
from poke_env.utils import to_id_str

import asyncio
import numpy as np  # pyre-ignore
import time


class EnvPlayer(Player, Env, ABC):  # pyre-ignore

    MAX_BATTLE_SWITCH_RETRY = 10000
    PAUSE_BETWEEN_RETRIES = 0.001

    def __init__(
        self,
        player_configuration: PlayerConfiguration,
        *,
        avatar: Optional[int] = None,
        battle_format: str,
        log_level: Optional[int] = None,
        server_configuration: ServerConfiguration,
        start_listening: bool = True,
    ):
        super(EnvPlayer, self).__init__(
            player_configuration=player_configuration,
            avatar=avatar,
            battle_format=battle_format,
            log_level=log_level,
            max_concurrent_battles=1,
            server_configuration=server_configuration,
            start_listening=start_listening,
        )
        self._observations = {}
        self._actions = {}
        self._current_battle: Battle
        self._reward_buffer = {}

    @abstractmethod
    def _action_to_move(self, action: int, battle: Battle) -> str:
        pass

    def _battle_finished_callback(self, battle: Battle) -> None:
        self._observations[battle].put(self.embed_battle(battle))

    def _init_battle(self, battle: Battle) -> None:
        self._observations[battle] = Queue()
        self._actions[battle] = Queue()

    def choose_move(self, battle: Battle) -> str:
        if battle not in self._observations or battle not in self._actions:
            self._init_battle(battle)
        self._observations[battle].put(self.embed_battle(battle))
        action = self._actions[battle].get()

        return self._action_to_move(action, battle)

    def close(self) -> None:
        pass

    def compute_reward(self, battle: Battle) -> float:
        return self.reward_computing_helper(battle)

    @abstractmethod
    def embed_battle(self, battle: Battle) -> np.ndarray:  # pyre-ignore
        pass

    def reset(self):
        for _ in range(self.MAX_BATTLE_SWITCH_RETRY):
            battles = [b for b in self._actions if not b.finished]
            if battles:
                self._current_battle = battles[0]
                observation = self._observations[self._current_battle].get()
                return observation
            time.sleep(self.PAUSE_BETWEEN_RETRIES)
        else:
            raise EnvironmentError("User %s has no active battle." % self.username)

    def render(self, mode="human") -> None:
        pass

    def reward_computing_helper(
        self,
        battle: Battle,
        *,
        fainted_value: float = 0.0,
        hp_value: float = 0.0,
        number_of_pokemons: int = 6,
        starting_value: float = 0.0,
        status_value: float = 0.0,
        victory_value: float = 1.0,
    ) -> float:
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
        np.random.seed(seed)

    def step(self, action) -> Tuple:
        self._actions[self._current_battle].put(action)
        observation = self._observations[self._current_battle].get()
        return (
            observation,
            self.compute_reward(self._current_battle),
            self._current_battle.finished,
            {},
        )

    def train_against(
        self,
        training_function: Callable,
        opponent: Player,
        n_battles: int = 1,
        training_kwargs=None,
    ):
        async def launch_battles(player: EnvPlayer, opponent: Player, n_battles: int):
            battles_coroutine = asyncio.gather(
                player.send_challenges(
                    opponent=to_id_str(opponent.username),
                    n_challenges=n_battles,
                    to_wait=opponent.logged_in,
                ),
                opponent.accept_challenges(
                    opponent=to_id_str(player.username), n_challenges=n_battles
                ),
            )
            await battles_coroutine

        loop = asyncio.get_event_loop()

        if training_kwargs is None:
            training_kwargs = {}

        thread = Thread(
            target=training_function, args=(self, n_battles), kwargs=training_kwargs
        )
        thread.start()

        loop.run_until_complete(launch_battles(self, opponent, n_battles))
        thread.join()

    @abstractproperty
    def action_space(self) -> List:
        pass


class Gen7EnvSinglePlayer(EnvPlayer):
    _ACTION_SPACE = list(range(3 * 4 + 6))

    def _action_to_move(self, action: int, battle: Battle) -> str:
        if (
            action < 4
            and action < len(battle.available_moves)
            and not battle.force_switch
        ):
            return self.create_order(battle.available_moves[action])
        elif (
            not battle.force_switch
            and battle.can_z_move
            and 0 <= action - 4 < len(battle.active_pokemon.available_z_moves)
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
        return self._ACTION_SPACE
