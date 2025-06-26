import asyncio

import pytest

from poke_env.player import ForfeitBattleOrder, RandomPlayer, cross_evaluate
from poke_env.ps_client import LocalhostServerConfiguration


class RandomPlayerThatForfeitsAfter100Turns(RandomPlayer):
    def choose_move(self, battle):
        if battle.turn > 100:
            return ForfeitBattleOrder()
        return super().choose_move(battle)


async def simple_cross_evaluation(n_battles, format_):
    players = [
        RandomPlayerThatForfeitsAfter100Turns(
            battle_format=format_,
            server_configuration=LocalhostServerConfiguration,
            max_concurrent_battles=n_battles,
            log_level=25,
        )
        for _ in range(3)
    ]
    await cross_evaluate(players, n_challenges=n_battles)

    for player in players:
        player.reset_battles()
        await player.ps_client.stop_listening()


@pytest.mark.asyncio
async def test_small_cross_evaluation_gen9():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen9randombattle"), timeout=20
    )


@pytest.mark.asyncio
async def test_small_cross_evaluation_gen8():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen8randombattle"), timeout=20
    )


@pytest.mark.asyncio
async def test_small_cross_evaluation_gen7():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen7randombattle"), timeout=20
    )


@pytest.mark.asyncio
async def test_small_cross_evaluation_gen6():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen6randombattle"), timeout=20
    )


@pytest.mark.asyncio
async def test_small_cross_evaluation_gen5():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen5randombattle"), timeout=20
    )


@pytest.mark.asyncio
async def test_small_cross_evaluation_gen4():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen4randombattle"), timeout=20
    )


@pytest.mark.asyncio
async def test_small_cross_evaluation_gen3():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen3randombattle"), timeout=20
    )


@pytest.mark.asyncio
async def test_small_cross_evaluation_gen2():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen2randombattle"), timeout=20
    )


@pytest.mark.asyncio
async def test_small_cross_evaluation_gen1():
    await asyncio.wait_for(
        simple_cross_evaluation(5, format_="gen1randombattle"), timeout=20
    )
