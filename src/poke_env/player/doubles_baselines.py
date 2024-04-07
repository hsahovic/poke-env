# -*- coding: utf-8 -*-
import random
from itertools import product

from poke_env.environment.move_category import MoveCategory
from poke_env.player.player import Player
from poke_env.player.battle_order import (
    BattleOrder,
    DefaultBattleOrder,
    DoubleBattleOrder,
)

class MaxDamageDoublesPlayer(Player):
    def choose_move(self, battle):
        slots = [0,1]
        if battle.available_moves:
            my_order = []
            for i in slots:
                if battle.active_pokemon[i] and battle.available_moves[i]:
                    best_move_lambda_key = lambda move: move.base_power if move.target=="normal" else move.base_power*0.75*2
                    best_move_ = max(battle.available_moves[i], key=best_move_lambda_key)
                    targets = battle.get_possible_showdown_targets(best_move_, battle.active_pokemon[i])
                    opp_targets = [t for t in targets if t>0]
                    if opp_targets:
                        target = opp_targets[int(random.random() * len(opp_targets))]
                    else:
                        target = targets[int(random.random() * len(targets))]
                    my_order.append([BattleOrder(best_move_, move_target=target)])
                else:
                    my_order.append([])
            order = DoubleBattleOrder.join_orders(my_order[0], my_order[1])
            return order[0]

        return self.choose_random_doubles_move(battle)


