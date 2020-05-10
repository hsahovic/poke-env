# -*- coding: utf-8 -*-
import asyncio

from poke_env.player.random_player import RandomPlayer
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import ShowdownServerConfiguration


async def main():
    # We create a random player
    player = RandomPlayer(
        player_configuration=PlayerConfiguration("bot_username", "bot_password"),
        server_configuration=ShowdownServerConfiguration,
    )
    await player.send_challenges("your_username", n_challenges=1)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
