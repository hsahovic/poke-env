# -*- coding: utf-8 -*-

import asyncio
import pytest

from poke_env.player.random_player import RandomPlayer


@pytest.mark.asyncio
async def test_laddering_sequential():
    async def send_message(self, *args, **kwargs):
        interactions.append("Search start")
        asyncio.ensure_future(start_battle())

    async def start_battle():
        interactions.append(f"Battle {player.count} start")
        await player._handle_message(
            f">battle-gen8randombattle-{player.count}\n|init|battle"
        )
        asyncio.ensure_future(end_battle(player.count))
        player.count += 1

    async def end_battle(count):
        await asyncio.sleep(0.01)
        interactions.append(f"Battle {count} end")
        await player._handle_message(
            f">battle-gen8randombattle-{count}\n|win|{player.username}"
        )

    player = RandomPlayer(start_listening=False)
    player.count = 0
    type(player)._send_message = send_message
    player.logged_in.set()

    interactions = []

    await asyncio.wait_for(asyncio.gather(player.ladder(5)), timeout=1)

    assert interactions == [
        "Search start",
        "Battle 0 start",
        "Battle 0 end",
        "Search start",
        "Battle 1 start",
        "Battle 1 end",
        "Search start",
        "Battle 2 start",
        "Battle 2 end",
        "Search start",
        "Battle 3 start",
        "Battle 3 end",
        "Search start",
        "Battle 4 start",
        "Battle 4 end",
    ]


@pytest.mark.asyncio
async def test_laddering_parallel():
    async def send_message(self, *args, **kwargs):
        interactions.append("Search start")
        asyncio.ensure_future(start_battle())

    async def start_battle():
        interactions.append(f"Battle {player.count} start")
        await player._handle_message(
            f">battle-gen8randombattle-{player.count}\n|init|battle"
        )
        asyncio.ensure_future(end_battle(player.count))
        player.count += 1

    async def end_battle(count):
        await asyncio.sleep(0.01)
        interactions.append(f"Battle {count} end")
        await player._handle_message(
            f">battle-gen8randombattle-{count}\n|win|{player.username}"
        )

    player = RandomPlayer(start_listening=False, max_concurrent_battles=3)
    player.count = 0
    type(player)._send_message = send_message
    player.logged_in.set()

    interactions = []

    await asyncio.wait_for(asyncio.gather(player.ladder(5)), timeout=1)

    assert set(interactions) == set(
        [
            "Search start",
            "Battle 0 start",
            "Search start",
            "Battle 1 start",
            "Search start",
            "Battle 2 start",
            "Battle 0 end",
            "Battle 1 end",
            "Battle 2 end",
            "Search start",
            "Battle 3 start",
            "Search start",
            "Battle 4 start",
            "Battle 3 end",
            "Battle 4 end",
        ]
    )
    for i in range(3):
        assert interactions[2 * i] == "Search start"
        assert interactions[2 * i + 1] == "Battle %d start" % i
