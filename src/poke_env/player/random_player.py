"""This module defines a random players baseline
"""

from poke_env.environment import Battle, DoubleBattle
from poke_env.player.battle_order import BattleOrder
from poke_env.player.player import Player


class RandomPlayer(Player):
    def choose_singles_move(self, battle: Battle) -> BattleOrder:
        return self.choose_random_singles_move(battle)

    def choose_doubles_move(self, battle: DoubleBattle) -> BattleOrder:
        return self.choose_random_doubles_move(battle)
