# -*- coding: utf-8 -*-
import asyncio
import pytest

from poke_env.player.random_player import RandomPlayer


async def simple_ladderring(n_battles, max_concurrent_battles):
    players = [
        RandomPlayer(max_concurrent_battles=max_concurrent_battles, log_level=20),
        RandomPlayer(max_concurrent_battles=max_concurrent_battles, log_level=20),
    ]

    await asyncio.gather(players[0].ladder(n_battles), players[1].ladder(n_battles))

    for player in players:
        await player.stop_listening()


@pytest.mark.flaky(reruns=3, reruns_delay=1)
@pytest.mark.asyncio
async def test_laddering():
    for n_battles in [1, 5]:
        await asyncio.wait_for(simple_ladderring(n_battles, 1), timeout=n_battles + 5)
        await asyncio.wait_for(
            simple_ladderring(n_battles, n_battles), timeout=n_battles
        )
