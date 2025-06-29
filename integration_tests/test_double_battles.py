import asyncio

import pytest

from poke_env.player import RandomPlayer, cross_evaluate
from poke_env.ps_client import AccountConfiguration, LocalhostServerConfiguration


async def simple_cross_evaluation(n_battles, format_, i=0):
    player_1_configuration = AccountConfiguration("Player %d" % (i + 1), None)
    player_2_configuration = AccountConfiguration("Player %d" % (i + 2), None)
    player_3_configuration = AccountConfiguration("Player %d" % (i + 3), None)
    players = [
        RandomPlayer(
            account_configuration=player_config,
            battle_format=format_,
            server_configuration=LocalhostServerConfiguration,
            max_concurrent_battles=n_battles,
        )
        for player_config in [
            player_1_configuration,
            player_2_configuration,
            player_3_configuration,
        ]
    ]
    await cross_evaluate(players, n_challenges=n_battles)

    for player in players:
        player.reset_battles()
        await player.ps_client.stop_listening()


@pytest.mark.asyncio
async def test_small_cross_evaluation_gen8():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen8randomdoublesbattle", i=3), timeout=20
    )
