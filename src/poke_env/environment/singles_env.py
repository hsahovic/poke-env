from typing import Any, Optional, Union

import numpy as np
from gymnasium.spaces import Discrete, Space

from poke_env.battle import Battle, Move, Pokemon
from poke_env.battle.move import SPECIAL_MOVES
from poke_env.data import GenData
from poke_env.environment.env import PokeEnv
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


class SinglesEnv(PokeEnv[np.int64]):
    def __init__(
        self,
        *,
        account_configuration1: Optional[AccountConfiguration] = None,
        account_configuration2: Optional[AccountConfiguration] = None,
        avatar: Optional[int] = None,
        battle_format: str = "gen9randombattle",
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
        choose_on_teampreview: bool = True,
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
            choose_on_teampreview=choose_on_teampreview,
            fake=fake,
            strict=strict,
        )
        gen = GenData.from_format(battle_format).gen
        self.action_spaces: dict[str, Space[Any]] = {
            agent: Discrete(SinglesEnv.get_action_space_size(gen))
            for agent in self.possible_agents
        }

    @staticmethod
    def get_move_slots(battle: Battle) -> tuple[Move, ...]:
        active = battle.active_pokemon
        known_moves = tuple(active.moves.values()) if active is not None else ()
        if (
            len(battle.available_moves) == 1
            and battle.available_moves[0].id in SPECIAL_MOVES
        ):
            return tuple(battle.available_moves)
        if battle.gen == 1 and battle.last_request.get("active"):
            moves = {move.id: move for move in known_moves}
            moves.update((move.id, move) for move in battle.available_moves)
            return tuple(
                (
                    moves[entry["id"]]
                    if entry["id"] in moves
                    else Move(entry["id"], gen=battle.gen)
                )
                for entry in battle.last_request["active"][0]["moves"][:4]
            )
        slots = known_moves[:4]
        if len(battle.available_moves) == 1 and battle.available_moves[0].id not in {
            move.id for move in slots
        }:
            return tuple(battle.available_moves)
        return slots

    @staticmethod
    def _action_targets(
        battle: Battle,
    ) -> tuple[Union[Move, Pokemon, DefaultBattleOrder, None], ...]:
        team = tuple(battle.team.values())
        active = battle.active_pokemon
        known_moves = SinglesEnv.get_move_slots(battle)
        available_moves = tuple(battle.available_moves)
        requested_moves = (
            battle.last_request.get("active", [{}])[0].get("moves", ())
            if battle.gen == 1
            else ()
        )
        disabled_slots = tuple(move.get("disabled", False) for move in requested_moves)
        if len(available_moves) == 1 and available_moves[0].id in SPECIAL_MOVES:
            disabled_slots = ()
        targets: list[Union[Move, Pokemon, DefaultBattleOrder, None]] = [
            None
        ] * SinglesEnv.get_action_space_size(battle.gen)
        if battle.wait:
            targets[0] = DefaultBattleOrder()
        else:
            if not battle.trapped:
                switches = set(battle.available_switches)
                for index, pokemon in enumerate(team[:6]):
                    if pokemon in switches:
                        targets[index] = pokemon
            if active is not None and not battle.force_switch:
                available_ids = {move.id for move in available_moves}
                moves = known_moves
                z_move_ids = (
                    {move.id for move in active.available_z_moves}
                    if battle.can_z_move
                    else set()
                )
                for index, move in enumerate(moves):
                    if index < len(disabled_slots) and disabled_slots[index]:
                        continue
                    if move.id not in available_ids:
                        continue
                    targets[6 + index] = move
                    if battle.can_mega_evolve and 10 + index < len(targets):
                        targets[10 + index] = move
                    if (
                        battle.can_z_move
                        and move.id in z_move_ids
                        and 14 + index < len(targets)
                    ):
                        targets[14 + index] = move
                    if battle.can_dynamax and 18 + index < len(targets):
                        targets[18 + index] = move
                    if battle.can_tera and 22 + index < len(targets):
                        targets[22 + index] = move
        return tuple(targets)

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
            if not fake:
                targets = SinglesEnv._action_targets(battle)
                index = int(action)
                if 0 <= index < len(targets) and (target := targets[index]) is not None:
                    if isinstance(target, DefaultBattleOrder):
                        return DefaultBattleOrder()
                    move_slot = 0
                    if (
                        index >= 6
                        and battle.gen == 1
                        and (requested := battle.last_request.get("active"))
                    ):
                        moves = requested[0]["moves"]
                        if len({move["id"] for move in moves}) < len(moves):
                            move_slot = index - 5
                    return SingleBattleOrder(
                        target,
                        move_slot=move_slot,
                        mega=10 <= index < 14,
                        z_move=14 <= index < 18,
                        dynamax=18 <= index < 22,
                        terastallize=22 <= index < 26,
                    )
                raise ValueError(
                    f"Invalid action {action} from player {battle.player_username} "
                    f"in battle {battle.battle_tag}"
                )
            if action < 6:
                order = Player.create_order(list(battle.team.values())[action])
            else:
                if battle.active_pokemon is None:
                    raise ValueError(
                        f"Invalid order from player {battle.player_username} "
                        f"in battle {battle.battle_tag} - action specifies a "
                        f"move, but battle.active_pokemon is None!"
                    )
                mvs = SinglesEnv.get_move_slots(battle)
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
                if not fake:
                    targets = SinglesEnv._action_targets(battle)
                    if battle.gen == 1 and order.move_slot:
                        index = 5 + order.move_slot
                        if 0 <= index < len(targets) and targets[index] is order.order:
                            return np.int64(index)
                    if isinstance(order.order, Pokemon):
                        choices = enumerate(targets[:6])
                    else:
                        if order.mega:
                            gimmick = 4
                        elif order.z_move:
                            gimmick = 8
                        elif order.dynamax:
                            gimmick = 12
                        elif order.terastallize:
                            gimmick = 16
                        else:
                            gimmick = 0
                        choices = enumerate(
                            targets[6 + gimmick : 10 + gimmick], start=6 + gimmick
                        )
                    for index, target in choices:
                        if target is order.order and (
                            isinstance(target, Pokemon) or order.move_target == 0
                        ):
                            return np.int64(index)
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
                    mvs = SinglesEnv.get_move_slots(battle)
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

    @staticmethod
    def get_action_mask(battle: Battle) -> list[int]:
        return [
            1 if target is not None else 0
            for target in SinglesEnv._action_targets(battle)
        ]

    @staticmethod
    def get_action_space_size(gen: int) -> int:
        num_switches = 6
        num_moves = 4
        if gen == 6:
            num_gimmicks = 1
        elif gen == 7:
            num_gimmicks = 2
        elif gen == 8:
            num_gimmicks = 3
        elif gen == 9:
            num_gimmicks = 4
        else:
            num_gimmicks = 0
        return num_switches + num_moves * (num_gimmicks + 1)
