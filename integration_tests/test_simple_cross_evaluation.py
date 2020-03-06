# -*- coding: utf-8 -*-
import asyncio
import pytest

from poke_env.player.random_player import RandomPlayer
from poke_env.player.utils import cross_evaluate
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import LocalhostServerConfiguration


async def simple_cross_evaluation(n_battles):
    player_1_configuration = PlayerConfiguration("Player 1", None)
    player_2_configuration = PlayerConfiguration("Player 2", None)
    player_3_configuration = PlayerConfiguration("Player 3", None)
    players = [
        RandomPlayer(
            player_configuration=player_config,
            battle_format="gen7randombattle",
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
        await player.stop_listening()


@pytest.mark.asyncio
async def test_small_cross_evaluation():
    await asyncio.wait_for(simple_cross_evaluation(5), timeout=10)
