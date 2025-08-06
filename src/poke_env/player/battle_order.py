from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import List, Union

from poke_env.battle.move import Move
from poke_env.battle.pokemon import Pokemon


class BattleOrder:
    def __str__(self) -> str:
        return self.message

    @property
    @abstractmethod
    def message(self) -> str:
        pass

    def __eq__(self, other) -> bool:
        return type(self) is type(other) and self.message == other.message


class ForfeitBattleOrder(BattleOrder):
    @property
    def message(self) -> str:
        return "/forfeit"


@dataclass
class SingleBattleOrder(BattleOrder):
    order: Union[Move, Pokemon, str]
    mega: bool = False
    z_move: bool = False
    dynamax: bool = False
    terastallize: bool = False
    move_target: int = 0

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

            if self.move_target != 0:
                message += f" {self.move_target}"
            return message
        elif isinstance(self.order, Pokemon):
            return f"/choose switch {self.order.species}"
        else:
            return self.order


class PassBattleOrder(SingleBattleOrder):
    def __init__(self):
        super().__init__("/choose pass")


@dataclass
class DoubleBattleOrder(BattleOrder):
    first_order: SingleBattleOrder = field(default_factory=PassBattleOrder)
    second_order: SingleBattleOrder = field(default_factory=PassBattleOrder)

    @property
    def message(self) -> str:
        return f"{self.first_order.message}, {self.second_order.message[8:]}"

    @staticmethod
    def join_orders(
        first_orders: List[SingleBattleOrder], second_orders: List[SingleBattleOrder]
    ) -> List[DoubleBattleOrder]:
        return [
            DoubleBattleOrder(first_order=first_order, second_order=second_order)
            for first_order in first_orders or [PassBattleOrder()]
            for second_order in second_orders or [PassBattleOrder()]
            if not (first_order.mega and second_order.mega)
            if not (first_order.z_move and second_order.z_move)
            if not (first_order.dynamax and second_order.dynamax)
            if not (first_order.terastallize and second_order.terastallize)
            if not (
                isinstance(first_order.order, Pokemon)
                and isinstance(second_order.order, Pokemon)
                and str(first_order) == str(second_order)
            )
            if not (
                isinstance(first_order, PassBattleOrder)
                and isinstance(second_order, PassBattleOrder)
            )
        ]


class DefaultBattleOrder(SingleBattleOrder, DoubleBattleOrder):
    def __init__(self):
        super().__init__("/choose default")
