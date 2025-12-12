import asyncio

import pytest

from poke_env.player import RandomPlayer, cross_evaluate


async def simple_cross_evaluation(n_battles, players):
    await cross_evaluate(players, n_challenges=n_battles)

    for player in players:
        player.reset_battles()
        await player.ps_client.stop_listening()


@pytest.mark.asyncio
async def test_random_players():
    for gen in range(4, 10):
        players = [
            RandomPlayer(
                battle_format=f"gen{gen}randombattle", strict_battle_tracking=True
            ),
            RandomPlayer(
                battle_format=f"gen{gen}randombattle", strict_battle_tracking=True
            ),
        ]
        await asyncio.wait_for(
            simple_cross_evaluation(100, players=players), timeout=60
        )
