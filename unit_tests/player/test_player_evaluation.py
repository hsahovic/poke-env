# -*- coding: utf-8 -*-
from poke_env.player.random_player import RandomPlayer
from poke_env.player.utils import evaluate_player, _estimate_strength_from_results

import math
import pytest


def test_estimate_strength_from_results():
    # Test extreme values with decent number of games
    with pytest.raises(ValueError):
        _estimate_strength_from_results(1000, 1, 1)

    with pytest.raises(ValueError):
        _estimate_strength_from_results(1000, 999, 1)

    # Test too few games
    with pytest.raises(ValueError):
        _estimate_strength_from_results(5, 2, 1)
    # Test too few games
    with pytest.raises(ValueError):
        _estimate_strength_from_results(10, 3, 1)

    # Test estimate values
    for n_games, n_victories, expected_value in (
        (100, 50, 1),
        (999, 333, 0.5),
        (999, 666, 2),
        (250, 150, 1.5),
    ):
        assert (
            abs(
                _estimate_strength_from_results(n_games, n_victories, 1)[0]
                - expected_value
            )
            < 10e-10
        )

    eis = []
    cis = []
    for n_games in [10 ** i for i in range(2, 10)]:
        ei, ci = _estimate_strength_from_results(n_games, n_games // 2 + 2, 1)
        eis.append(ei)
        cis.append(ci)

        assert (
            abs(
                ei * 2
                - _estimate_strength_from_results(n_games, n_games // 2 + 2, 2)[0]
            )
            < 10e-10
        )
        assert (
            abs(
                ei * 5
                - _estimate_strength_from_results(n_games, n_games // 2 + 2, 5)[0]
            )
            < 10e-10
        )

    for i, ci in enumerate(cis):
        assert ci[0] < eis[i] < ci[1]
        if i:
            assert ci[0] > cis[i - 1][0]
            assert ci[1] < cis[i - 1][1]

    assert _estimate_strength_from_results(95, 43, 1) == (
        0.8269230769230771,
        (0.5444919968130197, 1.2357621837082962),
    )

    assert _estimate_strength_from_results(10 ** 17, 10 ** 17 - 10, 1)[1][1] == math.inf


@pytest.mark.asyncio
async def test_player_evaluation_assertions():
    p = RandomPlayer(battle_format="gen8ou", start_listening=False)
    with pytest.raises(AssertionError):
        await evaluate_player(p)

    p = RandomPlayer(start_listening=False)
    with pytest.raises(AssertionError):
        await evaluate_player(p, n_battles=0)

    with pytest.raises(AssertionError):
        await evaluate_player(p, n_battles=-10)

    with pytest.raises(AssertionError):
        await evaluate_player(p, n_placement_battles=0)

    with pytest.raises(AssertionError):
        await evaluate_player(p, n_placement_battles=-10)
