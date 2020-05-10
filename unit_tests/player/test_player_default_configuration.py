# -*- coding: utf-8 -*-

from poke_env.player.random_player import RandomPlayer
from poke_env.player.player import Player
from poke_env.player_configuration import _CONFIGURATION_FROM_PLAYER_COUNTER


class CustomPlayer(Player):
    def choose_move(self, battle):
        return self.choose_random_move(battle)


def test_default_player_configuration():
    _CONFIGURATION_FROM_PLAYER_COUNTER.clear()

    usernames = set()

    for k in range(5):
        for C in [CustomPlayer, RandomPlayer]:
            instance = C()
            username = instance.username
            assert username not in usernames
            usernames.add(username)

            assert username
            assert isinstance(username, str)

            assert instance._password is None


def test_default_server_configuration():
    for k in range(5):
        for C in [CustomPlayer, RandomPlayer]:
            instance = C()
            url = instance.websocket_url

            assert url
            assert isinstance(url, str)
            assert "localhost" in url or "127.0.0.1" in url
