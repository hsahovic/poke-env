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
from poke_env.player.env import ObsType, PokeEnv
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
        fake: bool = False,
        strict: bool = True,
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
            fake=fake,
            strict=strict,
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
        act_size = 1 + num_switches + num_moves * num_targets * (num_gimmicks + 1)
        self.action_spaces = {
            agent: MultiDiscrete([act_size, act_size]) for agent in self.possible_agents
        }

    @staticmethod
    def action_to_order(
        action: npt.NDArray[np.int64],
        battle: DoubleBattle,
        fake: bool = False,
        strict: bool = True,
    ) -> BattleOrder:
        """
        Returns the BattleOrder relative to the given action.

        The action is a list in doubles, and the individual action mapping is as follows:
        element = -2: default
        element = -1: forfeit
        element = 0: pass
        1 <= element <= 6: switch
        7 <= element <= 11: move 1
        12 <= element <= 16: move 2
        17 <= element <= 21: move 3
        22 <= element <= 26: move 4
        27 <= element <= 31: move 1 and mega evolve
        32 <= element <= 36: move 2 and mega evolve
        37 <= element <= 41: move 3 and mega evolve
        42 <= element <= 46: move 4 and mega evolve
        47 <= element <= 51: move 1 and z-move
        52 <= element <= 56: move 2 and z-move
        57 <= element <= 61: move 3 and z-move
        62 <= element <= 66: move 4 and z-move
        67 <= element <= 71: move 1 and dynamax
        72 <= element <= 76: move 2 and dynamax
        77 <= element <= 81: move 3 and dynamax
        82 <= element <= 86: move 4 and dynamax
        87 <= element <= 91: move 1 and terastallize
        92 <= element <= 96: move 2 and terastallize
        97 <= element <= 101: move 3 and terastallize
        102 <= element <= 106: move 4 and terastallize

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
            order1 = DoublesEnv._action_to_order_individual(action[0], battle, fake, 0)
            order2 = DoublesEnv._action_to_order_individual(action[1], battle, fake, 1)
            joined_orders = DoubleBattleOrder.join_orders(
                [order1] if order1 is not None else [],
                [order2] if order2 is not None else [],
            )
            assert len(joined_orders) == 1, "invalid action"
            return joined_orders[0]
        except AssertionError as e:
            if not strict and str(e) == "invalid action":
                return DefaultBattleOrder()
            else:
                raise e

    @staticmethod
    def _action_to_order_individual(
        action: np.int64, battle: DoubleBattle, fake: bool, pos: int
    ) -> Optional[BattleOrder]:
        if action == 0:
            order = None
        elif action < 7:
            order = Player.create_order(list(battle.team.values())[action - 1])
            if not fake:
                assert isinstance(order.order, Pokemon)
                assert order.order.base_species in [
                    p.base_species for p in battle.available_switches[pos]
                ], "invalid action"
        else:
            active_mon = battle.active_pokemon[pos]
            if not fake:
                assert not battle.force_switch[pos], "invalid action"
                assert active_mon is not None, "invalid action"
            elif active_mon is None:
                return DefaultBattleOrder()
            mvs = (
                battle.available_moves[pos]
                if len(battle.available_moves[pos]) == 1
                and battle.available_moves[pos][0].id in ["struggle", "recharge"]
                else list(active_mon.moves.values())
            )
            if not fake:
                assert (action - 7) % 20 // 5 in range(len(mvs)), "invalid action"
            elif (action - 7) % 20 // 5 not in range(len(mvs)):
                return DefaultBattleOrder()
            order = Player.create_order(
                mvs[(action - 7) % 20 // 5],
                move_target=(action.item() - 7) % 5 - 2,
                mega=(action - 7) // 20 == 1,
                z_move=(action - 7) // 20 == 2,
                dynamax=(action - 7) // 20 == 3,
                terastallize=(action - 7) // 20 == 4,
            )
            if not fake:
                assert isinstance(order.order, Move)
                assert order.order.id in [
                    m.id for m in battle.available_moves[pos]
                ], "invalid action"
                move = [
                    m for m in battle.available_moves[pos] if m.id == order.order.id
                ][0]
                assert order.move_target in battle.get_possible_showdown_targets(
                    move, active_mon
                ), "invalid action"
                assert not order.mega or battle.can_mega_evolve[pos], "invalid action"
                assert not order.z_move or battle.can_z_move[pos], "invalid action"
                assert not order.dynamax or battle.can_dynamax[pos], "invalid action"
                assert (
                    not order.terastallize or battle.can_tera[pos] is not False
                ), "invalid action"
        return order

    @staticmethod
    def order_to_action(
        order: BattleOrder,
        battle: DoubleBattle,
        fake: bool = False,
        strict: bool = True,
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
                order.first_order, battle, fake, 0
            )
            action2 = DoublesEnv._order_to_action_individual(
                order.second_order, battle, fake, 1
            )
            return np.array([action1, action2])
        except AssertionError as e:
            if not strict and str(e) == "invalid order":
                return np.array([-2, -2])
            else:
                raise e

    @staticmethod
    def _order_to_action_individual(
        order: Optional[BattleOrder], battle: DoubleBattle, fake: bool, pos: int
    ) -> np.int64:
        if order is None:
            action = 0
        elif isinstance(order, DefaultBattleOrder):
            action = -2
        elif isinstance(order, ForfeitBattleOrder):
            action = -1
        elif order.order is None:
            raise ValueError()
        elif isinstance(order.order, Pokemon):
            action = [p.base_species for p in battle.team.values()].index(
                order.order.base_species
            ) + 1
        else:
            active_mon = battle.active_pokemon[pos]
            if not fake:
                assert not battle.force_switch[pos], "invalid order"
                assert active_mon is not None, "invalid order"
            elif active_mon is None:
                return np.int64(-2)
            mvs = (
                battle.available_moves[pos]
                if len(battle.available_moves[pos]) == 1
                and battle.available_moves[pos][0].id in ["struggle", "recharge"]
                else list(active_mon.moves.values())
            )
            if not fake:
                assert order.order.id in [m.id for m in mvs], "invalid order"
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
            action = 1 + 6 + 5 * action + target + 20 * gimmick
            if not fake:
                assert order.order.id in [
                    m.id for m in battle.available_moves[pos]
                ], "invalid order"
                move = [
                    m for m in battle.available_moves[pos] if m.id == order.order.id
                ][0]
                assert order.move_target in battle.get_possible_showdown_targets(
                    move, active_mon
                ), "invalid order"
                assert not order.mega or battle.can_mega_evolve[pos], "invalid order"
                assert not order.z_move or battle.can_z_move[pos], "invalid order"
                assert not order.dynamax or battle.can_dynamax[pos], "invalid order"
                assert (
                    not order.terastallize or battle.can_tera[pos] is not False
                ), "invalid order"
        return np.int64(action)
