# -*- coding: utf-8 -*-
from poke_env.player.random_player import RandomPlayer
from poke_env.player.utils import cross_evaluate
import asyncio
import orjson

msgs = []


class StoragePlayer(RandomPlayer):
    async def _handle_message(self, message):
        rtn = await RandomPlayer._handle_message(self, message)
        msgs.append(message)
        return rtn


players = [RandomPlayer(), StoragePlayer()]

asyncio.get_event_loop().run_until_complete(cross_evaluate(players, n_challenges=100))

with open("msgs.json", "wb+") as f:
    f.write(orjson.dumps(msgs))
