from poke_env.player import Player, RandomPlayer
from poke_env.ps_client.account_configuration import CONFIGURATION_FROM_PLAYER_COUNTER


class CustomPlayer(Player):
    def choose_move(self, battle):
        return self.choose_random_move(battle)


def test_default_player_configuration():
    CONFIGURATION_FROM_PLAYER_COUNTER.clear()

    usernames = set()

    for k in range(5):
        for C in [CustomPlayer, RandomPlayer]:
            instance = C()
            username = instance.username
            assert username not in usernames
            usernames.add(username)

            assert username
            assert isinstance(username, str)

            assert instance.ps_client.account_configuration.password is None


def test_default_server_configuration():
    for k in range(5):
        for C in [CustomPlayer, RandomPlayer]:
            instance = C()
            url = instance.ps_client.websocket_url

            assert url
            assert isinstance(url, str)
            assert "localhost" in url or "127.0.0.1" in url
