import random
from typing import List, Tuple

from poke_env.battle.abstract_battle import AbstractBattle
from poke_env.battle.battle import Battle
from poke_env.battle.double_battle import DoubleBattle
from poke_env.battle.move import Move
from poke_env.battle.move_category import MoveCategory
from poke_env.battle.pokemon import Pokemon
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.target import Target
from poke_env.data import GenData
from poke_env.player.battle_order import (
    BattleOrder,
    DefaultBattleOrder,
    DoubleBattleOrder,
    PassBattleOrder,
    SingleBattleOrder,
)
from poke_env.player.player import Player


class RandomPlayer(Player):
    def choose_move(self, battle: AbstractBattle) -> BattleOrder:
        return self.choose_random_move(battle)


class MaxBasePowerPlayer(Player):
    def choose_move(self, battle: AbstractBattle):
        if self.format_is_doubles:
            return self.choose_doubles_move(battle)  # type: ignore
        else:
            return self.choose_singles_move(battle)

    def choose_singles_move(self, battle: AbstractBattle):
        if battle.available_moves:
            best_move = max(battle.available_moves, key=lambda move: move.base_power)
            return self.create_order(best_move)
        return self.choose_random_move(battle)

    def choose_doubles_move(self, battle: DoubleBattle):
        orders: List[SingleBattleOrder] = []
        switched_in = None

        if any(battle.force_switch):
            return self.choose_random_doubles_move(battle)

        can_target_first_opponent = (
            battle.opponent_active_pokemon[0]
            and not battle.opponent_active_pokemon[0].fainted
        )
        can_target_second_opponent = (
            battle.opponent_active_pokemon[1]
            and not battle.opponent_active_pokemon[1].fainted
        )
        can_double_target = can_target_first_opponent and can_target_second_opponent

        for mon, moves, switches in zip(
            battle.active_pokemon, battle.available_moves, battle.available_switches
        ):
            switches = [s for s in switches if s != switched_in]

            if not mon or mon.fainted:
                orders.append(PassBattleOrder())
                continue
            elif not moves and switches:
                mon_to_switch_in = random.choice(switches)
                orders.append(SingleBattleOrder(mon_to_switch_in))
                switched_in = mon_to_switch_in
                continue
            elif not moves:
                orders.append(DefaultBattleOrder())
                continue

            def move_power_with_double_target(move):
                if move.target in {Target.NORMAL, Target.ANY} or not can_double_target:
                    return move.base_power
                return move.base_power * 1.5

            best_move = max(moves, key=move_power_with_double_target)

            # randomly picks between the two opponents for normal move targeting
            targets = battle.get_possible_showdown_targets(best_move, mon)
            opp_targets = [
                t
                for t in targets
                if t in {battle.OPPONENT_1_POSITION, battle.OPPONENT_2_POSITION}
            ]
            if opp_targets:
                target = random.choice(opp_targets)
            else:
                target = random.choice(targets)

            orders.append(SingleBattleOrder(best_move, move_target=target))

        if orders[0] or orders[1]:
            return DoubleBattleOrder(orders[0], orders[1])

        return self.choose_random_move(battle)


class PseudoBattle(Battle):
    def __init__(self, battle: DoubleBattle, active_id: int, opp_id: int):
        self._gen = battle.gen
        self._active_pokemon = battle.active_pokemon[active_id]
        self._opponent_active_pokemon = battle.opponent_active_pokemon[opp_id]
        self._team = battle.team
        self._opponent_team = battle.opponent_team
        self._available_moves = battle.available_moves[active_id]
        self._available_switches = battle.available_switches[active_id]
        self._force_switch = battle.force_switch[active_id]
        self._trapped = battle.trapped[active_id]
        self._wait = battle._wait
        self._side_conditions = battle.side_conditions
        self._opponent_side_conditions = battle.opponent_side_conditions
        self._can_mega_evolve = battle.can_mega_evolve[active_id]
        self._can_z_move = battle.can_z_move[active_id]
        self._can_dynamax = battle.can_dynamax[active_id]
        self._can_tera = battle.can_tera[active_id]

    @property
    def active_pokemon(self):
        return self._active_pokemon

    @property
    def opponent_active_pokemon(self):
        return self._opponent_active_pokemon


class SimpleHeuristicsPlayer(Player):
    ENTRY_HAZARDS = {
        "spikes": SideCondition.SPIKES,
        "stealhrock": SideCondition.STEALTH_ROCK,
        "stickyweb": SideCondition.STICKY_WEB,
        "toxicspikes": SideCondition.TOXIC_SPIKES,
    }

    ANTI_HAZARDS_MOVES = {"rapidspin", "defog"}

    SPEED_TIER_COEFICIENT = 0.1
    HP_FRACTION_COEFICIENT = 0.4
    SWITCH_OUT_MATCHUP_THRESHOLD = -2

    def _estimate_matchup(self, mon: Pokemon, opponent: Pokemon):
        score = max([opponent.damage_multiplier(t) for t in mon.types if t is not None])
        score -= max(
            [mon.damage_multiplier(t) for t in opponent.types if t is not None]
        )
        if mon.base_stats["spe"] > opponent.base_stats["spe"]:
            score += self.SPEED_TIER_COEFICIENT
        elif opponent.base_stats["spe"] > mon.base_stats["spe"]:
            score -= self.SPEED_TIER_COEFICIENT

        score += mon.current_hp_fraction * self.HP_FRACTION_COEFICIENT
        score -= opponent.current_hp_fraction * self.HP_FRACTION_COEFICIENT

        return score

    def _should_dynamax(self, battle: AbstractBattle, n_remaining_mons: int):
        if battle.can_dynamax:
            # Last full HP mon
            if (
                len([m for m in battle.team.values() if m.current_hp_fraction == 1])
                == 1
                and battle.active_pokemon.current_hp_fraction == 1
            ):
                return True
            # Matchup advantage and full hp on full hp
            if (
                self._estimate_matchup(
                    battle.active_pokemon, battle.opponent_active_pokemon
                )
                > 0
                and battle.active_pokemon.current_hp_fraction == 1
                and battle.opponent_active_pokemon.current_hp_fraction == 1
            ):
                return True
            if n_remaining_mons == 1:
                return True
        return False

    def _should_terastallize(self, battle: Battle, move: Move) -> bool:
        active = battle.active_pokemon
        opp_active = battle.opponent_active_pokemon
        if (
            not battle.can_tera
            or not active
            or not opp_active
            or active.tera_type is None
        ):
            return False
        offensive_tera_score = opp_active.damage_multiplier(move.type)
        defensive_score = min(
            [1 / (active.damage_multiplier(t) or 1 / 8) for t in opp_active.types]
        )
        defensive_tera_score = min(
            [
                1
                / (
                    t.damage_multiplier(
                        active.tera_type,
                        type_chart=GenData.from_gen(battle.gen).type_chart,
                    )
                    or 1 / 8
                )
                for t in opp_active.types
            ]
        )
        return offensive_tera_score * (defensive_tera_score / defensive_score) > 1

    def _should_switch_out(self, battle: AbstractBattle):
        active = battle.active_pokemon
        opponent = battle.opponent_active_pokemon
        # If there is a decent switch in...
        if [
            m
            for m in battle.available_switches
            if self._estimate_matchup(m, opponent) > 0
        ]:
            # ...and a 'good' reason to switch out
            if active.boosts["def"] <= -3 or active.boosts["spd"] <= -3:
                return True
            if (
                active.boosts["atk"] <= -3
                and active.stats["atk"] >= active.stats["spa"]
            ):
                return True
            if (
                active.boosts["spa"] <= -3
                and active.stats["atk"] <= active.stats["spa"]
            ):
                return True
            if (
                self._estimate_matchup(active, opponent)
                < self.SWITCH_OUT_MATCHUP_THRESHOLD
            ):
                return True
        return False

    def _stat_estimation(self, mon: Pokemon, stat: str):
        # Stats boosts value
        if mon.boosts[stat] > 1:
            boost = (2 + mon.boosts[stat]) / 2
        else:
            boost = 2 / (2 - mon.boosts[stat])
        return ((2 * mon.base_stats[stat] + 31) + 5) * boost

    def choose_singles_move(self, battle: Battle) -> Tuple[SingleBattleOrder, float]:
        # Main mons shortcuts
        active = battle.active_pokemon
        opponent = battle.opponent_active_pokemon

        if active is None or opponent is None:
            return self.choose_random_singles_move(battle), 0

        # Rough estimation of damage ratio
        physical_ratio = self._stat_estimation(active, "atk") / self._stat_estimation(
            opponent, "def"
        )
        special_ratio = self._stat_estimation(active, "spa") / self._stat_estimation(
            opponent, "spd"
        )

        if battle.available_moves and (
            not self._should_switch_out(battle) or not battle.available_switches
        ):
            n_remaining_mons = len(
                [m for m in battle.team.values() if m.fainted is False]
            )
            n_opp_remaining_mons = 6 - len(
                [m for m in battle.opponent_team.values() if m.fainted is True]
            )

            # Entry hazard...
            for move in battle.available_moves:
                # ...setup
                if (
                    n_opp_remaining_mons >= 3
                    and move.id in self.ENTRY_HAZARDS
                    and self.ENTRY_HAZARDS[move.id]
                    not in battle.opponent_side_conditions
                ):
                    return self.create_order(move), 0

                # ...removal
                elif (
                    battle.side_conditions
                    and move.id in self.ANTI_HAZARDS_MOVES
                    and n_remaining_mons >= 2
                ):
                    return self.create_order(move), 0

            # Setup moves
            if (
                active.current_hp_fraction == 1
                and self._estimate_matchup(active, opponent) > 0
            ):
                for move in battle.available_moves:
                    if (
                        move.boosts
                        and sum(move.boosts.values()) >= 2
                        and move.target == "self"
                        and min(
                            [active.boosts[s] for s, v in move.boosts.items() if v > 0]
                        )
                        < 6
                    ):
                        return self.create_order(move), 0

            move, score = max(
                [
                    (
                        m,
                        m.base_power
                        * (1.5 if m.type in active.types else 1)
                        * (
                            physical_ratio
                            if m.category == MoveCategory.PHYSICAL
                            else special_ratio
                        )
                        * m.accuracy
                        * m.expected_hits
                        * opponent.damage_multiplier(m),
                    )
                    for m in battle.available_moves
                ],
                key=lambda x: x[1],
            )
            return (
                self.create_order(
                    move,
                    dynamax=self._should_dynamax(battle, n_remaining_mons),
                    terastallize=self._should_terastallize(battle, move),
                ),
                score,
            )

        if battle.available_switches:
            switches: List[Pokemon] = battle.available_switches
            return (
                self.create_order(
                    max(switches, key=lambda s: self._estimate_matchup(s, opponent))
                ),
                0,
            )

        return self.choose_random_singles_move(battle), 0

    @staticmethod
    def get_double_target_multiplier(battle: DoubleBattle, order: SingleBattleOrder):
        can_target_first_opponent = (
            battle.opponent_active_pokemon[0]
            and not battle.opponent_active_pokemon[0].fainted
        )
        can_target_second_opponent = (
            battle.opponent_active_pokemon[1]
            and not battle.opponent_active_pokemon[1].fainted
        )
        can_double_target = can_target_first_opponent and can_target_second_opponent
        return (
            1
            if not hasattr(order, "order")
            or not isinstance(order.order, Move)
            or order.order.target in {Target.NORMAL, Target.ANY}
            or not can_double_target
            else 1.5
        )

    def choose_move(self, battle: AbstractBattle):
        if not isinstance(battle, DoubleBattle):
            return self.choose_singles_move(battle)[0]  # type: ignore
        orders: List[SingleBattleOrder] = []
        for active_id in [0, 1]:
            if (
                battle.active_pokemon[active_id] is None
                and not battle.available_switches[active_id]
            ):
                orders += [PassBattleOrder()]
                continue
            results = [
                self.choose_singles_move(PseudoBattle(battle, active_id, opp_id))
                for opp_id in [0, 1]
            ]
            possible_orders = [r[0] for r in results]
            scores = [r[1] for r in results]
            for order in possible_orders:
                mon = battle.active_pokemon[active_id]
                if (
                    order is not None
                    and hasattr(order, "order")
                    and isinstance(order.order, Move)
                    and mon is not None
                ):
                    target = [o for o in possible_orders].index(order) + 1
                    possible_targets = battle.get_possible_showdown_targets(
                        order.order, mon
                    )
                    if target not in possible_targets:
                        target = possible_targets[0]
                    order.move_target = target
            scores = [
                scores[i]
                * self.get_double_target_multiplier(battle, possible_orders[i])
                for i in [0, 1]
            ]
            orders += [
                (
                    max(results, key=lambda a: a[1])[0]
                    if battle.force_switch != [[False, True], [True, False]][active_id]
                    and not (
                        len(battle.available_switches[active_id]) == 1
                        and battle.force_switch == [True, True]
                        and active_id == 1
                    )
                    else PassBattleOrder()
                )
            ]
        joined_orders = DoubleBattleOrder.join_orders([orders[0]], [orders[1]])
        if joined_orders:
            return joined_orders[0]
        else:
            return DoubleBattleOrder(orders[0], DefaultBattleOrder())
