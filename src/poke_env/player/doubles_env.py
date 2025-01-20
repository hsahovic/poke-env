from typing import Optional, Union

import numpy as np
import numpy.typing as npt
from gymnasium.spaces import MultiDiscrete

from poke_env.environment import DoubleBattle, Move, Pokemon
from poke_env.player.battle_order import (
    BattleOrder,
    DefaultBattleOrder,
    DoubleBattleOrder,
    ForfeitBattleOrder,
)
from poke_env.player.gymnasium_api import ObsType, PokeEnv
from poke_env.player.player import Player
from poke_env.ps_client import (
    AccountConfiguration,
    LocalhostServerConfiguration,
    ServerConfiguration,
)
from poke_env.teambuilder import Teambuilder


class DoublesEnv(PokeEnv[ObsType, npt.NDArray[np.int64]]):
    def __init__(
        self,
        account_configuration1: Optional[AccountConfiguration] = None,
        account_configuration2: Optional[AccountConfiguration] = None,
        avatar: Optional[int] = None,
        battle_format: str = "gen8randombattle",
        log_level: Optional[int] = None,
        save_replays: Union[bool, str] = False,
        server_configuration: Optional[
            ServerConfiguration
        ] = LocalhostServerConfiguration,
        accept_open_team_sheet: Optional[bool] = False,
        start_timer_on_battle_start: bool = False,
        start_listening: bool = True,
        open_timeout: Optional[float] = 10.0,
        ping_interval: Optional[float] = 20.0,
        ping_timeout: Optional[float] = 20.0,
        team: Optional[Union[str, Teambuilder]] = None,
        start_challenging: bool = False,
    ):
        super().__init__(
            account_configuration1=account_configuration1,
            account_configuration2=account_configuration2,
            avatar=avatar,
            battle_format=battle_format,
            log_level=log_level,
            save_replays=save_replays,
            server_configuration=server_configuration,
            accept_open_team_sheet=accept_open_team_sheet,
            start_timer_on_battle_start=start_timer_on_battle_start,
            start_listening=start_listening,
            open_timeout=open_timeout,
            ping_interval=ping_interval,
            ping_timeout=ping_timeout,
            team=team,
            start_challenging=start_challenging,
        )
        num_switches = 6
        num_moves = 4
        num_targets = 5
        if battle_format.startswith("gen6"):
            num_gimmicks = 1
        elif battle_format.startswith("gen7"):
            num_gimmicks = 2
        elif battle_format.startswith("gen8"):
            num_gimmicks = 3
        elif battle_format.startswith("gen9"):
            num_gimmicks = 4
        else:
            num_gimmicks = 0
        act_size = num_switches + num_moves * num_targets * (num_gimmicks + 1)
        self.action_spaces = {
            agent: MultiDiscrete([act_size, act_size]) for agent in self.possible_agents
        }

    @staticmethod
    def action_to_order(
        action: npt.NDArray[np.int64], battle: DoubleBattle
    ) -> BattleOrder:
        """
        Returns the BattleOrder relative to the given action.

        The action is a list in doubles, and the individual action mapping is as follows:
        element = -2: default
        element = -1: forfeit
        element = 0: pass
        1 <= element <= 6: switch
        7 <= element <= 10: move with target = -2
        11 <= element <= 14: move with target = -1
        15 <= element <= 18: move with target = 0
        19 <= element <= 22: move with target = 1
        23 <= element <= 26: move with target = 2
        27 <= element <= 30: move with target = -2 and mega evolve
        31 <= element <= 34: move with target = -1 and mega evolve
        35 <= element <= 38: move with target = 0 and mega evolve
        39 <= element <= 42: move with target = 1 and mega evolve
        43 <= element <= 46: move with target = 2 and mega evolve
        47 <= element <= 50: move with target = -2 and z-move
        51 <= element <= 54: move with target = -1 and z-move
        55 <= element <= 58: move with target = 0 and z-move
        59 <= element <= 62: move with target = 1 and z-move
        63 <= element <= 66: move with target = 2 and z-move
        67 <= element <= 70: move with target = -2 and dynamax
        71 <= element <= 74: move with target = -1 and dynamax
        75 <= element <= 78: move with target = 0 and dynamax
        79 <= element <= 82: move with target = 1 and dynamax
        83 <= element <= 86: move with target = 2 and dynamax
        87 <= element <= 90: move with target = -2 and terastallize
        91 <= element <= 94: move with target = -1 and terastallize
        95 <= element <= 98: move with target = 0 and terastallize
        99 <= element <= 102: move with target = 1 and terastallize
        103 <= element <= 106: move with target = 2 and terastallize

        :param action: The action to take.
        :type action: ndarray[int64]
        :param battle: The current battle state
        :type battle: AbstractBattle

        :return: The battle order for the given action in context of the current battle.
        :rtype: BattleOrder

        """
        try:
            if action[0] == -2 or action[1] == -2:
                return DefaultBattleOrder()
            elif action[0] == -1 or action[1] == -1:
                return ForfeitBattleOrder()
            dont_respond1 = any(battle.force_switch) and not battle.force_switch[0]
            dont_respond2 = any(battle.force_switch) and not battle.force_switch[1]
            order1 = (
                None
                if dont_respond1
                else DoublesEnv._action_to_order_individual(action[0], battle, 0)
            )
            order2 = (
                None
                if dont_respond2
                else DoublesEnv._action_to_order_individual(action[1], battle, 1)
            )
            return DoubleBattleOrder.join_orders(
                [order1] if order1 is not None else [],
                [order2] if order2 is not None else [],
            )[0]
        except AssertionError as e:
            if str(e) == "invalid pick":
                return Player.choose_random_move(battle)
            else:
                raise e

    @staticmethod
    def _action_to_order_individual(
        action: np.int64, battle: DoubleBattle, pos: int
    ) -> Optional[BattleOrder]:
        order: Optional[BattleOrder]
        if action == 0:
            order = None
        elif action < 7:
            order = Player.create_order(list(battle.team.values())[action - 1])
            assert order.order in battle.available_switches[pos], "invalid pick"
        else:
            assert not battle.force_switch[pos], "invalid pick"
            active_mon = battle.active_pokemon[pos]
            assert active_mon is not None, "invalid pick"
            mvs = (
                battle.available_moves[pos]
                if len(battle.available_moves[pos]) == 1
                and battle.available_moves[pos][0].id in ["struggle", "recharge"]
                else list(active_mon.moves.values())
            )
            assert (action - 7) % 4 in range(len(mvs)), "invalid pick"
            order = Player.create_order(
                mvs[(action - 7) % 4],
                move_target=(action.item() - 7) % 20 // 4 - 2,
                mega=(action - 7) // 20 == 1,
                z_move=(action - 7) // 20 == 2,
                dynamax=(action - 7) // 20 == 3,
                terastallize=(action - 7) // 20 == 4,
            )
            assert isinstance(order.order, Move)
            assert order.order.id in [
                m.id for m in battle.available_moves[pos]
            ], "invalid pick"
            move = [m for m in battle.available_moves[pos] if m.id == order.order.id][0]
            assert order.move_target in battle.get_possible_showdown_targets(
                move, active_mon
            ), "invalid pick"
            assert not order.mega or battle.can_mega_evolve[pos], "invalid pick"
            assert not order.z_move or battle.can_z_move[pos], "invalid pick"
            assert not order.dynamax or battle.can_dynamax[pos], "invalid pick"
            assert (
                not order.terastallize or battle.can_tera[pos] is not False
            ), "invalid pick"
        return order

    @staticmethod
    def order_to_action(
        order: BattleOrder, battle: DoubleBattle
    ) -> npt.NDArray[np.int64]:
        """
        Returns the action relative to the given BattleOrder.

        :param order: The order to take.
        :type order: BattleOrder
        :param battle: The current battle state
        :type battle: AbstractBattle

        :return: The action for the given battle order in context of the current battle.
        :rtype: ndarray[int64]
        """
        try:
            if isinstance(order, DefaultBattleOrder):
                return np.array([-2, -2])
            elif isinstance(order, ForfeitBattleOrder):
                return np.array([-1, -1])
            assert isinstance(order, DoubleBattleOrder)
            action1 = DoublesEnv._order_to_action_individual(
                order.first_order, battle, 0
            )
            action2 = DoublesEnv._order_to_action_individual(
                order.second_order, battle, 1
            )
            return np.array([action1, action2])
        except AssertionError as e:
            if str(e) == "invalid pick":
                return np.array([-2, -2])
            else:
                raise e

    @staticmethod
    def _order_to_action_individual(
        order: Optional[BattleOrder], battle: DoubleBattle, pos: int
    ) -> np.int64:
        if order is None:
            action = 0
        elif isinstance(order, DefaultBattleOrder):
            action = -2
        elif isinstance(order, ForfeitBattleOrder):
            action = -1
        elif order.order is None:
            raise AssertionError()
        elif isinstance(order.order, Pokemon):
            action = [p.base_species for p in battle.team.values()].index(
                order.order.base_species
            ) + 1
        else:
            assert not battle.force_switch[pos], "invalid pick"
            active_mon = battle.active_pokemon[pos]
            assert active_mon is not None, "invalid pick"
            mvs = (
                battle.available_moves[pos]
                if len(battle.available_moves[pos]) == 1
                and battle.available_moves[pos][0].id in ["struggle", "recharge"]
                else list(active_mon.moves.values())
            )
            assert order.order.id in [m.id for m in mvs], "invalid pick"
            action = [m.id for m in mvs].index(order.order.id)
            target = order.move_target + 2
            if order.mega:
                gimmick = 1
            elif order.z_move:
                gimmick = 2
            elif order.dynamax:
                gimmick = 3
            elif order.terastallize:
                gimmick = 4
            else:
                gimmick = 0
            action = 1 + 6 + action + 4 * target + 20 * gimmick
            assert order.order.id in [
                m.id for m in battle.available_moves[pos]
            ], "invalid pick"
            move = [m for m in battle.available_moves[pos] if m.id == order.order.id][0]
            assert order.move_target in battle.get_possible_showdown_targets(
                move, active_mon
            ), "invalid pick"
            assert not order.mega or battle.can_mega_evolve[pos], "invalid pick"
            assert not order.z_move or battle.can_z_move[pos], "invalid pick"
            assert not order.dynamax or battle.can_dynamax[pos], "invalid pick"
            assert (
                not order.terastallize or battle.can_tera[pos] is not False
            ), "invalid pick"
        return np.int64(action)
