import asyncio
import logging
from collections import namedtuple
from unittest.mock import AsyncMock, PropertyMock, patch

import pytest
import websockets

from poke_env import AccountConfiguration, ServerConfiguration
from poke_env.player import PSClient

account_configuration = AccountConfiguration("username", "password")
requests_tuple = namedtuple("requests_tuple", ["text"])
server_configuration = ServerConfiguration("server.url", "auth.url")


class PSClientChild(PSClient):
    async def _handle_battle_message(self, message):
        pass

    async def _update_challenges(self):
        pass

    async def _handle_challenge_request(self):
        pass


def test_init_and_properties():
    player = PSClientChild(
        account_configuration=account_configuration,
        server_configuration=server_configuration,
        start_listening=False,
    )

    assert player.username == "username"
    assert player.websocket_url == "ws://server.url/showdown/websocket"


def test_create_logger():
    player = PSClientChild(
        account_configuration=account_configuration,
        server_configuration=server_configuration,
        start_listening=False,
        log_level=38,
    )

    assert isinstance(player._logger, logging.Logger)
    assert player._logger.getEffectiveLevel() == 38

    logger = player._create_logger(24)

    assert isinstance(logger, logging.Logger)
    assert logger.getEffectiveLevel() == 24


@pytest.mark.asyncio
@patch(
    "poke_env.ps_client.ps_client.requests.post",
    return_value=requests_tuple(':{"assertion":"content"}'),
)
async def testlog_in(post_mock):
    player = PSClientChild(
        account_configuration=account_configuration,
        avatar=12,
        server_configuration=server_configuration,
        log_level=38,
        start_listening=False,
    )

    player.send_message = AsyncMock()
    player.change_avatar = AsyncMock()

    await player.log_in(["A", "B", "C", "D"])

    player.change_avatar.assert_called_once_with(12)
    player.send_message.assert_called_once_with("/trn username,0,content")
    post_mock.assert_called_once()


@pytest.mark.asyncio
async def test_change_avatar():
    player = PSClientChild(
        account_configuration=account_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )

    player.send_message = AsyncMock()
    player._logged_in.set()

    await player.change_avatar(8)

    player.send_message.assert_called_once_with("/avatar 8")


@pytest.mark.asyncio
async def test_handle_message():
    player = PSClientChild(
        account_configuration=account_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )
    player.log_in = AsyncMock()

    await player._handle_message("|challstr")
    player.log_in.assert_called_once()

    assert player.logged_in.is_set() is False
    await player._handle_message("|updateuser| username")
    assert player._logged_in.is_set() is True

    player._update_challenges = AsyncMock()
    await player._handle_message("|updatechallenges")
    player._update_challenges.assert_called_once_with(["", "updatechallenges"])

    player._handle_battle_message = AsyncMock()
    await player._handle_message(">battle|thing")
    player._handle_battle_message.assert_called_once_with([[">battle", "thing"]])

    await player._handle_message("|updatesearch")

    player._logger.warning = AsyncMock()
    await player._handle_message("that was unexpected!|")
    player._logger.warning.assert_called_once_with(
        "Unhandled message: %s", "that was unexpected!|"
    )


@pytest.mark.asyncio
async def test_listen():
    player = PSClientChild(
        account_configuration=account_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )

    type(player).websocket_url = PropertyMock(return_value="ws://localhost:8899")

    player._handle_message = AsyncMock()
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
async def testsend_message():
    player = PSClientChild(
        account_configuration=account_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )
    player._websocket = AsyncMock()
    player._websocket.send = AsyncMock()

    await player.send_message("hey", "home")
    player._websocket.send.assert_called_once_with("home|hey")

    await player.send_message("hey", "home", "hey again")
    player._websocket.send.assert_called_with("home|hey|hey again")
