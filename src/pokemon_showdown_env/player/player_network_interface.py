# -*- coding: utf-8 -*-
"""This module defines a base class communicating with showdown servers.
"""

import websockets

from abc import ABC
from asyncio import Lock
from typing import Optional


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

    async def change_avatar(self, avatar_id: str) -> None:
        """Changes the player's avatar.

        :param avatar_id: The new avatar id.
        :type avatar_id: str
        """
        await self.send_message(f"/avatar {avatar_id}")

    async def handle_message(self, message: str) -> None:
        pass

    async def listen(self) -> None:
        """Listen to a showdown websocket."""
        async with websockets.connect(self.websocket_url) as websocket:
            self._websocket = websocket
            message = await websocket.recv()
            await self.handle_message(message)

    @property
    def username(self) -> str:
        """The player's username.

        :return: The player's username.
        :rtype: str
        """
        return self._username

    @property
    def websocket_url(self) -> str:
        return f"ws://{self._server_url}/showdown/websocket"
