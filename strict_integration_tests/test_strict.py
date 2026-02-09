import asyncio

import pytest

from poke_env.player import ForfeitBattleOrder, RandomPlayer, cross_evaluate


class ZoroarkForfeitRandomPlayer(RandomPlayer):
    def choose_move(self, battle):
        if "illusion" in [p.ability for p in battle.team.values()]:
            return ForfeitBattleOrder()
        return super().choose_move(battle)


async def simple_cross_evaluation(n_battles, players):
    await cross_evaluate(players, n_challenges=n_battles)

    for player in players:
        player.reset_battles()
        await player.ps_client.stop_listening()


@pytest.mark.asyncio
async def test_random_players():
    for gen in range(1, 10):
        players = [
            ZoroarkForfeitRandomPlayer(
                battle_format=f"gen{gen}randombattle",
                max_concurrent_battles=10,
                strict_battle_tracking=True,
            ),
            ZoroarkForfeitRandomPlayer(
                battle_format=f"gen{gen}randombattle",
                max_concurrent_battles=10,
                strict_battle_tracking=True,
            ),
        ]
        await asyncio.wait_for(
            simple_cross_evaluation(100, players=players), timeout=100
        )


@pytest.mark.asyncio
async def test_random_double_players():
    players = [
        ZoroarkForfeitRandomPlayer(
            battle_format=f"gen9randomdoublesbattle",
            max_concurrent_battles=10,
            strict_battle_tracking=True,
        ),
        ZoroarkForfeitRandomPlayer(
            battle_format=f"gen9randomdoublesbattle",
            max_concurrent_battles=10,
            strict_battle_tracking=True,
        ),
    ]
    await asyncio.wait_for(
        simple_cross_evaluation(100, players=players), timeout=100
    )
