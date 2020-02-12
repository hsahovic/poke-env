# -*- coding: utf-8 -*-
"""This module defines a base class for players.
"""

import json
import numpy as np  # pyre-ignore

from abc import ABC
from abc import abstractmethod
from asyncio import Condition
from asyncio import Event
from asyncio import Queue
from asyncio import Semaphore
from time import perf_counter
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from poke_env.environment.battle import Battle
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.exceptions import ShowdownException
from poke_env.player.player_network_interface import PlayerNetwork
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration


class Player(PlayerNetwork, ABC):
    """
    Base class for players.
    """

    MESSAGES_TO_IGNORE = [""]

    def __init__(
        self,
        player_configuration: PlayerConfiguration,
        *,
        avatar: Optional[int] = None,
        battle_format: str,
        log_level: Optional[int] = None,
        max_concurrent_battles: int = 1,
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
        super(Player, self).__init__(
            player_configuration=player_configuration,
            avatar=avatar,
            log_level=log_level,
            server_configuration=server_configuration,
            start_listening=start_listening,
        )

        self._format: str = battle_format
        self._max_concurrent_battles: int = max_concurrent_battles

        self._battles: Dict[str, Battle] = {}
        self._battle_semaphore: Semaphore = Semaphore(0)

        self._battle_start_condition: Condition = Condition()
        self._battle_count_queue: Queue = Queue(max_concurrent_battles)
        self._challenge_queue: Queue = Queue()

        self.logger.debug("Player initialisation finished")

    async def _create_battle(self, split_message: List[str]) -> Battle:
        """Returns battle object corresponding to received message.

        :param split_message: The battle initialisation message.
        :type split_message: List[str]
        :return: The corresponding battle object
        :rtype: Battle
        """
        # We check that the battle has the correct format
        if split_message[1] == self._format and len(split_message) >= 2:
            # Battle initialisation
            battle_tag = "-".join(split_message[0:3])
            if battle_tag.startswith(">"):
                battle_tag = battle_tag[1:]
            if battle_tag.endswith("\n"):
                battle_tag = battle_tag[:-1]

            if split_message[2] in self._battles:
                return self._battles[split_message[2]]
            else:
                battle = Battle(
                    battle_tag=battle_tag, username=self.username, logger=self.logger
                )
                await self._battle_count_queue.put(None)
                if split_message[2] in self._battles:
                    self._battle_count_queue.get()
                    return self._battles[split_message[2]]
                async with self._battle_start_condition:
                    self._battle_semaphore.release()
                    self._battle_start_condition.notify_all()
                    self._battles[split_message[2]] = battle
                return battle

            return self._battles[split_message[2]]
        else:
            self.logger.critical(
                "Unmanaged battle initialisation message received: %s", split_message
            )
            raise ShowdownException()

    async def _get_battle(self, battle_number: str) -> Battle:
        while True:
            if battle_number in self._battles:
                return self._battles[battle_number]
            async with self._battle_start_condition:
                await self._battle_start_condition.wait()

    async def _handle_battle_message(self, message: str) -> None:
        """Handles a battle message.

        :param split_message: The received battle message.
        :type split_message: str
        """
        # Battle messages can be multiline
        messages = [m.split("|") for m in message.split("\n")]

        split_first_message = messages[0]
        battle_info = split_first_message[0].split("-")

        if len(messages) > 1 and len(messages[1]) > 1 and messages[1][1] == "init":
            battle = await self._create_battle(battle_info)
            messages.pop(0)
        else:
            battle = await self._get_battle(battle_info[2])

        if battle is None:
            self.logger.critical("No battle found from message %s", message)
            return
        for split_message in messages[1:]:
            if len(split_message) <= 1:
                self.logger.debug("Battle message too short; ignored: %s", message)
                continue
            if split_message[1] in self.MESSAGES_TO_IGNORE:
                pass
            elif split_message[1] == "request":
                if split_message[2]:
                    request = json.loads(split_message[2])
                    if request:
                        await battle._parse_request(request)
                        if battle.force_switch:
                            await self._send_message(
                                self.choose_move(battle), battle.battle_tag
                            )
            elif split_message[1] == "title":
                player_1, player_2 = split_message[2].split(" vs. ")
                battle.players = player_1, player_2
            elif split_message[1] == "win":
                await battle._won_by(split_message[2])
                await self._battle_count_queue.get()
                self._battle_count_queue.task_done()
            elif split_message[1] == "tie":
                await battle._tied()
                await self._battle_count_queue.get()
                self._battle_count_queue.task_done()
            elif split_message[1] == "error":
                if split_message[2].startswith(
                    "[Invalid choice] Sorry, too late to make a different move"
                ):
                    if battle.trapped:
                        await self._send_message(
                            self.choose_move(battle), battle.battle_tag
                        )
                elif split_message[2].startswith(
                    "[Unavailable choice] Can't switch: The active Pokémon is trapped"
                ) or split_message[2].startswith(
                    "[Invalid choice] Can't switch: The active Pokémon is trapped"
                ):
                    battle.trapped = True
                    await self._send_message(
                        self.choose_move(battle), battle.battle_tag
                    )
                elif split_message[2].startswith("[Invalid choice]"):
                    await self._send_message(
                        self.choose_move(battle), battle.battle_tag
                    )
                    self._manage_error_in(battle)
                else:
                    self.logger.critical("Unexpected error message: %s", split_message)
            elif split_message[1] == "expire":
                pass
            elif split_message[1] == "turn":
                battle.turn = int(split_message[2])
                await self._send_message(self.choose_move(battle), battle.battle_tag)
            else:
                await battle._parse_message(split_message)

    def _manage_error_in(self, battle: Battle):
        pass

    async def _update_challenges(self, split_message: List[str]) -> None:
        """Update internal challenge state.

        Add corresponding challenges to internal queue of challenges, where they will be
        processed if relevant.

        :param split_message: Recevied message, split.
        :type split_message: List[str]
        """
        self.logger.debug("Updating challenges with %s", split_message)
        challenges = json.loads(split_message[2]).get("challengesFrom", {})
        for user, format_ in challenges.items():
            if format_ == self._format:
                await self._challenge_queue.put(user)

    async def accept_challenges(
        self, opponent: Optional[Union[str, List[str]]], n_challenges: int
    ) -> None:
        """Let the player wait for challenges from opponent, and accept them.

        If opponent is None, every challenge will be accepted. If opponent if a string,
        all challenges from player with that name will be accepted. If opponent is a
        list all challenges originating from players whose name is in the list will be
        accepted.

        Up to n_challenges challenges will be accepted, after what the function will
        wait for these battles to finish, and then return.

        :param opponent: Players from which challenges will be accepted.
        :type opponent: None, str or list of str
        :param n_challenges: Number of challenges that will be accepted
        :type n_challenges: int
        """
        await self._logged_in.wait()
        self.logger.debug("Event logged in received in accept_challenge")

        for _ in range(n_challenges):
            while True:
                username = await self._challenge_queue.get()
                self.logger.debug(
                    "Consumed %s from challenge queue in accept_challenge", username
                )
                if (
                    (opponent is None)
                    or (opponent == username)  # pyre-ignore
                    or (isinstance(opponent, list) and (username in opponent))
                ):
                    await self._accept_challenge(username)
                    await self._battle_semaphore.acquire()
                    break
        await self._battle_count_queue.join()

    @abstractmethod
    def choose_move(self, battle: Battle) -> str:
        """Abstract async method to choose a move in a battle.

        :param battle: The battle.
        :type battle: Battle
        :return: The move order.
        :rtype: str
        """
        pass

    def choose_random_move(self, battle: Battle) -> str:
        """Returns a random legal move from battle.

        :param battle: The battle in which to move.
        :type battle: Battle
        :return: Move order
        :rtype: str
        """
        available_orders = []
        available_z_moves = set()

        if battle.can_z_move:
            available_z_moves.update(battle.active_pokemon.available_z_moves)
            if not available_z_moves:
                print(battle.active_pokemon.item)
                print(battle.active_pokemon.moves)

        for move in battle.available_moves:
            available_orders.append(self.create_order(move))
            if battle.can_mega_evolve:
                available_orders.append(self.create_order(move, mega=True))
            if battle.can_z_move and move in available_z_moves:
                available_orders.append(self.create_order(move, z_move=True))

        for pokemon in battle.available_switches:
            available_orders.append(self.create_order(pokemon))

        order = np.random.choice(available_orders)
        return order

    async def send_challenges(
        self, opponent: str, n_challenges: int, to_wait: Optional[Event] = None
    ) -> None:
        """Make the player send challenges to opponent.

        opponent must be a string, corresponding to the name of the player to challenge.

        n_challenges defines how many challenges will be sent.

        to_wait is an optional event that can be set, in which case it will be waited
        before launching challenges.

        :param opponent: Player username to challenge.
        :type opponent: str
        :param n_challenges: Number of battles that will be started
        :type n_challenges: int
        :param to_wait: Optional event to wait before launching challenges.
        :type to_wait: Event, optional.
        """
        await self._logged_in.wait()
        self.logger.info("Event logged in received in challenge")

        if to_wait is not None:
            await to_wait.wait()

        start_time = perf_counter()

        for _ in range(n_challenges):
            await self._challenge(opponent, self._format)
            await self._battle_semaphore.acquire()
        await self._battle_count_queue.join()
        self.logger.info(
            "Challenges (%d battles) finished in %fs",
            n_challenges,
            perf_counter() - start_time,
        )

    def reset_battles(self) -> None:
        for battle in self._battles.values():
            if not battle.finished:
                raise EnvironmentError(
                    "Can not reset player's battles while they are still running"
                )
        self._battles = {}

    @staticmethod
    def create_order(
        order: Union[Move, Pokemon], mega: bool = False, z_move: bool = False
    ) -> str:
        """Formats an move order corresponding to the provided pokemon or move.

        :param order: Move to make or Pokemon to switch to.
        :type order: Move or Pokemon
        :param mega: Whether to mega evolve the pokemon, if a move is chosen.
        :type mega: bool
        :param z_move: Whether to make a zmove, if a move is chosen.
        :type z_move: bool
        :return: Formatted move order
        :rtype: str
        """
        if isinstance(order, Move):
            order = f"/choose move {order.id}"
            if mega:
                return order + " mega"
            if z_move:
                return order + " zmove"
            return order
        elif isinstance(order, Pokemon):
            return f"/choose switch {order.species}"
        else:
            raise ValueError(
                "Can not process order corresponding to '%s'"
                " (should be a Pokemon or Move object)" % order
            )

    @property
    def battles(self) -> Dict[str, Battle]:
        return self._battles

    @property
    def n_finished_battles(self) -> int:
        return len([None for b in self._battles.values() if b.finished])

    @property
    def n_lost_battles(self) -> int:
        return len([None for b in self._battles.values() if b.lost])

    @property
    def n_tied_battles(self) -> int:
        return self.n_finished_battles - self.n_lost_battles - self.n_won_battles

    @property
    def n_won_battles(self) -> int:
        return len([None for b in self._battles.values() if b.won])

    @property
    def win_rate(self) -> float:
        return self.n_won_battles / self.n_finished_battles
