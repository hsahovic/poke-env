# -*- coding: utf-8 -*-
import asyncio
import pytest

from poke_env.player.random_player import RandomPlayer


async def simple_laddering(n_battles, max_concurrent_battles):
    players = [
        RandomPlayer(max_concurrent_battles=max_concurrent_battles, log_level=20),
        RandomPlayer(max_concurrent_battles=max_concurrent_battles, log_level=20),
    ]

    await asyncio.gather(players[0].ladder(n_battles), players[1].ladder(n_battles))

    for player in players:
        player.reset_battles()
        await player.stop_listening()


@pytest.mark.asyncio
async def test_laddering():
    for n_battles in [1, 5]:
        await asyncio.wait_for(
            simple_laddering(n_battles, 1), timeout=5 * n_battles + 5
        )
        await asyncio.wait_for(
            simple_laddering(n_battles, n_battles), timeout=5 * n_battles
        )
