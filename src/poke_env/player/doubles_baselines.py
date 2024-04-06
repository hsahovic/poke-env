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

#TODO: credit haris for stolen code from the Gen8OU example

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

class DoublesSimpleHeuristicsPlayer(Player):
    def teampreview(self, battle):
        mon_performance = {}

        # For each of our pokemons
        for i, mon in enumerate(battle.team.values()):
            # We store their average performance against the opponent team
            mon_performance[i] = np.mean(
                [
                    teampreview_performance(mon, opp)
                    for opp in battle.opponent_team.values()
                ]
            )

        # We sort our mons by performance
        ordered_mons = sorted(mon_performance, key=lambda k: -mon_performance[k])

        # We start with the one we consider best overall
        # We use i + 1 as python indexes start from 0
        #  but showdown's indexes start from 1
        return "/team " + "".join([str(i + 1) for i in ordered_mons])

    def _needs_speed_control(self, battle):
        #TODO:
        # formato de retorno !!!
        # afeta_meu_time(), afeta_opp()


        speed_control_available = [[move for move in battle.available_moves[0] if is_speed_control(move)], [move for move in battle.available_moves[1] if is_speed_control(move)]]
        #shuffling

        for move_list in speed_control_available:
            for move in move_list:
                self_speeds = [int(mon.stats["spe"]*multiplier_from_boost(mon.boosts["spe"])) for mon in battle.active_pokemon]
                opp_speeds = [int(estimate_max_speed(mon.base_stats["spe"], mon.level)*multiplier_from_boost(mon.boosts["spe"])) for mon in battle.opponent_active_pokemon]

                if (move.id == "trick_room"
                    and (11 not in battle.fields) #no TR active
                    and (18 not in battle.side_conditions) #no tailwind active on my side
                    and all_are_slower(self_speeds,opp_speeds)
                ):
                    return bixo_com_tr_usa_tr

                if (move.id == "tailwind"
                    and (18 not in battle.side_conditions)
                ):
                    for self_speed, opp_speed in product(self_speeds, opp_speeds):
                        if self_speed < opp_speed and 2*self_speed > opp_speed:
                            return bixo_usa

                if move.boosts["spe"]<0:
                    new_opp_speeds = [int(estimate_max_speed(mon.base_stats["spe"], mon.level)*multiplier_from_boost(mon.boosts["spe"]+move.boosts["spe"])) for mon in battle.opponent_active_pokemon]
                    for self_speed, i in product(self_speeds, range(len(new_opp_speeds))):
                        if self_speed < opp_speeds[i] and self_speed > new_opp_speeds[i]:
                            #ver questão de golpes spread/single target/todos
                            return bixo_usa

                if move.self_boosts["spe"]>0:
                    #garantir que mon aqui é o usuário
                    old_user_speed = int(mon.stats["spe"]*multiplier_from_boost(mon.boosts["spe"]))
                    new_user_speed = int(mon.stats["spe"]*multiplier_from_boost(mon.boosts["spe"]+move.self_boosts["spe"]))
                    for opp_speed in opp_speeds:
                        if old_user_speed < opp_speed and new_user_speed > opp_speed:
                            return bixo_usa

        return False

    def _needs_weather(self, battle):
        #TODO:
        # tipo de retorno
        # comparação do battle.weather
        # determina_melhor_troca
        weather_moves = {"hail": 4, "raindance": 6, "sandstorm": 7, "sunnyday": 8}
        weather_moves_available = [[move for move in battle.available_moves[0] if move in weather_moves.keys()], [move for move in battle.available_moves[1] if move in weather_moves.keys()]]

        for move in weather_moves_available[0]:
            if battle.weather != weather_moves[move]:
                return golpe

        for move in weather_moves_available[1]:
            if battle.weather != weather_moves[move]:
                return golpe

        weather_abilities = {"snowwarning": 4, "drizzle": 6, "sandstream": 7, "drought": 8}
        weather_ability_switch_ins = [mon for mon in battle.available_switches if mon.ability in weather_abilities.keys()]

        for mon in weather_ability_switch_ins:
            if battle.weather != weather_abilities[mon.ability]:
                troca = determina_melhor_troca()
                return troca

        return False

    def _make_switch(self, battle, mon):
        #TODO:
        # outspeeds
        # resists
        if (takes_supereffective(mon, opp_a)
           and (not (can_ko(mon, opp_a) and outspeeds(mon, opp_a))) #considerar speed control aqui
           and (opp_a.boosts[bigger_base_stat(opp_a)]>=0 and mon.boosts[opposite_def(bigger_base_stat(opp_a))]<=0)):

            possible_switches = [mon for mon in battle.available_switches if resists(mon, tipo_superefetivo_a) and mon.current_hp_fraction>0.5]
            if possible_switches:
                return max(possible_switches, key = lambda mon: mon.current_hp_fraction)

        if (takes_supereffective(mon, opp_b)
           and (not (can_ko(mon, opp_b) and outspeeds(mon, opp_b)))
           and (opp_b.boosts[bigger_base_stat(opp_b)]>=0 and mon.boosts[opposite_def(bigger_base_stat(opp_b))]<=0)):

            possible_switches = [mon for mon in battle.available_switches if resists(mon, tipo_superefetivo_b) and mon.current_hp_fraction>0.5]
            if possible_switches:
                return max(possible_switches, key = lambda mon: mon.current_hp_fraction)

        return False

    def _make_protect(self,battle,mon):
        protect_moves = [move for move in mon.moves.values() if move.is_protect_counter]
        if (protect_moves
            and mon.protect_counter==0
            and (
                    (takes_supereffective(mon, opp_a)
                    and not (can_ko(mon, opp_a) and outspeeds(mon, opp_a))
                    and (partner_using_speed_control or can_ko(partner, mon_a)))
                or (takes_supereffective(mon, opp_b)
                    and not (can_ko(mon, opp_b) and outspeeds(mon, opp_b))
                    and (partner_using_speed_control or can_ko(partner, mon_b)))
            )
        ):
            return random.choice(protect_moves)
        return False

    def _should_setup(self,battle,mon):
        setup_moves = [move for move in mon.moves.values() if (
                        move.boosts
                        and sum(move.boosts.values()) >= 2
                        and move.target == "self"
                    )]

        if (setup_moves
            and mon.current_hp_fraction>0.5
            and not can_ko(mon, opp_a)
            and not can_ko(mon, opp_b)
            and resists(mon, opp_a) or opp_a.boosts[bigger_base_stat(opp_a)]<0 and not takes_supereffective(mon, opp_a)
            and resists(mon, opp_b) or opp_b.boosts[bigger_base_stat(opp_b)]<0 and not takes_supereffective(mon, opp_b)
        ):
            return max(setup_moves, key=lambda move: sum(move.boosts.values()))

        return False

    def _targeting(self,battle,slot):
        mon = battle.active_pokemon[slot]
        opp_a, opp_b = battle.opponent_active_pokemon
        partner = False
        for self_mon in battle.active_pokemon:
            if mon is not self_mon:
                partner = self_mon

        # if can_ko(mon, opp_a):
        #     if can_ko(mon, opp_b):
        #         if partner and can_ko(partner, opp_b):
        #             return (best_move(mon, opp_a), opp_a)
        #         if partner and can_ko(partner, opp_a):
        #             return (best_move(mon, opp_b), opp_b)
        #         if outspeeds(mon, opp_a):
        #             return (best_move(mon, opp_a), opp_a)
        #         if outspeeds(mon, opp_b):
        #             return (best_move(mon, opp_b), opp_b)
        #     return (best_move(mon, opp_a), opp_a)
        # if can_ko(mon, opp_b):
        #     return (best_move(mon, opp_b), opp_b)

        moves =  {move: 0 for move in mon.moves.values() if move in battle.available_moves[slot]}
        for move in moves:
            if move.base_power and move.target != "normal":
                moves[move]+=100
            if move.base_power and opp_a is not None and supereffective(move, opp_a):
                moves[move]+=100
            if move.base_power and opp_b is not None and supereffective(move, opp_b):
                moves[move]+=100
            if (opp_a is None or immune(move, opp_a)) and (opp_b is None or immune(move, opp_b)):
                moves[move] = -1000
            moves[move]+=move.base_power * (1.5 if move.type in mon.types else 1)

        best_move_ = max(moves.keys(), key=lambda move: moves[move])
        target = takes_most_from_move(best_move_, opp_a, opp_b)
        target_slot = battle.OPPONENT_1_POSITION if target == opp_a else battle.OPPONENT_2_POSITION
        if len(battle.get_possible_showdown_targets(best_move_, mon))==1:
            target_slot = battle.get_possible_showdown_targets(best_move_, mon)[0]
        # print("SLOT: "+str(target_slot))
        # print("DEDUCED TARGET: "+best_move_.deduced_target)
        # print("TARGET: "+best_move_.target)
        # print("POSSIBLE TARGETS: "+str(battle.get_possible_showdown_targets(best_move_, mon)))
        return [BattleOrder(best_move_, move_target=target_slot)]

    def _should_help_partner(self, battle, slot):
        mon = battle.active_pokemon[slot]

        if (len(battle.active_pokemon) == 2
            #and not can_ko(mon, opp_a)
            #and not can_ko(mon, opp_b)
        ):
            for self_mon in battle.active_pokemon:
                if mon is not self_mon:
                    partner = self_mon

            side_condition_values = [cond.value for cond in battle.side_conditions]

            if partner and "helpinghand" in mon.moves and not ("helpinghand" in partner.moves):
                move = mon.moves["helpinghand"]
                target_slot = battle.get_possible_showdown_targets(move, mon)[0]
                return [BattleOrder(move, move_target=target_slot)]

            if (
                "auroraveil" in mon.moves
                and 2 not in side_condition_values
                and battle.weather
                and list(battle.weather)[0].value == 4
            ):
                move = mon.moves["auroraveil"]
                target_slot = battle.get_possible_showdown_targets(move, mon)[0]
                return [BattleOrder(move, move_target=target_slot)]

            if "lightscreen" in mon.moves and (10 not in side_condition_values):
                move = mon.moves["lightscreen"]
                target_slot = battle.get_possible_showdown_targets(move, mon)[0]
                return [BattleOrder(move, move_target=target_slot)]

            if "reflect" in mon.moves and (13 not in side_condition_values):
                move = mon.moves["reflect"]
                target_slot = battle.get_possible_showdown_targets(move, mon)[0]
                return [BattleOrder(move, move_target=target_slot)]

            for move in battle.available_moves[slot]:
                if move.status and move.target != "self":
                    for target_slot, opp in enumerate(battle.opponent_active_pokemon):
                        if opp and not opp.status:
                            return [BattleOrder(move, move_target=target_slot+1)]

        return False

    def choose_move(self, battle):
        if battle.available_moves[0] or battle.available_moves[1]:
            my_order = []
            for slot, mon in enumerate(battle.active_pokemon):
                if mon:
                    mon_order = self._should_help_partner(battle, slot)
                    if mon_order:
                        pass
                    elif battle.available_moves[slot] and battle.available_moves[slot][0].id != "struggle":
                        try:
                            mon_order = self._targeting(battle, slot)
                        except ValueError:
                            print("RANDOM MOVE (VALUE ERROR)")
                            self.choose_random_doubles_move(battle)
                    elif battle.available_switches[slot]:
                        #TODO: melhorar troca
                        mon_order = [self.create_order(battle.available_switches[slot][0])]
                    else:
                        print("RANDOM MOVE (ELSE)")
                        self.choose_random_doubles_move(battle)
                else:
                    mon_order = []
                my_order.append(mon_order)

            # print("After enumerate")
            order = DoubleBattleOrder.join_orders(my_order[0], my_order[1])
            # print([my_order[0], my_order[1]])
            return order[0]

        return self.choose_random_doubles_move(battle)

###############################################################################################################
###############################################################################################################

def teampreview_performance(mon_a, mon_b):
    # We evaluate the performance on mon_a against mon_b as its type advantage
    a_on_b = b_on_a = -np.inf
    for type_ in mon_a.types:
        if type_:
            a_on_b = max(a_on_b, type_.damage_multiplier(*mon_b.types))
    # We do the same for mon_b over mon_a
    for type_ in mon_b.types:
        if type_:
            b_on_a = max(b_on_a, type_.damage_multiplier(*mon_a.types))
    # Our performance metric is the different between the two
    return a_on_b - b_on_a

def estimate_max_speed(base_speed, level):
    return int( ( int( (31 + 2 * base_speed + int(252/4) ) * level/100 ) + 5) * 1.1)

def multiplier_from_boost(boost):
    if boost<0:
        return 2/(2+(-1)*boost)
    else:
        return (2+boost)/2

def can_ko(attacker, target):
    #TODO:
    # damage calcs
    # check all moves
    return (random.random()>0.5)

def is_speed_control(move):
    if move.id in ["tailwind", "trickroom"]: #field conditions
        return True

    if move.id in ["thunderwave", "nuzzle"]: #paralysis
        return True

    if move.boosts["spe"]<0 or move.self_boosts["spe"]>0:
        return True

    return False

def all_are_slower(self_speeds, opp_speeds):
    for self_speed, opp_speed in product(self_speeds, opp_speeds):
        if self_speed >= opp_speed:
            return False
    return True

def takes_supereffective(defender, attacker):
    for type_ in attacker.types:
        if defender.damage_multiplier(type_) > 1:
            return True
    return False

def resists(defender, attacker):
    for type_ in attacker.types:
        if defender.damage_multiplier(type_) >= 1:
            return False
    return True

def supereffective(move, target):
    return target.damage_multiplier(move)>1

def immune(move, target):
    return target.damage_multiplier(move)==0

#TODO: improve
def takes_most_from_move(move, opp_a, opp_b):
    if opp_a is None:
        return opp_b
    if opp_b is None:
        return opp_a
    if opp_a.damage_multiplier(move) > opp_b.damage_multiplier(move):
        return opp_a
    return opp_b

def best_move(mon, opp):
    return False
    #copiar max damage


