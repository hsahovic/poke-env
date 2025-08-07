"""This module defines a base class for players."""

from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from asyncio import Condition, Event, Queue, Semaphore
from logging import Logger
from time import perf_counter
from typing import Any, Awaitable, Dict, List, Optional, Union

import orjson

from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.battle.battle import Battle
from poke_env.battle.double_battle import DoubleBattle
from poke_env.battle.move import Move
from poke_env.battle.pokemon import Pokemon
from poke_env.concurrency import create_in_poke_loop, handle_threaded_coroutines
from poke_env.data import GenData, to_id_str
from poke_env.exceptions import ShowdownException
from poke_env.player.battle_order import (
    BattleOrder,
    DefaultBattleOrder,
    DoubleBattleOrder,
    SingleBattleOrder,
)
from poke_env.ps_client import PSClient
from poke_env.ps_client.account_configuration import AccountConfiguration
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

    MESSAGES_TO_IGNORE = {"t:", "expire", "uhtmlchange"}

    # When an error resulting from an invalid choice is made, the next order has this
    # chance of being showdown's default order to prevent infinite loops
    DEFAULT_CHOICE_CHANCE = 1 / 1000

    def __init__(
        self,
        account_configuration: Optional[AccountConfiguration] = None,
        *,
        avatar: Optional[str] = None,
        battle_format: str = "gen9randombattle",
        log_level: Optional[int] = None,
        max_concurrent_battles: int = 1,
        accept_open_team_sheet: bool = False,
        save_replays: Union[bool, str] = False,
        server_configuration: ServerConfiguration = LocalhostServerConfiguration,
        start_timer_on_battle_start: bool = False,
        start_listening: bool = True,
        open_timeout: Optional[float] = 10.0,
        ping_interval: Optional[float] = 20.0,
        ping_timeout: Optional[float] = 20.0,
        team: Optional[Union[str, Teambuilder]] = None,
    ):
        """
        :param account_configuration: Player configuration. If empty, defaults to an
            automatically generated username with no password. This option must be set
            if the server configuration requires authentication.
        :type account_configuration: AccountConfiguration, optional
        :param avatar: Player avatar name. Optional.
        :type avatar: str, optional
        :param battle_format: Name of the battle format this player plays. Defaults to
            gen9randombattle.
        :type battle_format: str
        :param log_level: The player's logger level.
        :type log_level: int. Defaults to logging's default level.
        :param max_concurrent_battles: Maximum number of battles this player will play
            concurrently. If 0, no limit will be applied. Defaults to 1.
        :type max_concurrent_battles: int
        :param accept_open_team_sheet: Boolean to define whether we want to accept or reject open team
            sheet requests
        :type accept_open_team_sheet: bool
        :param save_replays: Whether to save battle replays. Can be a boolean, where
            True will lead to replays being saved in a potentially new /replay folder,
            or a string representing a folder where replays will be saved.
        :type save_replays: bool or str
        :param server_configuration: Server configuration. Defaults to Localhost Server
            Configuration.
        :type server_configuration: ServerConfiguration
        :param start_listening: Whether to start listening to the server. Defaults to
            True.
        :type start_listening: bool
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
        :param start_timer_on_battle_start: Whether to automatically start the battle
            timer on battle start. Defaults to False.
        :type start_timer_on_battle_start: bool
        :param team: The team to use for formats requiring a team. Can be a showdown
            team string, a showdown packed team string, of a ShowdownTeam object.
            Defaults to None.
        :type team: str or Teambuilder, optional
        """
        self.ps_client = PSClient(
            account_configuration=account_configuration
            or AccountConfiguration.generate(self.__class__.__name__),
            avatar=avatar,
            log_level=log_level,
            server_configuration=server_configuration,
            start_listening=start_listening,
            open_timeout=open_timeout,
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
        self._accept_open_team_sheet: bool = accept_open_team_sheet

        self._battles: Dict[str, AbstractBattle] = {}
        self._battle_semaphore: Semaphore = create_in_poke_loop(Semaphore, 0)

        self._battle_start_condition: Condition = create_in_poke_loop(Condition)
        self._battle_count_queue: Queue[Any] = create_in_poke_loop(
            Queue, max_concurrent_battles
        )
        self._battle_end_condition: Condition = create_in_poke_loop(Condition)
        self._challenge_queue: Queue[Any] = create_in_poke_loop(Queue)
        self._waiting: Event = create_in_poke_loop(Event)
        self._trying_again: Event = create_in_poke_loop(Event)
        self._team: Optional[Teambuilder] = None

        if isinstance(team, Teambuilder):
            self._team = team
        elif isinstance(team, str):
            self._team = ConstantTeambuilder(team)

        self.logger.debug("Player initialisation finished")

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
                    battle: AbstractBattle = DoubleBattle(
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

                # Add our team as teampreview_team, as part of battle initialisation
                if isinstance(self._team, ConstantTeambuilder):
                    battle.teampreview_team = [
                        Pokemon(gen=gen, teambuilder=tb_mon)
                        for tb_mon in self._team.team
                    ]

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

                if hasattr(self.ps_client, "websocket") and "vgc" in self.format:
                    if self.accept_open_team_sheet:
                        await self.ps_client.send_message(
                            "/acceptopenteamsheets", room=battle_tag
                        )
                    else:
                        await self.ps_client.send_message(
                            "/rejectopenteamsheets", room=battle_tag
                        )

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
            if not split_message:
                continue
            elif len(split_message) == 1:
                if (
                    battle.teampreview
                    and self.accept_open_team_sheet
                    and "rejected open team sheets." in split_message[0]
                ):
                    await self._handle_battle_request(battle)
            elif split_message[1] == "":
                battle.parse_message(split_message)
            elif split_message[1] in self.MESSAGES_TO_IGNORE:
                pass
            elif split_message[1] == "request":
                if split_message[2]:
                    request = orjson.loads(split_message[2])
                    battle.parse_request(request)
                    if battle._wait:
                        self._waiting.set()
                    elif not (battle.teampreview and self.accept_open_team_sheet):
                        await self._handle_battle_request(battle)
            elif split_message[1] == "showteam":
                role = split_message[2]
                teambuilder_team = Teambuilder.parse_packed_team(
                    "|".join(split_message[3:])
                )
                teampreview_team = (
                    battle.teampreview_team
                    if role == battle.player_role
                    else battle.teampreview_opponent_team
                )
                for preview_mon in teampreview_team:
                    teambuilder_mon = [
                        m
                        for m in teambuilder_team
                        if preview_mon.base_species in to_id_str(m.nickname)
                    ][0]
                    mon = battle.get_pokemon(
                        f"{role}: {teambuilder_mon.nickname}",
                        details=preview_mon._last_details,
                    )
                    mon._update_from_teambuilder(teambuilder_mon)
                # only handle battle request after all open sheets are processed
                if role == "p2":
                    await self._handle_battle_request(battle)
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
                if hasattr(self.ps_client, "websocket"):
                    await self.ps_client.send_message(f"/leave {battle.battle_tag}")
            elif split_message[1] == "error":
                self.logger.log(
                    25, "Error message received: %s", "|".join(split_message)
                )
                if split_message[2].startswith(
                    "[Invalid choice] Sorry, too late to make a different move"
                ):
                    if battle.trapped:
                        self._trying_again.set()
                elif split_message[2].startswith(
                    "[Unavailable choice] Can't switch: The active Pokémon is "
                    "trapped"
                ) or split_message[2].startswith(
                    "[Invalid choice] Can't switch: The active Pokémon is trapped"
                ):
                    self._trying_again.set()
                elif split_message[2].startswith("[Invalid choice] Can't pass: "):
                    await self._handle_battle_request(battle, maybe_default_order=True)
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
                    self._trying_again.set()
                elif split_message[2].startswith("[Invalid choice]") and split_message[
                    2
                ].endswith("is disabled"):
                    self._trying_again.set()
                elif split_message[2].startswith(
                    "[Invalid choice] Can't move: You sent more choices than unfainted"
                    " Pokémon."
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                elif split_message[2].startswith(
                    "[Invalid choice] Can't move: You can only Terastallize once per battle."
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                elif split_message[2].startswith(
                    "[Invalid choice] Unknown error for choice:"
                ):
                    await self._handle_battle_request(battle, maybe_default_order=True)
                else:
                    self.logger.critical("Unexpected error message: %s", split_message)
            elif split_message[1] == "bigerror":
                self.logger.warning("Received 'bigerror' message: %s", split_message)
            else:
                battle.parse_message(split_message)

    async def _handle_battle_request(
        self,
        battle: AbstractBattle,
        maybe_default_order: bool = False,
    ):
        if maybe_default_order and (
            "illusion" in [p.ability for p in battle.team.values()]
            or random.random() < self.DEFAULT_CHOICE_CHANCE
        ):
            message = self.choose_default_move().message
        elif battle.teampreview:
            message = self.teampreview(battle)
        else:
            if maybe_default_order:
                self._trying_again.set()
            choice = self.choose_move(battle)
            if isinstance(choice, Awaitable):
                choice = await choice
            message = choice.message
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
        packed_team: Optional[str] = None,
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
            team = packed_team or self.next_team
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
                    await self.ps_client.accept_challenge(username, team)
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

    @staticmethod
    def choose_default_move() -> DefaultBattleOrder:
        """Returns showdown's default move order.

        This order will result in the first legal order - according to showdown's
        ordering - being chosen.
        """
        return DefaultBattleOrder()

    @staticmethod
    def choose_random_doubles_move(battle: DoubleBattle) -> DoubleBattleOrder:
        orders = DoubleBattleOrder.join_orders(*battle.valid_orders)
        if orders:
            return orders[int(random.random() * len(orders))]
        else:
            return DoubleBattleOrder(DefaultBattleOrder(), DefaultBattleOrder())

    @staticmethod
    def choose_random_singles_move(battle: Battle) -> SingleBattleOrder:
        orders = battle.valid_orders
        if orders:
            return orders[int(random.random() * len(orders))]
        else:
            return Player.choose_default_move()

    @staticmethod
    def choose_random_move(battle: AbstractBattle) -> BattleOrder:
        """Returns a random legal move from battle.

        :param battle: The battle in which to move.
        :type battle: AbstractBattle
        :return: Move order
        :rtype: str
        """
        if isinstance(battle, DoubleBattle):
            return Player.choose_random_doubles_move(battle)
        elif isinstance(battle, Battle):
            return Player.choose_random_singles_move(battle)
        else:
            raise ValueError(
                f"battle should be Battle or DoubleBattle. Received {type(battle)}"
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

    async def battle_against(self, *opponents: Player, n_battles: int = 1):
        """Make the player play n_battles against the given opponents.

        This function is a wrapper around send_challenges and accept_challenges.

        :param opponents: The opponents to play against.
        :type opponents: Player
        :param n_battles: The number of games to play. Defaults to 1.
        :type n_battles: int
        """
        await handle_threaded_coroutines(
            self._battle_against(*opponents, n_battles=n_battles)
        )

    async def _battle_against(self, *opponents: Player, n_battles: int):
        for opponent in opponents:
            await asyncio.gather(
                self.send_challenges(
                    to_id_str(opponent.username),
                    n_battles,
                    to_wait=opponent.ps_client.logged_in,
                ),
                opponent.accept_challenges(to_id_str(self.username), n_battles),
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
    ) -> SingleBattleOrder:
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
        return SingleBattleOrder(
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
    def accept_open_team_sheet(self) -> bool:
        return self._accept_open_team_sheet

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
