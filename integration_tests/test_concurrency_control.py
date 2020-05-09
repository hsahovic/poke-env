# -*- coding: utf-8 -*-
"""
These tests aim to verify that concurrency control is working properly.
"""
import asyncio
import pytest

from poke_env.player.random_player import RandomPlayer
from poke_env.player.utils import cross_evaluate
from poke_env.player_configuration import PlayerConfiguration
from poke_env.server_configuration import LocalhostServerConfiguration


class MoveCallTrackingRandomPlayer(RandomPlayer):
    def choose_move(self, battle):
        try:
            self.move_history.append(battle.battle_tag)
        except AttributeError:
            self.move_history = [battle.battle_tag]
        return super(MoveCallTrackingRandomPlayer, self).choose_move(battle)


async def simple_cross_evaluation(n_battles, n_concurrent_battles):
    player_1_configuration = PlayerConfiguration("Player 1", None)
    player_2_configuration = PlayerConfiguration("Player 2", None)
    players = [
        RandomPlayer(
            player_configuration=player_1_configuration,
            battle_format="gen7randombattle",
            server_configuration=LocalhostServerConfiguration,
            max_concurrent_battles=n_concurrent_battles,
        ),
        MoveCallTrackingRandomPlayer(
            player_configuration=player_2_configuration,
            battle_format="gen7randombattle",
            server_configuration=LocalhostServerConfiguration,
            max_concurrent_battles=n_concurrent_battles,
        ),
    ]
    await cross_evaluate(players, n_challenges=n_battles)

    for player in players:
        await player.stop_listening()

    return players[-1].move_history


@pytest.mark.asyncio
async def test_max_concurrent_battle_works():
    for max_battles in [1, 3, 5]:
        result = await asyncio.wait_for(
            simple_cross_evaluation(7 * max_battles, max_battles),
            timeout=5 * max_battles + 5,
        )

        times_per_battle = {}
        for i, val in enumerate(result):
            if val not in times_per_battle:
                times_per_battle[val] = []
            times_per_battle[val].append(i)

        start_end = [(values[0], values[-1]) for values in times_per_battle.values()]
        max_concurrent_battles = 0

        for i, val in enumerate(result):
            current_battles = 0
            for start, end in start_end:
                if start <= i <= end:
                    current_battles += 1
            max_concurrent_battles = max(max_concurrent_battles, current_battles)

        assert max_concurrent_battles == max_battles
