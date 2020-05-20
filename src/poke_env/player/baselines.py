# -*- coding: utf-8 -*-
from poke_env.player.player import Player


class MaxBasePowerPlayer(Player):
    def choose_move(self, battle):
        if battle.available_moves:
            best_move = max(battle.available_moves, key=lambda move: move.base_power)
            return self.create_order(best_move)
        return self.choose_random_move(battle)
