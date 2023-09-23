from dataclasses import dataclass
from typing import Any, List, Optional, Union

from poke_env.environment.double_battle import DoubleBattle
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon


@dataclass
class BattleOrder:
    order: Optional[Union[Move, Pokemon]]
    mega: bool = False
    z_move: bool = False
    dynamax: bool = False
    terastallize: bool = False
    move_target: int = DoubleBattle.EMPTY_TARGET_POSITION

    DEFAULT_ORDER = "/choose default"

    def __str__(self) -> str:
        return self.message

    @property
    def message(self) -> str:
        if isinstance(self.order, Move):
            if self.order.id == "recharge":
                return "/choose move 1"

            message = f"/choose move {self.order.id}"
            if self.mega:
                message += " mega"
            elif self.z_move:
                message += " zmove"
            elif self.dynamax:
                message += " dynamax"
            elif self.terastallize:
                message += " terastallize"

            if self.move_target != DoubleBattle.EMPTY_TARGET_POSITION:
                message += f" {self.move_target}"
            return message
        elif isinstance(self.order, Pokemon):
            return f"/choose switch {self.order.species}"
        else:
            return ""


class DefaultBattleOrder(BattleOrder):
    def __init__(self, *args: Any, **kwargs: Any):
        pass

    @property
    def message(self) -> str:
        return self.DEFAULT_ORDER


@dataclass
class DoubleBattleOrder(BattleOrder):
    def __init__(
        self,
        first_order: Optional[BattleOrder] = None,
        second_order: Optional[BattleOrder] = None,
    ):
        self.first_order = first_order
        self.second_order = second_order

    @property
    def message(self) -> str:
        if self.first_order and self.second_order:
            return (
                self.first_order.message
                + ", "
                + self.second_order.message.replace("/choose ", "")
            )
        elif self.first_order:
            return self.first_order.message + ", default"
        elif self.second_order:
            return self.second_order.message + ", default"
        else:
            return self.DEFAULT_ORDER

    @staticmethod
    def join_orders(first_orders: List[BattleOrder], second_orders: List[BattleOrder]):
        if first_orders and second_orders:
            orders = [
                DoubleBattleOrder(first_order=first_order, second_order=second_order)
                for first_order in first_orders
                for second_order in second_orders
                if not first_order.mega or not second_order.mega
                if not first_order.z_move or not second_order.z_move
                if not first_order.dynamax or not second_order.dynamax
                if not first_order.terastallize or not second_order.terastallize
                if first_order.order != second_order.order
            ]
            if orders:
                return orders
        elif first_orders:
            return [DoubleBattleOrder(first_order=order) for order in first_orders]
        elif second_orders:
            return [DoubleBattleOrder(first_order=order) for order in second_orders]
        return [DefaultBattleOrder()]


class ForfeitBattleOrder(BattleOrder):
    def __init__(self, *args: Any, **kwargs: Any):
        pass

    @property
    def message(self) -> str:
        return "/forfeit"
