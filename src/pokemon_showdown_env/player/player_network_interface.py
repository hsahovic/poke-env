# -*- coding: utf-8 -*-
"""This module defines a base class communicating with showdown servers.
"""

import json
import logging
import requests
import websockets

from abc import ABC, abstractmethod
from asyncio import Lock
from typing import List, Optional

from pokemon_showdown_env.exceptions import ShowdownException


class PlayerNetwork(ABC):
    """
    Network interface of a player.

    Responsible for communicating with showdown servers.
    """

    def __init__(
        self,
        username: str,
        password: str,
        *,
        avatar: Optional[int] = None,
        authentication_url: str,
        server_url: str,
    ) -> None:
        """
        :param username: Player username.
        :type username: str
        :param password: Player password.
        :type password: str
        :param avatar: Player avatar id. Optional.
        :type avatar: int, optional
        :param authentication_url: Authentication server url.
        :type authentication_url: str
        :param server_url: Server URL.
        :type server_url: str
        """
        self._authentication_url = authentication_url
        self._avatar = avatar
        self._lock = Lock()
        self._password = password
        self._username = username
        self._server_url = server_url

        self._logged_in: bool = False
        self._websocket = None

    async def _log_in(self, split_message: List[str]) -> None:
        """Log the player with specified username and password.

        Split message contains information sent by the server. This information is
        necessary to log in.

        :param split_message: Message received from the server that triggers logging in.
        :type split_message: List[str]
        """
        log_in_request = requests.post(
            self._authentication_url,
            data={
                "act": "login",
                "name": self._username,
                "pass": self._password,
                "challstr": split_message[2] + "%7C" + split_message[3],
            },
        )
        await self.send_message(
            f"""/trn {self._username},0,{
                json.loads(log_in_request.text[1:])['assertion']
            }"""
        )

        # If there is an avatar to select, select it
        if self._avatar:
            self.change_avatar(self._avatar)

    async def change_avatar(self, avatar_id: str) -> None:
        """Changes the player's avatar.

        :param avatar_id: The new avatar id.
        :type avatar_id: str
        """
        await self.send_message(f"/avatar {avatar_id}")

    @abstractmethod
    async def handle_battle_message(self, split_message: List[str]) -> None:
        pass

    async def handle_message(self, message: str) -> None:
        """Handle received messages.

        :param message: The message to parse.
        :type message: str
        """
        logging.debug("Received message to handle: %s", message)

        # Showdown websocket messages are pipe-separated sequences
        split_message = message.split("|")

        # The type of message is determined by the first entry in the message
        # For battles, this is the zero-th entry
        # Otherwisem it is the one-th entry
        if split_message[1] == "challstr":
            # Confirms connection to the server: we can login
            await self._log_in(split_message)
        elif split_message[1] == "updateuser" and split_message[2] == self.username:
            # Confirms successful login
            self._logged_in = True
        elif "updatechallenges" in split_message[1]:
            # Contain information about current challenge
            self.update_challenges(split_message)
        elif split_message[0].startswith(">battle"):
            # Battle update
            await self.handle_battle_message(split_message)
        elif split_message[1] in ["updatesearch", "popup", "updateuser"]:
            logging.info("Ignored message: %s", message)
            pass
        elif split_message[1] in ["nametaken"]:
            logging.critical("Error message received: %s", message)
            raise ShowdownException("Error message received: %s", message)
        else:
            logging.warning("Unhandled message: %s", message)

    async def listen(self) -> None:
        """Listen to a showdown websocket and dispatch messages to be handled."""
        logging.info("Starting listening to showdown websocket")
        async with websockets.connect(self.websocket_url) as websocket:
            logging.info("Connection to websocket established")
            self._websocket = websocket
            while True:
                message = await websocket.recv()
                logging.debug("Received message: %s", message)
                await self.handle_message(message)

    async def send_message(
        self, message: str, room: Optional[str] = "", message_2: Optional[str] = None
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
        async with self._lock:
            await self._websocket.send(to_send)
        logging.debug("Sent message from %s : %s", self.username, to_send)

    @abstractmethod
    def update_challenges(self, split_message: List[str]) -> None:
        pass

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
