import asyncio

import pytest

from poke_env.player import (
    MaxBasePowerPlayer,
    RandomPlayer,
    SimpleHeuristicsPlayer,
    cross_evaluate,
)


async def simple_cross_evaluation(n_battles, players):
    await cross_evaluate(players, n_challenges=n_battles)

    for player in players:
        player.reset_battles()
        await player.ps_client.stop_listening()


@pytest.mark.asyncio
async def test_random_players():
    players = [RandomPlayer(strict=True), RandomPlayer(strict=True)]
    await asyncio.wait_for(
        simple_cross_evaluation(5, players=players),
        timeout=5,
    )


@pytest.mark.asyncio
async def test_random_players_in_doubles():
    players = [
        RandomPlayer(battle_format="gen9randomdoublesbattle", strict=True),
        RandomPlayer(battle_format="gen9randomdoublesbattle", strict=True),
    ]
    await asyncio.wait_for(simple_cross_evaluation(5, players=players), timeout=5)


@pytest.mark.asyncio
async def test_shp():
    players = [RandomPlayer(strict=True), SimpleHeuristicsPlayer(strict=True)]
    await asyncio.wait_for(simple_cross_evaluation(5, players=players), timeout=5)


@pytest.mark.asyncio
async def test_shp_in_doubles():
    players = [
        RandomPlayer(battle_format="gen9randomdoublesbattle", strict=True),
        SimpleHeuristicsPlayer(battle_format="gen9randomdoublesbattle", strict=True),
    ]
    await asyncio.wait_for(simple_cross_evaluation(5, players=players), timeout=5)


@pytest.mark.asyncio
async def test_max_base_power():
    players = [RandomPlayer(strict=True), MaxBasePowerPlayer(strict=True)]
    await asyncio.wait_for(simple_cross_evaluation(5, players=players), timeout=5)


@pytest.mark.asyncio
async def test_max_base_power_in_doubles():
    players = [
        RandomPlayer(battle_format="gen9randomdoublesbattle", strict=True),
        MaxBasePowerPlayer(battle_format="gen9randomdoublesbattle", strict=True),
    ]
    await asyncio.wait_for(simple_cross_evaluation(5, players=players), timeout=5)
