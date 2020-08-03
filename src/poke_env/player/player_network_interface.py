# -*- coding: utf-8 -*-
"""This module defines a base class for communicating with showdown servers.
"""

import json
import logging
import requests
import websockets  # pyre-ignore

from abc import ABC
from abc import abstractmethod
from asyncio import CancelledError
from asyncio import ensure_future
from asyncio import Event
from asyncio import Lock
from asyncio import sleep
from time import perf_counter
from typing import List
from typing import Optional

from aiologger import Logger  # pyre-ignore
from poke_env.exceptions import ShowdownException
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration


class PlayerNetwork(ABC):
    """
    Network interface of a player.

    Responsible for communicating with showdown servers. Also implements some higher
    level methods for basic tasks, such as changing avatar and low-level message
    handling.
    """

    def __init__(
        self,
        player_configuration: PlayerConfiguration,
        *,
        avatar: Optional[int] = None,
        log_level: Optional[int] = None,
        server_configuration: ServerConfiguration,
        start_listening: bool = True,
    ) -> None:
        """
        :param player_configuration: Player configuration.
        :type player_configuration: PlayerConfiguration
        :param avatar: Player avatar id. Optional.
        :type avatar: int, optional
        :param log_level: The player's logger level.
        :type log_level: int. Defaults to logging's default level.
        :param server_configuration: Server configuration.
        :type server_configuration: ServerConfiguration
        :param start_listening: Wheter to start listening to the server. Defaults to
            True.
        :type start_listening: bool
        """
        self._authentication_url = server_configuration.authentication_url
        self._avatar = avatar
        self._password = player_configuration.password
        self._username = player_configuration.username
        self._server_url = server_configuration.server_url

        self._logged_in: Event = Event()
        self._sending_lock = Lock()

        self._websocket: websockets.client.WebSocketClientProtocol  # pyre-ignore
        self._logger: Logger = self._create_player_logger(log_level)  # pyre-ignore

        if start_listening:
            self._listening_coroutine = ensure_future(self.listen())

    async def _accept_challenge(self, username: str) -> None:
        assert self.logged_in.is_set()
        await self._set_team()
        await self._send_message("/accept %s" % username)

    async def _challenge(self, username: str, format_: str):
        assert self.logged_in.is_set()
        await self._set_team()
        await self._send_message(f"/challenge {username}, {format_}")

    async def _change_avatar(self, avatar_id: Optional[int]) -> None:
        """Changes the player's avatar.

        :param avatar_id: The new avatar id. If None, nothing happens.
        :type avatar_id: int
        """
        await self._wait_for_login()
        if avatar_id is not None:
            await self._send_message(f"/avatar {avatar_id}")

    def _create_player_logger(self, log_level: Optional[int]) -> Logger:
        """Creates a logger for the player.

        Returns a Logger displaying asctime and the player's username before messages.

        :param log_level: The logger's level.
        :type log_level: int
        :return: The logger.
        :rtype: Logger
        """
        logger = logging.getLogger(self._username)

        stream_handler = logging.StreamHandler()
        if log_level is not None:
            logger.setLevel(log_level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)
        return logger

    async def _handle_message(self, message: str) -> None:
        """Handle received messages.

        :param message: The message to parse.
        :type message: str
        """
        try:
            self.logger.debug("Received message to handle: %s", message)

            # Showdown websocket messages are pipe-separated sequences
            split_message = message.split("|")
            assert len(split_message) > 1
            # The type of message is determined by the first entry in the message
            # For battles, this is the zero-th entry
            # Otherwise it is the one-th entry
            if split_message[1] == "challstr":
                # Confirms connection to the server: we can login
                await self._log_in(split_message)
            elif split_message[1] == "updateuser":
                if split_message[2] == " " + self._username:
                    # Confirms successful login
                    self.logged_in.set()
                elif not split_message[2].startswith(" Guest "):
                    self.logger.warning(
                        """Trying to login as %s, showdown returned %s """
                        """- this might prevent future actions from this agent. """
                        """Changing the agent's username might solve this problem.""",
                        self.username,
                        split_message[2],
                    )
            elif "updatechallenges" in split_message[1]:
                # Contain information about current challenge
                await self._update_challenges(split_message)
            elif split_message[0].startswith(">battle"):
                # Battle update
                await self._handle_battle_message(message)
            elif split_message[1] == "updatesearch":
                self.logger.debug("Ignored message: %s", message)
                pass
            elif split_message[1] == "popup":
                self.logger.warning("Popup message received: %s", message)
            elif split_message[1] in ["nametaken"]:
                self.logger.critical("Error message received: %s", message)
                raise ShowdownException("Error message received: %s", message)
            elif split_message[1] == "pm":
                self.logger.info("Received pm: %s", split_message)
            else:
                self.logger.critical("Unhandled message: %s", message)
                raise NotImplementedError("Unhandled message: %s" % message)
        except CancelledError as e:
            self.logger.critical("CancelledError intercepted. %s", e)
        except Exception as exception:
            self.logger.exception(
                "Unhandled exception raised while handling message:\n%s", message
            )
            raise exception

    async def _log_in(self, split_message: List[str]) -> None:
        """Log the player with specified username and password.

        Split message contains information sent by the server. This information is
        necessary to log in.

        :param split_message: Message received from the server that triggers logging in.
        :type split_message: List[str]
        """
        if self._password:
            log_in_request = requests.post(
                self._authentication_url,
                data={
                    "act": "login",
                    "name": self._username,
                    "pass": self._password,
                    "challstr": split_message[2] + "%7C" + split_message[3],
                },
            )
            self.logger.info("Sending authentication request")
            assertion = json.loads(log_in_request.text[1:])["assertion"]
        else:
            self.logger.info("Bypassing authentication request")
            assertion = ""

        await self._send_message(f"/trn {self._username},0,{assertion}")

        await self._change_avatar(self._avatar)

    async def _search_ladder_game(self, format_):
        await self._set_team()
        await self._send_message(f"/search {format_}")

    async def _send_message(
        self, message: str, room: str = "", message_2: Optional[str] = None
    ) -> None:
        """Sends a message to the specified room.

        `message_2` can be used to send a sequence of length 2.

        :param message: The message to send.
        :type message: str
        :param room: The room to which the message should be sent.
        :type room: str
        :param message_2: Second element of the sequence to be sent. Optional.
        :type message_2: str, optional
        """
        if message_2:
            to_send = "|".join([room, message, message_2])
        else:
            to_send = "|".join([room, message])
        await self._websocket.send(to_send)
        self.logger.info(">>> %s", to_send)

    async def _set_team(self):
        if self._team is not None:
            await self._send_message("/utm %s" % self._team.yield_team())

    async def _wait_for_login(
        self, checking_interval: float = 0.001, wait_for: int = 5
    ) -> None:
        start = perf_counter()
        while perf_counter() - start < wait_for:
            await sleep(checking_interval)
            if self.logged_in:
                return
        assert self.logged_in

    async def listen(self) -> None:
        """Listen to a showdown websocket and dispatch messages to be handled."""
        self.logger.info("Starting listening to showdown websocket")
        coroutines = []
        try:
            async with websockets.connect(
                self.websocket_url, max_queue=None
            ) as websocket:
                self._websocket = websocket
                async for message in websocket:
                    self.logger.info("<<< %s", message)
                    coroutines.append(ensure_future(self._handle_message(message)))
        except websockets.exceptions.ConnectionClosedOK:
            self.logger.warning(
                "Websocket connection with %s closed", self.websocket_url
            )
        except (CancelledError, RuntimeError) as e:
            self.logger.critical("Listen interrupted by %s", e)
        except Exception as e:
            self.logger.exception(e)
        finally:
            for coroutine in coroutines:
                coroutine.cancel()

    async def stop_listening(self) -> None:
        if self._listening_coroutine is not None:
            self._listening_coroutine.cancel()
        await self._websocket.close()

    @abstractmethod
    async def _handle_battle_message(self, message: str) -> None:
        """Abstract method.

        Implementation should redirect messages to corresponding battles.
        """

    @abstractmethod
    async def _update_challenges(self, split_message: List[str]) -> None:
        """Abstract method.

        Implementation should keep track of current challenges.
        """

    @property
    def logged_in(self) -> Event:
        """Event object associated with user login.

        :return: The logged-in event
        :rtype: Event
        """
        return self._logged_in

    @property
    def logger(self) -> Logger:
        """Logger associated with the player.

        :return: The logger.
        :rtype: Logger
        """
        return self._logger

    @property
    def username(self) -> str:
        """The player's username.

        :return: The player's username.
        :rtype: str
        """
        return self._username

    @property
    def websocket_url(self) -> str:
        """The websocket url.

        It is derived from the server url.

        :return: The websocket url.
        :rtype: str
        """
        return f"ws://{self._server_url}/showdown/websocket"
