# -*- coding: utf-8 -*-
"""This module defines a random players baseline
"""

from poke_env.player.player import Player


class RandomPlayer(Player):
    def choose_move(self, battle) -> str:
        return self.choose_random_move(battle)
