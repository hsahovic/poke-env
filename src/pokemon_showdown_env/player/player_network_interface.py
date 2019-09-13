# -*- coding: utf-8 -*-
"""This module defines a base class communicating with showdown servers.
"""

import websockets

from abc import ABC


class PlayerNetwork(ABC):
    """
    Network interface of a player.

    Responsible for communicating with showdown servers.
    """

    def __init__(self, *, server_url: str) -> None:
        self._server_url = server_url

    async def handle_message(self, message: str) -> None:
        pass

    async def listen(self) -> None:
        """Listen to a showdown websocket."""
        async with websockets.connect(self.websocket_url) as websocket:
            self._websocket = websocket
            message = await websocket.recv()
            await self.handle_message(message)

    @property
    def websocket_url(self) -> str:
        return f"ws://{self._server_url}/showdown/websocket"
