# -*- coding: utf-8 -*-

import asyncio
import logging
import pytest
import websockets

from collections import namedtuple
from asynctest.mock import CoroutineMock
from asynctest.mock import patch
from asynctest.mock import PropertyMock
from poke_env.player.player_network_interface import PlayerNetwork
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ServerConfiguration


player_configuration = PlayerConfiguration("username", "password")
requests_tuple = namedtuple("requests_tuple", ["text"])
server_configuration = ServerConfiguration("server.url", "auth.url")


class PlayerNetworkChild(PlayerNetwork):
    async def _handle_battle_message(self, message):
        pass

    async def _update_challenges(self):
        pass


def test_init_and_properties():
    player = PlayerNetworkChild(
        player_configuration=player_configuration,
        server_configuration=server_configuration,
        start_listening=False,
    )

    assert player.username == "username"
    assert player.websocket_url == "ws://server.url/showdown/websocket"


def test_create_player_logger():
    player = PlayerNetworkChild(
        player_configuration=player_configuration,
        server_configuration=server_configuration,
        start_listening=False,
        log_level=38,
    )

    assert isinstance(player._logger, logging.Logger)
    assert player._logger.getEffectiveLevel() == 38

    logger = player._create_player_logger(24)

    assert isinstance(logger, logging.Logger)
    assert logger.getEffectiveLevel() == 24


@pytest.mark.asyncio
@patch(
    "poke_env.player.player_network_interface.requests.post",
    return_value=requests_tuple(':{"assertion":"content"}'),
)
async def test_log_in(post_mock):
    player = PlayerNetworkChild(
        player_configuration=player_configuration,
        avatar=12,
        server_configuration=server_configuration,
        log_level=38,
        start_listening=False,
    )

    player._send_message = CoroutineMock()
    player._change_avatar = CoroutineMock()

    await player._log_in(["A", "B", "C", "D"])

    player._change_avatar.assert_called_once_with(12)
    player._send_message.assert_called_once_with("/trn username,0,content")
    post_mock.assert_called_once()


@pytest.mark.asyncio
async def test_change_avatar():
    player = PlayerNetworkChild(
        player_configuration=player_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )

    player._send_message = CoroutineMock()
    player._logged_in.set()

    await player._change_avatar(8)

    player._send_message.assert_called_once_with("/avatar 8")


@pytest.mark.asyncio
async def test_handle_message():
    player = PlayerNetworkChild(
        player_configuration=player_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )
    player._log_in = CoroutineMock()

    await player._handle_message("|challstr")
    player._log_in.assert_called_once()

    assert player.logged_in.is_set() is False
    await player._handle_message("|updateuser| username")
    assert player._logged_in.is_set() is True

    player._update_challenges = CoroutineMock()
    await player._handle_message("|updatechallenges")
    player._update_challenges.assert_called_once_with(["", "updatechallenges"])

    player._handle_battle_message = CoroutineMock()
    await player._handle_message(">battle|thing")
    player._handle_battle_message.assert_called_once_with([[">battle", "thing"]])

    await player._handle_message("|updatesearch")

    player._logger.warning = CoroutineMock()
    await player._handle_message("that was unexpected!|")
    player._logger.warning.assert_called_once_with(
        "Unhandled message: %s", "that was unexpected!|"
    )


@pytest.mark.asyncio
async def test_listen():
    player = PlayerNetworkChild(
        player_configuration=player_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )

    type(player).websocket_url = PropertyMock(return_value="ws://localhost:8899")

    player._handle_message = CoroutineMock()
    semaphore = asyncio.Semaphore()

    async def showdown_server_mock(websocket, path):
        semaphore.release()
        await websocket.ping()
        await websocket.send("error|test 1")
        await websocket.send("error|test 2")
        await websocket.send("error|test 3")

    await semaphore.acquire()

    gathered = asyncio.gather(websockets.serve(showdown_server_mock, "0.0.0.0", 8899))

    await player.listen()

    await gathered
    assert player._handle_message.await_count == 3
    player._handle_message.assert_awaited_with("error|test 3")


@pytest.mark.asyncio
async def test_send_message():
    player = PlayerNetworkChild(
        player_configuration=player_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )
    player._websocket = CoroutineMock()
    player._websocket.send = CoroutineMock()

    await player._send_message("hey", "home")
    player._websocket.send.assert_called_once_with("home|hey")

    await player._send_message("hey", "home", "hey again")
    player._websocket.send.assert_called_with("home|hey|hey again")
