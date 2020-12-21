# -*- coding: utf-8 -*-
import asyncio
import pytest

from poke_env.player.random_player import RandomPlayer
from poke_env.player.utils import cross_evaluate
from poke_env.server_configuration import LocalhostServerConfiguration


async def simple_cross_evaluation(n_battles, format_):
    players = [
        RandomPlayer(
            battle_format=format_,
            server_configuration=LocalhostServerConfiguration,
            max_concurrent_battles=n_battles,
            log_level=20,
        )
        for _ in range(3)
    ]
    await cross_evaluate(players, n_challenges=n_battles)

    for player in players:
        await player.stop_listening()


@pytest.mark.asyncio
async def test_small_cross_evaluation():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen8randombattle"), timeout=10
    )
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen7randombattle"), timeout=10
    )
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen6randombattle"), timeout=10
    )
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen5randombattle"), timeout=10
    )
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen4randombattle"), timeout=10
    )
