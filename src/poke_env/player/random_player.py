# -*- coding: utf-8 -*-
"""This module defines a random players baseline
"""

from poke_env.player.player import Player
from poke_env.player.battle_order import BattleOrder


class RandomPlayer(Player):
    def choose_move(self, battle) -> BattleOrder:
        return self.choose_random_move(battle)
