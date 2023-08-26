"""This module defines a base class for players.
"""

import asyncio
import random
from abc import ABC, abstractmethod
from asyncio import Condition, Event, Queue, Semaphore
from logging import Logger
from time import perf_counter
from typing import Any, Awaitable, Dict, List, Optional, Union

import orjson

from poke_env.concurrency import create_in_poke_loop, handle_threaded_coroutines
from poke_env.data import GenData, to_id_str
from poke_env.environment.abstract_battle import AbstractBattle
from poke_env.environment.battle import Battle
from poke_env.environment.double_battle import DoubleBattle
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.exceptions import ShowdownException
from poke_env.player.battle_order import (
    BattleOrder,
    DefaultBattleOrder,
    DoubleBattleOrder,
)
from poke_env.ps_client import PSClient
from poke_env.ps_client.account_configuration import (
    CONFIGURATION_FROM_PLAYER_COUNTER,
    AccountConfiguration,
)
from poke_env.ps_client.server_configuration import (
    LocalhostServerConfiguration,
    ServerConfiguration,
)
from poke_env.teambuilder.constant_teambuilder import ConstantTeambuilder
from poke_env.teambuilder.teambuilder import Teambuilder


class Player(ABC):
    """
    Base class for players.
    """

    MESSAGES_TO_IGNORE = {"", "t:", "expire", "uhtmlchange"}

    # When an error resulting from an invalid choice is made, the next order has this
    # chance of being showdown's default order to prevent infinite loops
    DEFAULT_CHOICE_CHANCE = 1 / 1000

    def __init__(
        self,
        account_configuration: Optional[AccountConfiguration] = None,
        *,
        avatar: Optional[int] = None,
        battle_format: str = "gen9randombattle",
        log_level: Optional[int] = None,
        max_concurrent_battles: int = 1,
        save_replays: Union[bool, str] = False,
        server_configuration: Optional[ServerConfiguration] = None,
        start_timer_on_battle_start: bool = False,
        start_listening: bool = True,
        ping_interval: Optional[float] = 20.0,
        ping_timeout: Optional[float] = 20.0,
        team: Optional[Union[str, Teambuilder]] = None,
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
        :type battle_format: str
        :param log_level: The player's logger level.
        :type log_level: int. Defaults to logging's default level.
        :param max_concurrent_battles: Maximum number of battles this player will play
            concurrently. If 0, no limit will be applied. Defaults to 1.
        :type max_concurrent_battles: int
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
        :param ping_interval: How long between keepalive pings (Important for backend
            websockets). If None, disables keepalive entirely.
        :type ping_interval: float, optional
        :param ping_timeout: How long to wait for a timeout of a specific ping
            (important for backend websockets.
            Increase only if timeouts occur during runtime).
            If None pings will never time out.
        :type ping_timeout: float, optional
        :param start_timer_on_battle_start: Whether to automatically start the battle
            timer on battle start. Defaults to False.
        :type start_timer_on_battle_start: bool
        :param team: The team to use for formats requiring a team. Can be a showdown
            team string, a showdown packed team string, of a ShowdownTeam object.
            Defaults to None.
        :type team: str or Teambuilder, optional
        """
        if account_configuration is None:
            account_configuration = self._create_account_configuration()

        if server_configuration is None:
            server_configuration = LocalhostServerConfiguration

        self.ps_client = PSClient(
            account_configuration=account_configuration,
            avatar=avatar,
            log_level=log_level,
            server_configuration=server_configuration,
            start_listening=start_listening,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
        )

        self.ps_client._handle_battle_message = self._handle_battle_message  # type: ignore
        self.ps_client._update_challenges = self._update_challenges  # type: ignore
        self.ps_client._handle_challenge_request = self._handle_challenge_request  # type: ignore

        self._format: str = battle_format
        self._max_concurrent_battles: int = max_concurrent_battles
        self._save_replays = save_replays
        self._start_timer_on_battle_start: bool = start_timer_on_battle_start

        self._battles: Dict[str, AbstractBattle] = {}
        self._battle_semaphore: Semaphore = create_in_poke_loop(Semaphore, 0)

        self._battle_start_condition: Condition = create_in_poke_loop(Condition)
        self._battle_count_queue: Queue[Any] = create_in_poke_loop(
            Queue, max_concurrent_battles
        )
        self._battle_end_condition: Condition = create_in_poke_loop(Condition)
        self._challenge_queue: Queue[Any] = create_in_poke_loop(Queue)

        if isinstance(team, Teambuilder):
            self._team = team
        elif isinstance(team, str):
            self._team = ConstantTeambuilder(team)
        else:
            self._team = None

        self.logger.debug("Player initialisation finished")

    def _create_account_configuration(self) -> AccountConfiguration:
        key = type(self).__name__
        CONFIGURATION_FROM_PLAYER_COUNTER.update([key])
        username = "%s %d" % (key, CONFIGURATION_FROM_PLAYER_COUNTER[key])
        if len(username) > 18:
            username = "%s %d" % (
                key[: 18 - len(username)],
                CONFIGURATION_FROM_PLAYER_COUNTER[key],
            )
        return AccountConfiguration(username, None)

    def _battle_finished_callback(self, battle: AbstractBattle):
        pass

    def update_team(self, team: Union[Teambuilder, str]):
        """Updates the team used by the player.

        :param team: The new team to use.
        :type team: str or Teambuilder
        """
        if isinstance(team, Teambuilder):
            self._team = team
        else:
            self._team = ConstantTeambuilder(team)

    async def _create_battle(self, split_message: List[str]) -> AbstractBattle:
        """Returns battle object corresponding to received message.

        :param split_message: The battle initialisation message.
        :type split_message: List[str]
        :return: The corresponding battle object.
        :rtype: AbstractBattle
        """
        # We check that the battle has the correct format
        if split_message[1] == self._format and len(split_message) >= 2:
            # Battle initialisation
            battle_tag = "-".join(split_message)[1:]

            if battle_tag in self._battles:
                return self._battles[battle_tag]
            else:
                gen = GenData.from_format(self._format).gen
                if self.format_is_doubles:
                    battle = DoubleBattle(
                        battle_tag=battle_tag,
                        username=self.username,
                        logger=self.logger,
                        save_replays=self._save_replays,
                        gen=gen,
                    )
                else:
                    battle = Battle(
                        battle_tag=battle_tag,
                        username=self.username,
                        logger=self.logger,
                        gen=gen,
                        save_replays=self._save_replays,
                    )

                await self._battle_count_queue.put(None)
                if battle_tag in self._battles:
                    await self._battle_count_queue.get()
                    return self._battles[battle_tag]
                async with self._battle_start_condition:
                    self._battle_semaphore.release()
                    self._battle_start_condition.notify_all()
                    self._battles[battle_tag] = battle

                if self._start_timer_on_battle_start:
                    await self.ps_client.send_message("/timer on", battle.battle_tag)

                return battle
        else:
            self.logger.critical(
                "Unmanaged battle initialisation message received: %s", split_message
            )
            raise ShowdownException()

    async def _get_battle(self, battle_tag: str) -> AbstractBattle:
        battle_tag = battle_tag[1:]
        while True:
            if battle_tag in self._battles:
                return self._battles[battle_tag]
            async with self._battle_start_condition:
                await self._battle_start_condition.wait()

    async def _handle_battle_message(self, split_messages: List[List[str]]):
        """Handles a battle message.

        :param split_message: The received battle message.
        :type split_message: str
        """
        # Battle messages can be multiline
        if (
            len(split_messages) > 1
            and len(split_messages[1]) > 1
            and split_messages[1][1] == "init"
        ):
            battle_info = split_messages[0][0].split("-")
            battle = await self._create_battle(battle_info)
        else:
            battle = await self._get_battle(split_messages[0][0])

        for split_message in split_messages[1:]:
            if len(split_message) <= 1:
                continue
            elif split_message[1] in self.MESSAGES_TO_IGNORE:
                pass
            elif split_message[1] == "request":
                if split_message[2]:
                    request = orjson.loads(split_message[2])
                    battle.parse_request(request)
                    if battle.move_on_next_request:
                        await self._handle_battle_request(battle)
                        battle.move_on_next_request = False
            elif split_message[1] == "win" or split_message[1] == "tie":
                if split_message[1] == "win":
                    battle.won_by(split_message[2])
                else:
                    battle.tied()
                await self._battle_count_queue.get()
                self._battle_count_queue.task_done()
                self._battle_finished_callback(battle)
                async with self._battle_end_condition:
                    self._battle_end_condition.notify_all()
            elif split_message[1] == "error":
                self.logger.log(
                    25, "Error message received: %s", "|".join(split_message)
                )
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
                elif split_message[2].startswith(
                    "[Invalid choice] Can't switch: You can't switch to a fainted "
                    "Pokémon"
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                elif split_message[2].startswith(
                    "[Invalid choice] Can't move: Invalid target for"
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                elif split_message[2].startswith(
                    "[Invalid choice] Can't move: You can't choose a target for"
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                elif split_message[2].startswith(
                    "[Invalid choice] Can't move: "
                ) and split_message[2].endswith("needs a target"):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                elif (
                    split_message[2].startswith("[Invalid choice] Can't move: Your")
                    and " doesn't have a move matching " in split_message[2]
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                elif split_message[2].startswith(
                    "[Invalid choice] Incomplete choice: "
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                elif split_message[2].startswith(
                    "[Unavailable choice]"
                ) and split_message[2].endswith("is disabled"):
                    battle.move_on_next_request = True
                elif split_message[2].startswith("[Invalid choice]") and split_message[
                    2
                ].endswith("is disabled"):
                    battle.move_on_next_request = True
                elif split_message[2].startswith(
                    "[Invalid choice] Can't move: You sent more choices than unfainted"
                    " Pokémon."
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                elif split_message[2].startswith(
                    "[Invalid choice] Can't move: You can only Terastallize once per battle."
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                else:
                    self.logger.critical("Unexpected error message: %s", split_message)
            elif split_message[1] == "turn":
                battle.parse_message(split_message)
                await self._handle_battle_request(battle)
            elif split_message[1] == "teampreview":
                battle.parse_message(split_message)
                await self._handle_battle_request(battle, from_teampreview_request=True)
            elif split_message[1] == "bigerror":
                self.logger.warning("Received 'bigerror' message: %s", split_message)
            else:
                battle.parse_message(split_message)

    async def _handle_battle_request(
        self,
        battle: AbstractBattle,
        from_teampreview_request: bool = False,
        maybe_default_order: bool = False,
    ):
        if maybe_default_order and random.random() < self.DEFAULT_CHOICE_CHANCE:
            message = self.choose_default_move().message
        elif battle.teampreview:
            if not from_teampreview_request:
                return
            message = self.teampreview(battle)
        else:
            message = self.choose_move(battle)
            if isinstance(message, Awaitable):
                message = await message
            message = message.message

        await self.ps_client.send_message(message, battle.battle_tag)

    async def _handle_challenge_request(self, split_message: List[str]):
        """Handles an individual challenge."""
        challenging_player = split_message[2].strip()

        if challenging_player != self.username:
            if len(split_message) >= 6:
                if split_message[5] == self._format:
                    await self._challenge_queue.put(challenging_player)

    async def _update_challenges(self, split_message: List[str]):
        """Update internal challenge state.

        Add corresponding challenges to internal queue of challenges, where they will be
        processed if relevant.

        :param split_message: Recevied message, split.
        :type split_message: List[str]
        """
        self.logger.debug("Updating challenges with %s", split_message)
        challenges = orjson.loads(split_message[2]).get("challengesFrom", {})
        for user, format_ in challenges.items():
            if format_ == self._format:
                await self._challenge_queue.put(user)

    async def accept_challenges(
        self,
        opponent: Optional[Union[str, List[str]]],
        n_challenges: int,
        packed_team: Optional[str],
    ):
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
        :packed_team: Team to use. Defaults to generating a team with the agent's teambuilder.
        :type packed_team: string, optional.
        """
        if packed_team is None:
            packed_team = self.next_team

        await handle_threaded_coroutines(
            self._accept_challenges(opponent, n_challenges, packed_team)
        )

    async def _accept_challenges(
        self,
        opponent: Optional[Union[str, List[str]]],
        n_challenges: int,
        packed_team: Optional[str],
    ):
        if opponent:
            if isinstance(opponent, list):
                opponent = [to_id_str(o) for o in opponent]
            else:
                opponent = to_id_str(opponent)
        await self.ps_client.logged_in.wait()
        self.logger.debug("Event logged in received in accept_challenge")

        for _ in range(n_challenges):
            while True:
                username = to_id_str(await self._challenge_queue.get())
                self.logger.debug(
                    "Consumed %s from challenge queue in accept_challenge", username
                )
                if (
                    (opponent is None)
                    or (opponent == username)
                    or (isinstance(opponent, list) and (username in opponent))
                ):
                    await self.ps_client.accept_challenge(username, packed_team)
                    await self._battle_semaphore.acquire()
                    break
        await self._battle_count_queue.join()

    @abstractmethod
    def choose_move(
        self, battle: AbstractBattle
    ) -> Union[BattleOrder, Awaitable[BattleOrder]]:
        """Abstract method to choose a move in a battle.

        :param battle: The battle.
        :type battle: AbstractBattle
        :return: The move order.
        :rtype: str
        """
        pass

    def choose_default_move(self) -> DefaultBattleOrder:
        """Returns showdown's default move order.

        This order will result in the first legal order - according to showdown's
        ordering - being chosen.
        """
        return DefaultBattleOrder()

    def choose_random_doubles_move(self, battle: DoubleBattle) -> BattleOrder:
        active_orders: List[List[BattleOrder]] = [[], []]

        for (
            orders,
            mon,
            switches,
            moves,
            can_mega,
            can_z_move,
            can_dynamax,
            can_tera,
        ) in zip(
            active_orders,
            battle.active_pokemon,
            battle.available_switches,
            battle.available_moves,
            battle.can_mega_evolve,
            battle.can_z_move,
            battle.can_dynamax,
            battle.can_tera,
        ):
            if mon:
                targets = {
                    move: battle.get_possible_showdown_targets(move, mon)
                    for move in moves
                }
                orders.extend(
                    [
                        BattleOrder(move, move_target=target)
                        for move in moves
                        for target in targets[move]
                    ]
                )
                orders.extend([BattleOrder(switch) for switch in switches])

                if can_mega:
                    orders.extend(
                        [
                            BattleOrder(move, move_target=target, mega=True)
                            for move in moves
                            for target in targets[move]
                        ]
                    )
                if can_z_move:
                    available_z_moves = set(mon.available_z_moves)
                    orders.extend(
                        [
                            BattleOrder(move, move_target=target, z_move=True)
                            for move in moves
                            for target in targets[move]
                            if move in available_z_moves
                        ]
                    )

                if can_dynamax:
                    orders.extend(
                        [
                            BattleOrder(move, move_target=target, dynamax=True)
                            for move in moves
                            for target in targets[move]
                        ]
                    )

                if can_tera:
                    orders.extend(
                        [
                            BattleOrder(move, move_target=target, terastallize=True)
                            for move in moves
                            for target in targets[move]
                        ]
                    )

                if sum(battle.force_switch) == 1:
                    if orders:
                        return orders[int(random.random() * len(orders))]
                    return self.choose_default_move()

        orders = DoubleBattleOrder.join_orders(*active_orders)

        if orders:
            return orders[int(random.random() * len(orders))]
        else:
            return DefaultBattleOrder()

    def choose_random_singles_move(self, battle: Battle) -> BattleOrder:
        available_orders = [BattleOrder(move) for move in battle.available_moves]
        available_orders.extend(
            [BattleOrder(switch) for switch in battle.available_switches]
        )

        if battle.can_mega_evolve:
            available_orders.extend(
                [BattleOrder(move, mega=True) for move in battle.available_moves]
            )

        if battle.can_dynamax:
            available_orders.extend(
                [BattleOrder(move, dynamax=True) for move in battle.available_moves]
            )

        if battle.can_tera:
            available_orders.extend(
                [
                    BattleOrder(move, terastallize=True)
                    for move in battle.available_moves
                ]
            )

        if battle.can_z_move and battle.active_pokemon:
            available_z_moves = set(battle.active_pokemon.available_z_moves)
            available_orders.extend(
                [
                    BattleOrder(move, z_move=True)
                    for move in battle.available_moves
                    if move in available_z_moves
                ]
            )

        if available_orders:
            return available_orders[int(random.random() * len(available_orders))]
        else:
            return self.choose_default_move()

    def choose_random_move(self, battle: AbstractBattle) -> BattleOrder:
        """Returns a random legal move from battle.

        :param battle: The battle in which to move.
        :type battle: AbstractBattle
        :return: Move order
        :rtype: str
        """
        if isinstance(battle, Battle):
            return self.choose_random_singles_move(battle)
        elif isinstance(battle, DoubleBattle):
            return self.choose_random_doubles_move(battle)
        else:
            raise ValueError(
                "battle should be Battle or DoubleBattle. Received %d" % (type(battle))
            )

    async def ladder(self, n_games: int):
        """Make the player play games on the ladder.

        n_games defines how many battles will be played.

        :param n_games: Number of battles that will be played
        :type n_games: int
        """
        await handle_threaded_coroutines(self._ladder(n_games))

    async def _ladder(self, n_games: int):
        await self.ps_client.logged_in.wait()
        start_time = perf_counter()

        for _ in range(n_games):
            async with self._battle_start_condition:
                await self.ps_client.search_ladder_game(self._format, self.next_team)
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

    async def battle_against(self, opponent: "Player", n_battles: int = 1):
        """Make the player play n_battles against opponent.

        This function is a wrapper around send_challenges and accept challenges.

        :param opponent: The opponent to play against.
        :type opponent: Player
        :param n_battles: The number of games to play. Defaults to 1.
        :type n_battles: int
        """
        await handle_threaded_coroutines(self._battle_against(opponent, n_battles))

    async def _battle_against(self, opponent: "Player", n_battles: int):
        await asyncio.gather(
            self.send_challenges(
                to_id_str(opponent.username),
                n_battles,
                to_wait=opponent.ps_client.logged_in,
            ),
            opponent.accept_challenges(
                to_id_str(self.username), n_battles, opponent.next_team
            ),
        )

    async def send_challenges(
        self, opponent: str, n_challenges: int, to_wait: Optional[Event] = None
    ):
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
        await handle_threaded_coroutines(
            self._send_challenges(opponent, n_challenges, to_wait)
        )

    async def _send_challenges(
        self, opponent: str, n_challenges: int, to_wait: Optional[Event] = None
    ):
        await self.ps_client.logged_in.wait()
        self.logger.info("Event logged in received in send challenge")

        if to_wait is not None:
            await to_wait.wait()

        start_time = perf_counter()

        for _ in range(n_challenges):
            await self.ps_client.challenge(opponent, self._format, self.next_team)
            await self._battle_semaphore.acquire()
        await self._battle_count_queue.join()
        self.logger.info(
            "Challenges (%d battles) finished in %fs",
            n_challenges,
            perf_counter() - start_time,
        )

    def random_teampreview(self, battle: AbstractBattle) -> str:
        """Returns a random valid teampreview order for the given battle.

        :param battle: The battle.
        :type battle: AbstractBattle
        :return: The random teampreview order.
        :rtype: str
        """
        members = list(range(1, len(battle.team) + 1))
        random.shuffle(members)
        return "/team " + "".join([str(c) for c in members])

    def reset_battles(self):
        """Resets the player's inner battle tracker."""
        for battle in list(self._battles.values()):
            if not battle.finished:
                raise EnvironmentError(
                    "Can not reset player's battles while they are still running"
                )
        self._battles = {}

    def teampreview(self, battle: AbstractBattle) -> str:
        """Returns a teampreview order for the given battle.

        This order must be of the form /team TEAM, where TEAM is a string defining the
        team chosen by the player. Multiple formats are supported, among which '3461'
        and '3, 4, 6, 1' are correct and indicate leading with pokemon 3, with pokemons
        4, 6 and 1 in the back in single battles or leading with pokemons 3 and 4 with
        pokemons 6 and 1 in the back in double battles.

        Please refer to Pokemon Showdown's protocol documentation for more information.

        :param battle: The battle.
        :type battle: AbstractBattle
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
        terastallize: bool = False,
        move_target: int = DoubleBattle.EMPTY_TARGET_POSITION,
    ) -> BattleOrder:
        """Formats an move order corresponding to the provided pokemon or move.

        :param order: Move to make or Pokemon to switch to.
        :type order: Move or Pokemon
        :param mega: Whether to mega evolve the pokemon, if a move is chosen.
        :type mega: bool
        :param z_move: Whether to make a zmove, if a move is chosen.
        :type z_move: bool
        :param dynamax: Whether to dynamax, if a move is chosen.
        :type dynamax: bool
        :param terastallize: Whether to terastallize, if a move is chosen.
        :type terastallize: bool
        :param move_target: Target Pokemon slot of a given move
        :type move_target: int
        :return: Formatted move order
        :rtype: str
        """
        return BattleOrder(
            order,
            mega=mega,
            move_target=move_target,
            z_move=z_move,
            dynamax=dynamax,
            terastallize=terastallize,
        )

    @property
    def battles(self) -> Dict[str, AbstractBattle]:
        return self._battles

    @property
    def format(self) -> str:
        return self._format

    @property
    def format_is_doubles(self) -> bool:
        format_lowercase = self._format.lower()
        return (
            "vgc" in format_lowercase
            or "double" in format_lowercase
            or "metronome" in format_lowercase
        )

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

    @property
    def logger(self) -> Logger:
        return self.ps_client.logger

    @property
    def username(self) -> str:
        return self.ps_client.username

    @property
    def next_team(self) -> Optional[str]:
        if self._team:
            return self._team.yield_team()
        return None
