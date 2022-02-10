# -*- coding: utf-8 -*-
import asyncio
import pytest
import time

from poke_env.player.random_player import RandomPlayer


async def simple_laddering(n_battles, max_concurrent_battles):
    players = [
        RandomPlayer(max_concurrent_battles=max_concurrent_battles, log_level=20),
        RandomPlayer(max_concurrent_battles=max_concurrent_battles, log_level=20),
    ]

    await asyncio.gather(players[0].ladder(n_battles), players[1].ladder(n_battles))

    for player in players:
        await player.stop_listening()


@pytest.mark.asyncio
async def test_laddering():
    for n_battles in [2, 6]:
        start_sequential_battle = time.time()
        await asyncio.wait_for(simple_laddering(n_battles, 1), None)
        end_sequential_battle = time.time()
        sequential_duration = end_sequential_battle - start_sequential_battle
        start_parallel_battle = time.time()
        await asyncio.wait_for(simple_laddering(n_battles, n_battles), None)
        end_parallel_battle = time.time()
        parallel_duration = end_parallel_battle - start_parallel_battle

        assert parallel_duration < sequential_duration
