import asyncio

import pytest

from poke_env.player import ForfeitBattleOrder, RandomPlayer, cross_evaluate


class ZoroarkForfeitRandomPlayer(RandomPlayer):
    def choose_move(self, battle):
        if "illusion" in [p.ability for p in battle.team.values()]:
            return ForfeitBattleOrder()
        return super().choose_move(battle)


@pytest.mark.asyncio
@pytest.mark.timeout(130)
@pytest.mark.parametrize(
    "battle_format",
    [f"gen{gen}randombattle" for gen in range(1, 10)] + ["gen9randomdoublesbattle"],
)
async def test_random_players(battle_format):
    players = [
        ZoroarkForfeitRandomPlayer(
            battle_format=battle_format,
            max_concurrent_battles=10,
            strict_battle_tracking=True,
        )
        for _ in range(2)
    ]
    try:
        await asyncio.wait_for(cross_evaluate(players, n_challenges=100), timeout=100)
    finally:
        await asyncio.wait_for(
            asyncio.gather(*(player.ps_client.stop_listening() for player in players)),
            timeout=10,
        )
