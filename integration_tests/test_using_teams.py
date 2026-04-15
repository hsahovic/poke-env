import asyncio

import pytest

from poke_env.player import (
    ForfeitBattleOrder,
    RandomPlayer,
    SimpleHeuristicsPlayer,
    cross_evaluate,
)
from poke_env.ps_client import AccountConfiguration, LocalhostServerConfiguration


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
        if "bo3" in format_:
            continue  # bo3 formats tested separately below
        await asyncio.wait_for(
            cross_evaluation(n_battles=5, format_=format_, teams=teams),
            timeout=len(teams) * len(teams) + 1,
        )


class RandomVGCPlayer(RandomPlayer):
    def choose_move(self, battle):
        if battle.turn > 50:
            return ForfeitBattleOrder()
        return self.choose_random_move(battle)


@pytest.mark.asyncio
async def test_bo3_cross_evaluation(showdown_format_teams):
    for format_, teams in showdown_format_teams.items():
        if "bo3" not in format_:
            continue
        players = [
            RandomVGCPlayer(
                battle_format=format_, max_concurrent_battles=1, team=team, log_level=25
            )
            for team in teams
        ]
        await asyncio.wait_for(cross_evaluate(players, n_challenges=1), timeout=120)
        for player in players:
            await player.ps_client.stop_listening()


@pytest.mark.asyncio
async def test_bo3_concurrent(showdown_format_teams):
    for format_, teams in showdown_format_teams.items():
        if "bo3" not in format_:
            continue
        p1 = RandomVGCPlayer(
            account_configuration=AccountConfiguration("ConcBo3T 1", None),
            battle_format=format_,
            server_configuration=LocalhostServerConfiguration,
            max_concurrent_battles=3,
            team=teams[0],
            log_level=25,
        )
        p2 = RandomVGCPlayer(
            account_configuration=AccountConfiguration("ConcBo3T 2", None),
            battle_format=format_,
            server_configuration=LocalhostServerConfiguration,
            max_concurrent_battles=3,
            team=teams[-1],
            log_level=25,
        )
        await asyncio.wait_for(p1.battle_against(p2, n_battles=3), timeout=180)
        assert p1.n_finished_battles >= 6
        assert p2.n_finished_battles >= 6
        assert all(g["finished"] for g in p1._bestof_games.values())
        p1.reset_battles()
        p2.reset_battles()
        await p1.ps_client.stop_listening()
        await p2.ps_client.stop_listening()
