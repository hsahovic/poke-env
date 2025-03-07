import asyncio

import pytest

from poke_env.player import SimpleHeuristicsPlayer, cross_evaluate


async def cross_evaluation(n_battles, format_, teams):
    if len(teams) > 1:
        players = [
            SimpleHeuristicsPlayer(
                battle_format=format_,
                max_concurrent_battles=n_battles,
                team=team,
                log_level=25,
            )
            for team in teams
        ]
    else:
        assert len(teams) == 1
        players = [
            SimpleHeuristicsPlayer(
                battle_format=format_,
                max_concurrent_battles=n_battles,
                team=teams[0],
                log_level=25,
            )
            for _ in range(2)
        ]
    await cross_evaluate(players, n_challenges=n_battles)

    for player in players:
        player.reset_battles()
        await player.ps_client.stop_listening()


@pytest.mark.asyncio
async def test_all_formats_cross_evaluation(showdown_format_teams):
    for format_, teams in showdown_format_teams.items():
        await asyncio.wait_for(
            cross_evaluation(n_battles=5, format_=format_, teams=teams),
            timeout=len(teams) * len(teams) + 1,
        )
