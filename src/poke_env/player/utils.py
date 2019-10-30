# -*- coding: utf-8 -*-
"""This module contains utility functions and objects related to Player classes.
"""

from poke_env.player.player import Player
from poke_env.utils import to_id_str
from typing import Dict
from typing import List
from typing import Optional

import asyncio


async def cross_evaluate(
    players: List[Player], n_challenges: int
) -> Dict[str, Dict[str, Optional[float]]]:
    results = {p_1.username: {p_2.username: None for p_2 in players} for p_1 in players}
    for i, p_1 in enumerate(players):
        for j, p_2 in enumerate(players):
            if j <= i:
                continue
            await asyncio.gather(
                p_1.send_challenges(
                    opponent=to_id_str(p_2.username),
                    n_challenges=n_challenges,
                    to_wait=p_2.logged_in,
                ),
                p_2.accept_challenges(
                    opponent=to_id_str(p_1.username), n_challenges=n_challenges
                ),
            )
            results[p_1.username][p_2.username] = p_1.win_rate  # pyre-ignore
            results[p_2.username][p_1.username] = p_2.win_rate  # pyre-ignore

            p_1.reset_battles()
            p_2.reset_battles()
    return results  # pyre-ignore
