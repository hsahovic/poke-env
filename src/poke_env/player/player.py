# -*- coding: utf-8 -*-
"""This module defines a base class for players.
"""

import asyncio
import random

from abc import ABC
from abc import abstractmethod
from asyncio import Condition
from asyncio import Event
from asyncio import Queue
from asyncio import Semaphore
from json import JSONDecoder
from time import perf_counter
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from poke_env.environment.battle import Battle
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.exceptions import ShowdownException
from poke_env.exceptions import UnexpectedEffectException
from poke_env.player.player_network_interface import PlayerNetwork
from poke_env.player_configuration import _create_player_configuration_from_player
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import LocalhostServerConfiguration
from poke_env.server_configuration import ServerConfiguration
from poke_env.teambuilder.teambuilder import Teambuilder
from poke_env.teambuilder.constant_teambuilder import ConstantTeambuilder
from poke_env.utils import to_id_str


class Player(PlayerNetwork, ABC):
    """
    Base class for players.
    """

    MESSAGES_TO_IGNORE = [""]

    # When an error resulting from an invalid choice is made, the next order has this
    # chance of being showdown's default order to prevent infinite loops
    DEFAULT_CHOICE_CHANCE = 1 / 1000

    def __init__(
        self,
        player_configuration: Optional[PlayerConfiguration] = None,
        *,
        avatar: Optional[int] = None,
        battle_format: str = "gen8randombattle",
        log_level: Optional[int] = None,
        max_concurrent_battles: int = 1,
        server_configuration: Optional[ServerConfiguration] = None,
        start_listening: bool = True,
        team: Optional[Union[str, Teambuilder]] = None,
    ) -> None:
        """
        :param player_configuration: Player configuration. If empty, defaults to an
            automatically generated username with no password. This option must be set
            if the server configuration requires authentication.
        :type player_configuration: PlayerConfiguration, optional
        :param avatar: Player avatar id. Optional.
        :type avatar: int, optional
        :param battle_format: Name of the battle format this player plays. Defaults to
            gen8randombattle.
        :type battle_format: str
        :param log_level: The player's logger level.
        :type log_level: int. Defaults to logging's default level.
        :param max_concurrent_battles: Maximum number of battles this player will play
            concurrently. If 0, no limit will be applied. Defaults to 1.
        :type max_concurrent_battles: int
        :param server_configuration: Server configuration. Defaults to Localhost Server
            Configuration.
        :type server_configuration: ServerConfiguration, optional
        :param start_listening: Wheter to start listening to the server. Defaults to
            True.
        :type start_listening: bool
        :param team: The team to use for formats requiring a team. Can be a showdown
            team string, a showdown packed team string, of a ShowdownTeam object.
            Defaults to None.
        :type team: str or Teambuilder, optional
        """
        if player_configuration is None:
            player_configuration = _create_player_configuration_from_player(self)

        if server_configuration is None:
            server_configuration = LocalhostServerConfiguration

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
        self._battle_end_condition: Condition = Condition()
        self._challenge_queue: Queue = Queue()

        if isinstance(team, Teambuilder):
            self._team = team
        elif isinstance(team, str):
            self._team = ConstantTeambuilder(team)
        else:
            self._team = None

        self.logger.debug("Player initialisation finished")
        self._json_decoder = JSONDecoder()

    def _battle_finished_callback(self, battle: Battle) -> None:
        pass

    async def _create_battle(self, split_message: List[str]) -> Battle:
        """Returns battle object corresponding to received message.

        :param split_message: The battle initialisation message.
        :type split_message: List[str]
        :return: The corresponding battle object.
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
                self.logger.debug(
                    "Battle message too short; ignored: '%s'", "".join(split_message)
                )
            elif split_message[1] in self.MESSAGES_TO_IGNORE:
                pass
            elif split_message[1] == "request":
                if split_message[2]:
                    request = self._json_decoder.decode(split_message[2])
                    if request:
                        battle._parse_request(request)
                        if battle.move_on_next_request:
                            await self._handle_battle_request(battle)
                            battle.move_on_next_request = False
            elif split_message[1] == "title":
                player_1, player_2 = split_message[2].split(" vs. ")
                battle.players = player_1, player_2
            elif split_message[1] == "win" or split_message[1] == "tie":
                if split_message[1] == "win":
                    battle._won_by(split_message[2])
                else:
                    battle._tied()
                await self._battle_count_queue.get()
                self._battle_count_queue.task_done()
                self._battle_finished_callback(battle)
                async with self._battle_end_condition:
                    self._battle_end_condition.notify_all()
            elif split_message[1] == "error":
                if split_message[2].startswith(
                    "[Invalid choice] Sorry, too late to make a different move"
                ):
                    if battle.trapped:
                        await self._handle_battle_request(battle)
                elif split_message[2].startswith(
                    "[Unavailable choice] Can't switch: The active Pokémon is "
                    "trapped"
                ) or split_message[2].startswith(
                    "[Invalid choice] Can't switch: The active Pokémon is trapped"
                ):
                    battle.trapped = True
                    await self._handle_battle_request(battle)
                elif split_message[2].startswith(
                    "[Invalid choice] Can't switch: You can't switch to an active "
                    "Pokémon"
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                elif split_message[2].startswith("[Invalid choice]"):
                    self._manage_error_in(battle)
                elif split_message[2].startswith(
                    "[Unavailable choice]"
                ) and split_message[2].endswith("is disabled"):
                    self._manage_error_in(battle)
                    battle.move_on_next_request = True
                else:
                    self.logger.critical("Unexpected error message: %s", split_message)
            elif split_message[1] == "expire":
                pass
            elif split_message[1] == "turn":
                battle.turn = int(split_message[2])
                await self._handle_battle_request(battle)
            elif split_message[1] == "teampreview":
                await self._handle_battle_request(battle, from_teampreview_request=True)
            else:
                try:
                    battle._parse_message(split_message)
                except UnexpectedEffectException as e:
                    self.logger.exception(e)

    async def _handle_battle_request(
        self,
        battle: Battle,
        from_teampreview_request: bool = False,
        maybe_default_order=False,
    ):
        if maybe_default_order and random.random() < self.DEFAULT_CHOICE_CHANCE:
            message = self.choose_default_move(battle)
        elif battle.teampreview:
            if not from_teampreview_request:
                return
            message = self.teampreview(battle)
        else:
            message = self.choose_move(battle)
        await self._send_message(message, battle.battle_tag)

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
        challenges = self._json_decoder.decode(split_message[2]).get(
            "challengesFrom", {}
        )
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
                    or (opponent == username)
                    or (isinstance(opponent, list) and (username in opponent))
                ):
                    await self._accept_challenge(username)
                    await self._battle_semaphore.acquire()
                    break
        await self._battle_count_queue.join()

    @abstractmethod
    def choose_move(self, battle: Battle) -> str:
        """Abstract method to choose a move in a battle.

        :param battle: The battle.
        :type battle: Battle
        :return: The move order.
        :rtype: str
        """
        pass

    def choose_default_move(self, *args, **kwargs) -> str:
        """Returns showdown's default move order.

        This order will result in the first legal order - according to showdown's
        ordering - being chosen.
        """
        return "/choose default"

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

        for move in battle.available_moves:
            available_orders.append(self.create_order(move))
            if battle.can_mega_evolve:
                available_orders.append(self.create_order(move, mega=True))
            if battle.can_z_move and move in available_z_moves:
                available_orders.append(self.create_order(move, z_move=True))
            if battle.can_dynamax:
                available_orders.append(self.create_order(move, dynamax=True))

        for pokemon in battle.available_switches:
            available_orders.append(self.create_order(pokemon))

        if available_orders:
            order = random.choice(available_orders)
        else:
            order = "/choose default"
        return order

    async def ladder(self, n_games):
        """Make the player play games on the ladder.

        n_games defines how many battles will be played.

        :param n_games: Number of battles that will be played
        :type n_games: int
        """
        await self._logged_in.wait()
        start_time = perf_counter()

        for _ in range(n_games):
            async with self._battle_start_condition:
                await self._search_ladder_game(self._format)
                await self._battle_start_condition.wait()
                while self._battle_count_queue.full():
                    async with self._battle_end_condition:
                        await self._battle_end_condition.wait()
                await self._battle_semaphore.acquire()
        await self._battle_count_queue.join()
        self.logger.info(
            "Laddering (%d battles) finished in %fs",
            n_games,
            perf_counter() - start_time,
        )

    async def battle_against(self, opponent: "Player", n_battles: int) -> None:
        """Make the player play n_battles against opponent.

        This function is a wrapper around send_challenges and accept challenges.

        :param opponent: The opponent to play against.
        :type opponent: Player
        :param n_battles: The number of games to play.
        :type n_battles: int
        """
        await asyncio.gather(
            self.send_challenges(
                to_id_str(opponent.username), n_battles, to_wait=opponent.logged_in
            ),
            opponent.accept_challenges(to_id_str(self.username), n_battles),
        )

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
        self.logger.info("Event logged in received in send challenge")

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

    def random_teampreview(self, battle: Battle) -> str:
        """Returns a random valid teampreview order for the given battle.

        :param battle: The battle.
        :type battle: Battle
        :return: The random teampreview order.
        :rtype: str
        """
        members = list(range(1, len(battle.team) + 1))
        random.shuffle(members)
        return "/team " + "".join([str(c) for c in members])

    def reset_battles(self) -> None:
        for battle in self._battles.values():
            if not battle.finished:
                raise EnvironmentError(
                    "Can not reset player's battles while they are still running"
                )
        self._battles = {}

    def teampreview(self, battle: Battle) -> str:
        """Returns a teampreview order for the given battle.

        This order must be of the form /team TEAM, where TEAM is a string defining the
        team chosen by the player. Multiple formats are supported, among which '3461'
        and '3, 4, 6, 1' are correct and indicate leading with pokemon 3, with pokemons
        4, 6 and 1 in the back in single battles or leading with pokemons 3 and 4 with
        pokemons 6 and 1 in the back in double battles.

        Please refer to Pokemon Showdown's protocol documentation for more information.

        :param battle: The battle.
        :type battle: Battle
        :return: The teampreview order.
        :rtype: str
        """
        return self.random_teampreview(battle)

    @staticmethod
    def create_order(
        order: Union[Move, Pokemon],
        mega: bool = False,
        z_move: bool = False,
        dynamax: bool = False,
    ) -> str:
        """Formats an move order corresponding to the provided pokemon or move.

        :param order: Move to make or Pokemon to switch to.
        :type order: Move or Pokemon
        :param mega: Whether to mega evolve the pokemon, if a move is chosen.
        :type mega: bool
        :param z_move: Whether to make a zmove, if a move is chosen.
        :type z_move: bool
        :param dynamax: Whether to dynamax, if a move is chosen.
        :type dynamax: bool
        :return: Formatted move order
        :rtype: str
        """
        if isinstance(order, Move):
            order = f"/choose move {order.id}"
            if mega:
                return order + " mega"
            if z_move:
                return order + " zmove"
            if dynamax:
                return order + " dynamax"
            return order
        else:
            return f"/choose switch {order.species}"

    @property
    def battles(self) -> Dict[str, Battle]:
        return self._battles

    @property
    def format(self) -> str:
        return self._format

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
