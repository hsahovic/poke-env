# -*- coding: utf-8 -*-

import asyncio
import logging
import pytest
import websockets

from collections import namedtuple
from asynctest.mock import CoroutineMock
from asynctest.mock import patch
from asynctest.mock import PropertyMock
from pokemon_showdown_env.player.player_network_interface import PlayerNetwork


requests_tuple = namedtuple("requests_tuple", ["text"])


class PlayerNetworkChild(PlayerNetwork):
    def handle_battle_message(self, message):
        pass

    def update_challenges(self):
        pass


def test_init_and_properties():
    player = PlayerNetworkChild(
        "username", "password", authentication_url="auth.url", server_url="server.url"
    )

    assert player.username == "username"
    assert player.websocket_url == "ws://server.url/showdown/websocket"


def test_create_player_logger():
    player = PlayerNetworkChild(
        "username",
        "password",
        authentication_url="auth.url",
        server_url="server.url",
        log_level=38,
    )

    assert isinstance(player._logger, logging.Logger)
    assert player._logger.getEffectiveLevel() == 38

    logger = player._create_player_logger(24)

    assert isinstance(logger, logging.Logger)
    assert logger.getEffectiveLevel() == 24


@pytest.mark.asyncio
@patch(
    "pokemon_showdown_env.player.player_network_interface.requests.post",
    return_value=requests_tuple(':{"assertion":"content"}'),
)
async def test_log_in(post_mock):
    player = PlayerNetworkChild(
        "username",
        "password",
        avatar=12,
        authentication_url="auth.url",
        server_url="server.url",
        log_level=38,
    )

    player.send_message = CoroutineMock()
    player.change_avatar = CoroutineMock()

    await player._log_in(["A", "B", "C", "D"])

    player.change_avatar.assert_called_once_with(12)
    player.send_message.assert_called_once_with("/trn username,0,content")
    post_mock.assert_called_once()


@pytest.mark.asyncio
async def test_change_avatar():
    player = PlayerNetworkChild(
        "username",
        "password",
        avatar=12,
        authentication_url="auth.url",
        server_url="server.url",
    )

    player.send_message = CoroutineMock()

    await player.change_avatar(8)

    player.send_message.assert_called_once_with("/avatar 8")


@pytest.mark.asyncio
async def test_handle_message():
    pass


@pytest.mark.asyncio
async def test_listen():
    player = PlayerNetworkChild(
        "username",
        "password",
        avatar=12,
        authentication_url="auth.url",
        server_url="server.url",
    )

    type(player).websocket_url = PropertyMock(return_value="ws://localhost:8899")

    player.handle_message = CoroutineMock()
    semaphore = asyncio.Semaphore()

    async def showdown_server_mock(websocket, path):
        semaphore.release()
        await websocket.ping()
        await websocket.send("test 1")
        await websocket.send("test 2")
        await websocket.send("test 3")

    await semaphore.acquire()

    gathered = asyncio.gather(websockets.serve(showdown_server_mock, "0.0.0.0", 8899))

    await player.listen()

    await gathered
    assert player.handle_message.await_count == 3
    player.handle_message.assert_awaited_with("test 3")


def test_send_message():
    pass
