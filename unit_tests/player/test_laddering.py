import asyncio
from unittest.mock import patch

import pytest

from poke_env.player import RandomPlayer


@patch("poke_env.ps_client.ps_client.PSClient.send_message")
@pytest.mark.asyncio
async def test_laddering_sequential(send_message_mock):
    async def send_message(self, *args, **kwargs):
        if tuple(send_message_mock.call_args) == (("/utm null",), {}):
            return

        interactions.append("Search start")
        asyncio.ensure_future(start_battle())

    async def start_battle():
        await asyncio.sleep(0.01)
        interactions.append(f"Battle {player.count} start")
        await player.ps_client._handle_message(
            f">battle-gen9randombattle-{player.count}\n|init|battle"
        )
        asyncio.ensure_future(end_battle(player.count))
        player.count += 1

    async def end_battle(count):
        await asyncio.sleep(0.01)
        interactions.append(f"Battle {count} end")
        await player.ps_client._handle_message(
            f">battle-gen9randombattle-{count}\n|win|{player.username}"
        )

    player = RandomPlayer(start_listening=False)
    player.count = 0
    send_message_mock.side_effect = send_message
    player.ps_client.logged_in.set()

    interactions = []
    await asyncio.wait_for(player.ladder(5), timeout=3)

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


@patch("poke_env.ps_client.ps_client.PSClient.send_message")
@pytest.mark.asyncio
async def test_laddering_parallel(send_message_mock):
    async def send_message(self, *args, **kwargs):
        if tuple(send_message_mock.call_args) == (("/utm null",), {}):
            return

        interactions.append("Search start")
        asyncio.ensure_future(start_battle())

    async def start_battle():
        interactions.append(f"Battle {player.count} start")
        await player.ps_client._handle_message(
            f">battle-gen9randombattle-{player.count}\n|init|battle"
        )
        asyncio.ensure_future(end_battle(player.count))
        player.count += 1

    async def end_battle(count):
        await asyncio.sleep(0.05)
        interactions.append(f"Battle {count} end")
        await player.ps_client._handle_message(
            f">battle-gen9randombattle-{count}\n|win|{player.username}"
        )

    player = RandomPlayer(start_listening=False, max_concurrent_battles=3)
    player.count = 0
    send_message_mock.side_effect = send_message
    player.ps_client.logged_in.set()

    interactions = []

    await asyncio.wait_for(asyncio.gather(player.ladder(5)), timeout=1)

    assert set(interactions) == {
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
    }

    for i in range(3):
        assert interactions[2 * i] == "Search start"
        assert interactions[2 * i + 1] == "Battle %d start" % i
