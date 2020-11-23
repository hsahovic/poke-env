# -*- coding: utf-8 -*-
from poke_env.player.random_player import RandomPlayer
from poke_env.player_configuration import PlayerConfiguration
import asyncio
import json

with open("msgs.json", "r") as f:
    msgs = json.load(f)


class FakePlayer(RandomPlayer):
    async def _send_message(self, *args, **kwargs):
        pass


p = FakePlayer(
    start_listening=False,
    player_configuration=PlayerConfiguration("StoragePlayer 1", None),
)
p._logged_in.set()


async def main():
    for msg in msgs:
        await p._handle_message(msg)


asyncio.get_event_loop().run_until_complete(main())

# from poke_env.player.player import c
# print(c)
