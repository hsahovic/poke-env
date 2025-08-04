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

    def __eq__(self, other) -> bool:
        if (
            self.mega != other.mega
            or self.dynamax != other.dynamax
            or self.terastallize != other.terastallize
            or self.move_target != other.move_target
            or type(self.order) is not type(other.order)
        ):
            return False
        if isinstance(self.order, str):
            return self.order == other.order
        elif isinstance(self.order, Pokemon):
            return self.order.species == other.order.species
        else:
            return self.order.id == other.order.id


class PassBattleOrder(SingleBattleOrder):
    def __init__(self):
        super().__init__("/choose pass")

    def __eq__(self, other) -> bool:
        return type(self) is type(other)


@dataclass
class DoubleBattleOrder(BattleOrder):
    first_order: SingleBattleOrder = field(default_factory=PassBattleOrder)
    second_order: SingleBattleOrder = field(default_factory=PassBattleOrder)

    @property
    def message(self) -> str:
        return f"{self.first_order.message}, {self.second_order.message[8:]}"

    def __eq__(self, other) -> bool:
        return (
            self.first_order == other.first_order
            and self.second_order == other.second_order
        )

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

    def __eq__(self, other) -> bool:
        return type(self) is type(other)
