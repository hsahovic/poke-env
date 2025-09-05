from typing import Optional, Union

import numpy as np
from gymnasium.spaces import Discrete

from poke_env.battle import Battle, Pokemon
from poke_env.environment.env import ObsType, PokeEnv
from poke_env.player.battle_order import (
    BattleOrder,
    DefaultBattleOrder,
    ForfeitBattleOrder,
    SingleBattleOrder,
)
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
        challenge_timeout: Optional[float] = 60.0,
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
            challenge_timeout=challenge_timeout,
            team=team,
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
        try:
            if action == -2:
                return DefaultBattleOrder()
            elif action == -1:
                return ForfeitBattleOrder()
            elif action < 6:
                order = Player.create_order(list(battle.team.values())[action])
            else:
                if battle.active_pokemon is None:
                    raise ValueError(
                        f"Invalid order from player {battle.player_username} "
                        f"in battle {battle.battle_tag} - action specifies a "
                        f"move, but battle.active_pokemon is None!"
                    )
                mvs = (
                    battle.available_moves
                    if len(battle.available_moves) == 1
                    and battle.available_moves[0].id in ["struggle", "recharge"]
                    else list(battle.active_pokemon.moves.values())
                )
                if (action - 6) % 4 not in range(len(mvs)):
                    raise ValueError(
                        f"Invalid action {action} from player {battle.player_username} "
                        f"in battle {battle.battle_tag} - action specifies a move "
                        f"but the move index {(action - 6) % 4} is out of bounds "
                        f"for available moves {mvs}!"
                    )
                order = Player.create_order(
                    mvs[(action - 6) % 4],
                    mega=10 <= action.item() < 14,
                    z_move=14 <= action.item() < 18,
                    dynamax=18 <= action.item() < 22,
                    terastallize=22 <= action.item() < 26,
                )
            if not fake and str(order) not in [str(o) for o in battle.valid_orders]:
                raise ValueError(
                    f"Invalid action {action} from player {battle.player_username} "
                    f"in battle {battle.battle_tag} - converted order {order} "
                    f"not in valid orders {[str(o) for o in battle.valid_orders]}!"
                )
            return order
        except ValueError as e:
            if strict:
                raise e
            else:
                if battle.logger is not None:
                    battle.logger.warning(str(e) + " Defaulting to random move.")
                return Player.choose_random_singles_move(battle)

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
            else:
                assert isinstance(order, SingleBattleOrder)
                assert not isinstance(order.order, str)
                if not fake and str(order) not in [str(o) for o in battle.valid_orders]:
                    raise ValueError(
                        f"Invalid order from player {battle.player_username} "
                        f"in battle {battle.battle_tag} - order {order} "
                        f"not in valid orders {[str(o) for o in battle.valid_orders]}!"
                    )
                if isinstance(order.order, Pokemon):
                    action = [p.base_species for p in battle.team.values()].index(
                        order.order.base_species
                    )
                else:
                    assert battle.active_pokemon is not None
                    mvs = (
                        battle.available_moves
                        if len(battle.available_moves) == 1
                        and battle.available_moves[0].id in ["struggle", "recharge"]
                        else list(battle.active_pokemon.moves.values())
                    )
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
            return np.int64(action)
        except ValueError as e:
            if strict:
                raise e
            else:
                if battle.logger is not None:
                    battle.logger.warning(str(e) + " Defaulting to random move.")
                return SinglesEnv.order_to_action(
                    Player.choose_random_singles_move(battle), battle, fake, strict
                )
