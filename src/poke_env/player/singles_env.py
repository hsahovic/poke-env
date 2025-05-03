from typing import Optional, Union

import numpy as np
from gymnasium.spaces import Discrete

from poke_env.environment import Battle, Move, Pokemon
from poke_env.player.battle_order import (
    BattleOrder,
    DefaultBattleOrder,
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


class SinglesEnv(PokeEnv[ObsType, np.int64]):
    def __init__(
        self,
        *,
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
            start_challenging=start_challenging,
            fake=fake,
            strict=strict,
        )
        num_switches = 6
        num_moves = 4
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
        act_size = num_switches + num_moves * (num_gimmicks + 1)
        self.action_spaces = {
            agent: Discrete(act_size) for agent in self.possible_agents
        }

    @staticmethod
    def action_to_order(
        action: np.int64, battle: Battle, fake: bool = False, strict: bool = True
    ) -> BattleOrder:
        """
        Returns the BattleOrder relative to the given action.

        The action mapping is as follows:
        action = -2: default
        action = -1: forfeit
        0 <= action <= 5: switch
        6 <= action <= 9: move
        10 <= action <= 13: move and mega evolve
        14 <= action <= 17: move and z-move
        18 <= action <= 21: move and dynamax
        22 <= action <= 25: move and terastallize

        :param action: The action to take.
        :type action: int64
        :param battle: The current battle state
        :type battle: AbstractBattle
        :param fake: If true, action-order converters will try to avoid returning a default
            output if at all possible, even if the output isn't a legal decision. Defaults
            to False.
        :type fake: bool
        :param strict: If true, action-order converters will throw an error if the move is
            illegal. Otherwise, it will return default. Defaults to True.
        :type strict: bool

        :return: The battle order for the given action in context of the current battle.
        :rtype: BattleOrder
        """
        import logging
        logger = logging.getLogger("poke_env.singles_env")
        logger.debug(f"action_to_order called with action={action}, battle.finished={getattr(battle, 'finished', None)}")
        # Prevent invalid actions if the battle is finished
        if hasattr(battle, 'finished') and battle.finished:
            logger.info("Returning DefaultBattleOrder: battle is finished.")
            return DefaultBattleOrder()
        try:
            if action == -2:
                logger.info("Returning DefaultBattleOrder: action == -2 (default action)")
                return DefaultBattleOrder()
            elif action == -1:
                logger.info("Returning ForfeitBattleOrder: action == -1 (forfeit action)")
                return ForfeitBattleOrder()
            elif action < 6:
                order = Player.create_order(list(battle.team.values())[action])
                if not fake:
                    if battle.trapped:
                        logger.warning(f"Invalid switch action: Pokemon is trapped. action={action}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid switch (trapped)")
                            return DefaultBattleOrder()
                        assert not battle.trapped, "invalid action"
                    if not isinstance(order.order, Pokemon):
                        logger.warning(f"Invalid switch action: order is not a Pokemon. action={action}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid switch (not a Pokemon)")
                            return DefaultBattleOrder()
                        assert isinstance(order.order, Pokemon)
                    if order.order.base_species not in [p.base_species for p in battle.available_switches]:
                        logger.warning(f"Invalid switch action: base_species not in available_switches. action={action}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid switch (not available)")
                            return DefaultBattleOrder()
                        assert order.order.base_species in [
                            p.base_species for p in battle.available_switches
                        ], "invalid action"
            else:
                if not fake:
                    if battle.force_switch:
                        logger.warning(f"Invalid move action: force_switch is True. action={action}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid move (force_switch)")
                            return DefaultBattleOrder()
                        assert not battle.force_switch, "invalid action"
                    if battle.active_pokemon is None:
                        logger.warning(f"Invalid move action: active_pokemon is None. action={action}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid move (no active_pokemon)")
                            return DefaultBattleOrder()
                        assert battle.active_pokemon is not None, "invalid action"
                elif battle.active_pokemon is None:
                    logger.info("Returning DefaultBattleOrder: battle.active_pokemon is None")
                    return DefaultBattleOrder()
                mvs = (
                    battle.available_moves
                    if len(battle.available_moves) == 1
                    and battle.available_moves[0].id in ["struggle", "recharge"]
                    else list(battle.active_pokemon.moves.values())
                )
                if not fake:
                    if (action - 6) % 4 not in range(len(mvs)):
                        logger.warning(f"Invalid move action: move index out of range. action={action}, len(mvs)={len(mvs)}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid move (index out of range)")
                            return DefaultBattleOrder()
                        assert (action - 6) % 4 in range(len(mvs)), "invalid action"
                elif (action - 6) % 4 not in range(len(mvs)):
                    logger.info("Returning DefaultBattleOrder: move index out of range")
                    return DefaultBattleOrder()
                order = Player.create_order(
                    mvs[(action - 6) % 4],
                    mega=10 <= action.item() < 14,
                    z_move=14 <= action.item() < 18,
                    dynamax=18 <= action.item() < 22,
                    terastallize=22 <= action.item() < 26,
                )
                if not fake:
                    if not isinstance(order.order, Move):
                        logger.warning(f"Invalid move action: order is not a Move. action={action}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid move (not a Move)")
                            return DefaultBattleOrder()
                        assert isinstance(order.order, Move)
                    if order.order.id not in [m.id for m in battle.available_moves]:
                        logger.warning(f"Invalid move action: move id not in available_moves. action={action}, move_id={order.order.id}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid move (id not available)")
                            return DefaultBattleOrder()
                        assert order.order.id in [
                            m.id for m in battle.available_moves
                        ], "invalid action"
                    if order.mega and not battle.can_mega_evolve:
                        logger.warning(f"Invalid move action: tried mega evolve when not available. action={action}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid move (mega evolve not available)")
                            return DefaultBattleOrder()
                        assert not order.mega or battle.can_mega_evolve, "invalid action"
                    if order.z_move and not (battle.can_z_move and order.order in battle.active_pokemon.available_z_moves):
                        logger.warning(f"Invalid move action: tried z-move when not available. action={action}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid move (z-move not available)")
                            return DefaultBattleOrder()
                        assert not order.z_move or (
                            battle.can_z_move
                            and order.order in battle.active_pokemon.available_z_moves
                        ), "invalid action"
                    if order.dynamax and not battle.can_dynamax:
                        logger.warning(f"Invalid move action: tried dynamax when not available. action={action}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid move (dynamax not available)")
                            return DefaultBattleOrder()
                        assert not order.dynamax or battle.can_dynamax, "invalid action"
                    if order.terastallize and not (battle.can_tera is not None):
                        logger.warning(f"Invalid move action: tried terastallize when not available. action={action}")
                        if not strict:
                            logger.info("Returning DefaultBattleOrder: invalid move (terastallize not available)")
                            return DefaultBattleOrder()
                        assert (
                            not order.terastallize or battle.can_tera is not None
                        ), "invalid action"
            return order
        except AssertionError as e:
            logger.error(f"AssertionError in action_to_order: {e}, action={action}")
            if not strict and str(e) == "invalid action":
                logger.info("Returning DefaultBattleOrder: assertion error and not strict mode")
                return DefaultBattleOrder()
            else:
                raise e

    @staticmethod
    def order_to_action(
        order: BattleOrder, battle: Battle, fake: bool = False, strict: bool = True
    ) -> np.int64:
        """
        Returns the action relative to the given BattleOrder.

        :param order: The order to take.
        :type order: BattleOrder
        :param battle: The current battle state
        :type battle: AbstractBattle
        :param fake: If true, action-order converters will try to avoid returning a default
            output if at all possible, even if the output isn't a legal decision. Defaults
            to False.
        :type fake: bool
        :param strict: If true, action-order converters will throw an error if the move is
            illegal. Otherwise, it will return default. Defaults to True.
        :type strict: bool

        :return: The action for the given battle order in context of the current battle.
        :rtype: int64
        """
        try:
            if isinstance(order, DefaultBattleOrder):
                action = -2
            elif isinstance(order, ForfeitBattleOrder):
                action = -1
            elif order.order is None:
                raise ValueError()
            elif isinstance(order.order, Pokemon):
                if not fake:
                    assert not battle.trapped, "invalid order"
                    assert order.order.base_species in [
                        p.base_species for p in battle.available_switches
                    ], "invalid order"
                action = [p.base_species for p in battle.team.values()].index(
                    order.order.base_species
                )
            else:
                if not fake:
                    assert not battle.force_switch, "invalid order"
                    assert battle.active_pokemon is not None, "invalid order"
                elif battle.active_pokemon is None:
                    return np.int64(-2)
                mvs = (
                    battle.available_moves
                    if len(battle.available_moves) == 1
                    and battle.available_moves[0].id in ["struggle", "recharge"]
                    else list(battle.active_pokemon.moves.values())
                )
                if not fake:
                    assert order.order.id in [m.id for m in mvs], "invalid order"
                action = [m.id for m in mvs].index(order.order.id)
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
                action = 6 + action + 4 * gimmick
                if not fake:
                    assert order.order.id in [
                        m.id for m in battle.available_moves
                    ], "invalid order"
                    assert not order.mega or battle.can_mega_evolve, "invalid order"
                    assert not order.z_move or (
                        battle.can_z_move
                        and order.order in battle.active_pokemon.available_z_moves
                    ), "invalid order"
                    assert not order.dynamax or battle.can_dynamax, "invalid order"
                    assert (
                        not order.terastallize or battle.can_tera is not None
                    ), "invalid order"
            return np.int64(action)
        except AssertionError as e:
            if not strict and str(e) == "invalid order":
                return np.int64(-2)
            else:
                raise e
