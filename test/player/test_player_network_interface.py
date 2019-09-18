# -*- coding: utf-8 -*-

import asyncio
import logging

from collections import namedtuple
from mock import MagicMock
from mock import patch
from pokemon_showdown_env.player.player_network_interface import PlayerNetwork


# This hack comes from
# https://stackoverflow.com/questions/51394411/python-object-magicmock-cant-be-used-in-await-expression
async def async_magic():
    pass


MagicMock.__await__ = lambda x: async_magic().__await__()


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


@patch(
    "pokemon_showdown_env.player.player_network_interface.requests.post",
    return_value=requests_tuple(':{"assertion":"content"}'),
)
def test_log_in(post_mock):
    player = PlayerNetworkChild(
        "username",
        "password",
        avatar=12,
        authentication_url="auth.url",
        server_url="server.url",
        log_level=38,
    )

    player.send_message = MagicMock()
    player.change_avatar = MagicMock()

    asyncio.run(player._log_in(["A", "B", "C", "D"]))

    player.change_avatar.assert_called_once_with(12)
    player.send_message.assert_called_once_with("/trn username,0,content")
    post_mock.assert_called_once()


def test_change_avatar():
    pass


def test_handle_message():
    pass


def test_listen():
    pass


def test_send_message():
    pass
