import pytest

from poke_env.player import RandomPlayer, cross_evaluate
from poke_env.ps_client import LocalhostServerConfiguration


@pytest.mark.asyncio
async def test_avatar():
    players = [
        RandomPlayer(
            server_configuration=LocalhostServerConfiguration,
            max_concurrent_battles=1,
            log_level=25,
            avatar="dragontamer",
        )
        for _ in range(2)
    ]
    await cross_evaluate(players, n_challenges=1)


@pytest.mark.asyncio
async def test_timer():
    players = [
        RandomPlayer(
            server_configuration=LocalhostServerConfiguration,
            max_concurrent_battles=1,
            log_level=25,
            start_timer_on_battle_start=True,
        )
        for _ in range(2)
    ]
    await cross_evaluate(players, n_challenges=1)
