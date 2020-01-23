# -*- coding: utf-8 -*-
"""This module defines a random players baseline
"""

import asyncio
import numpy as np  # pyre-ignore

from abc import ABC
from abc import abstractmethod
from poke_env.environment.battle import Battle
from poke_env.player.player import Player
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration
from poke_env.utils import to_id_str
from typing import Dict
from typing import List
from typing import Optional


class TrainablePlayer(Player, ABC):
    def __init__(
        self,
        player_configuration: PlayerConfiguration,
        *,
        avatar: Optional[int] = None,
        battle_format: str,
        log_level: Optional[int] = None,
        max_concurrent_battles: int = 1,
        model=None,
        server_configuration: ServerConfiguration,
        start_listening: bool = True,
    ) -> None:
        """
        :param player_configuration: Player configuration.
        :type player_configuration: PlayerConfiguration
        :param avatar: Player avatar id. Optional.
        :type avatar: int, optional
        :param battle_format: Name of the battle format this player plays.
        :type battle_format: str
        :param log_level: The player's logger level.
        :type log_level: int. Defaults to logging's default level.
        :param max_concurrent_battles: Maximum number of battles this player will play
            concurrently. If 0, no limit will be applied. Defaults to 1.
        :type max_concurrent_battles: int
        :param server_configuration: Server configuration.
        :type server_configuration: ServerConfiguration
        :param start_listening: Wheter to start listening to the server. Defaults to
            True.
        :type start_listening: bool
        """
        super(TrainablePlayer, self).__init__(
            player_configuration=player_configuration,
            avatar=avatar,
            battle_format=battle_format,
            log_level=log_level,
            max_concurrent_battles=max_concurrent_battles,
            server_configuration=server_configuration,
            start_listening=start_listening,
        )
        if not model:
            model = self.init_model()
        self.model = model
        self._training_data = {}

        self._n_replays = 0

    def _manage_error_in(self, battle: Battle):
        self._training_data[battle].pop()

    @staticmethod
    def init_model():
        pass

    @abstractmethod
    def action_to_move(self, action, battle: Battle):
        pass

    @abstractmethod
    def battle_to_state(self, battle: Battle):
        pass

    @abstractmethod
    def state_to_action(self, state: np.array, battle: Battle):  # pyre-ignore
        pass

    @abstractmethod
    def replay(self, battle_history: Dict):
        pass

    def choose_move(self, battle: Battle) -> str:
        state = self.battle_to_state(battle)
        action = self.state_to_action(state, battle)
        move = self.action_to_move(action, battle)

        if battle not in self._training_data:
            self._training_data[battle] = []

        self._training_data[battle].append((state, action))

        return move

    async def train_against(
        self, opponent: "TrainablePlayer", n_battles=100, train_opponent: bool = False
    ):
        self._training_data = {}
        if train_opponent:
            opponent._training_data = {}

        await asyncio.gather(
            self.send_challenges(
                opponent=to_id_str(opponent.username),
                n_challenges=n_battles,
                to_wait=opponent.logged_in,
            ),
            opponent.accept_challenges(
                opponent=to_id_str(self.username), n_challenges=n_battles
            ),
        )

        self.replay(self._training_data)
        if train_opponent:
            opponent.replay(opponent._training_data)

        self._n_replays += 1

    @property
    def training_data(self) -> Dict[Battle, List]:
        return self._training_data

    @property
    def n_replays(self) -> int:
        return self._n_replays
