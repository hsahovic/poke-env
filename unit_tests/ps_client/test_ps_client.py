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
server_configuration = ServerConfiguration(
    "ws://server.url/showdown/websocket", "auth.url"
)


def test_init_and_properties():
    client = PSClient(
        account_configuration=account_configuration,
        server_configuration=server_configuration,
        start_listening=False,
    )

    assert client.username == "username"
    assert client.websocket_url == "ws://server.url/showdown/websocket"


def test_create_logger():
    client = PSClient(
        account_configuration=account_configuration,
        server_configuration=server_configuration,
        start_listening=False,
        log_level=38,
    )

    assert isinstance(client._logger, logging.Logger)
    assert client._logger.getEffectiveLevel() == 38

    logger = client._create_logger(24)

    assert isinstance(logger, logging.Logger)
    assert logger.getEffectiveLevel() == 24


@pytest.mark.asyncio
@patch(
    "poke_env.ps_client.ps_client.requests.post",
    return_value=requests_tuple(':{"assertion":"content"}'),
)
async def testlog_in(post_mock):
    client = PSClient(
        account_configuration=account_configuration,
        avatar=12,
        server_configuration=server_configuration,
        log_level=38,
        start_listening=False,
    )

    client.send_message = AsyncMock()
    client.change_avatar = AsyncMock()

    await client.log_in(["A", "B", "C", "D"])

    client.change_avatar.assert_called_once_with(12)
    client.send_message.assert_called_once_with("/trn username,0,content")
    post_mock.assert_called_once()


@pytest.mark.asyncio
async def test_change_avatar():
    client = PSClient(
        account_configuration=account_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )

    client.send_message = AsyncMock()
    client._logged_in.set()

    await client.change_avatar(8)

    client.send_message.assert_called_once_with("/avatar 8")


@pytest.mark.asyncio
async def test_handle_message():
    client = PSClient(
        account_configuration=account_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )
    client.log_in = AsyncMock()

    await client._handle_message("|challstr")
    client.log_in.assert_called_once()

    assert client.logged_in.is_set() is False
    await client._handle_message("|updateuser| username")
    assert client._logged_in.is_set() is True

    client._update_challenges = AsyncMock()
    await client._handle_message("|updatechallenges")
    client._update_challenges.assert_called_once_with(["", "updatechallenges"])

    client._handle_battle_message = AsyncMock()
    await client._handle_message(">battle\n|request|request-thing")
    await client._handle_message(">battle\n|turn|15")
    client._handle_battle_message.assert_called_once_with(
        [[">battle"], ["", "turn", "15"], ["", "request", "request-thing"]]
    )

    await client._handle_message("|updatesearch")

    client._logger.warning = AsyncMock()
    await client._handle_message("that was unexpected!|")
    client._logger.warning.assert_called_once_with(
        "Unhandled message: %s", "that was unexpected!|"
    )


@patch("poke_env.ps_client.ps_client.PSClient._handle_message")
@pytest.mark.asyncio
async def test_listen(handle_message_mock):
    client = PSClient(
        account_configuration=account_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )

    websocket_url_as_mock = PropertyMock(return_value="ws://localhost:8899")
    PSClient.websocket_url = websocket_url_as_mock

    semaphore = asyncio.Semaphore()

    async def showdown_server_mock(websocket, path):
        semaphore.release()
        await websocket.ping()
        await websocket.send("error|test 1")
        await websocket.send("error|test 2")
        await websocket.send("error|test 3")

    await semaphore.acquire()

    gathered = asyncio.gather(websockets.serve(showdown_server_mock, "0.0.0.0", 8899))

    await client.listen()

    await gathered
    assert handle_message_mock.await_count == 3
    handle_message_mock.assert_awaited_with("error|test 3")


@pytest.mark.asyncio
async def test_send_message():
    client = PSClient(
        account_configuration=account_configuration,
        avatar=12,
        server_configuration=server_configuration,
        start_listening=False,
    )
    client.websocket = AsyncMock()
    client.websocket.send = AsyncMock()

    await client.send_message("hey", "home")

    client.websocket.send.assert_called_once_with("home|hey")

    await client.send_message("hey", "home", "hey again")
    client.websocket.send.assert_called_with("home|hey|hey again")
