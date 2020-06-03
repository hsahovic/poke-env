# -*- coding: utf-8 -*-
import asyncio
import pytest

from poke_env.player.baselines import SimpleHeuristicsPlayer
from poke_env.player.utils import cross_evaluate


async def cross_evaluation(n_battles, format_, teams):
    players = [
        SimpleHeuristicsPlayer(
            battle_format=format_, max_concurrent_battles=n_battles, team=team
        )
        for i, team in enumerate(teams)
    ]
    await cross_evaluate(players, n_challenges=n_battles)

    for player in players:
        await player.stop_listening()


@pytest.mark.asyncio
async def test_all_formats_cross_evaluation(showdown_format_teams):
    coroutines = [
        asyncio.wait_for(
            cross_evaluation(n_battles=5, format_=format_, teams=teams),
            timeout=3 * (len(teams) ** 2) + 3,
        )
        for format_, teams in showdown_format_teams.items()
    ]
    await asyncio.gather(*coroutines)
