# -*- coding: utf-8 -*-
from poke_env.data import MOVES
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.status import Status
from poke_env.environment.weather import Weather
from poke_env.exceptions import ShowdownException
from poke_env.utils import to_id_str

from functools import lru_cache
from typing import Dict
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union


special_moves: Dict


class Move:
    MISC_FLAGS = [
        "onModifyMove",
        "onEffectiveness",
        "onHitField",
        "onAfterMoveSecondarySelf",
        "onHit",
        "onTry",
        "beforeTurnCallback",
        "onAfterMove",
        "onTryHit",
        "onTryMove",
        "hasCustomRecoil",
        "onMoveFail",
        "onPrepareHit",
        "onAfterHit",
        "onBasePower",
        "basePowerCallback",
        "damageCallback",
        "onTryHitSide",
        "beforeMoveCallback",
    ]

    def __init__(self, move: str = "", move_id: Optional[str] = None):
        if move_id:
            self._id = move_id
        else:
            self._id: str = self.retrieve_id(move)
        self._current_pp = self.max_pp

    def __repr__(self) -> str:
        return f"{self._id} (Move object)"

    def use(self) -> None:
        self._current_pp -= 1

    @property
    def accuracy(self) -> float:
        accuracy = self.entry["accuracy"]
        if isinstance(accuracy, int):
            return accuracy / 100
        if accuracy is True:
            return 1
        raise ShowdownException("Unmanaged accuracy: %s", accuracy)

    @property
    def base_power(self) -> int:
        return self.entry["basePower"]

    @property
    def boosts(self) -> Optional[Dict[str, float]]:
        return self.entry.get("boosts", None)

    @property
    def breaks_protect(self) -> bool:
        return self.entry.get("breaksProtect", False)

    @property
    def can_z_move(self) -> bool:
        return bool(self.z_move_boost or self.z_move_power or self.z_move_effect)

    @property
    def category(self) -> MoveCategory:
        return MoveCategory[self.entry["category"].upper()]

    @property
    def crit_ratio(self) -> int:
        if "critRatio" in self.entry:
            return int(self.entry["critRatio"])
        elif "willCrit" in self.entry:
            return 6
        return 0

    @property
    def current_pp(self) -> int:
        return self._current_pp

    @property
    def damage(self) -> Union[int, str]:
        return self.entry.get("damage", 0)

    @property
    def defensive_category(self) -> MoveCategory:
        if "defensiveCategory" in self.entry:
            return MoveCategory[self.entry["defensiveCategory"].upper()]
        return self.category

    @property
    def drain(self) -> float:
        if "drain" in self.entry:
            return self.entry["drain"][0] / self.entry["drain"][1]
        return 0

    @property
    def entry(self) -> Dict:
        if self._id in MOVES:
            return MOVES[self._id]
        elif self._id.startswith("z") and self._id[1:] in MOVES:
            return MOVES[self._id[1:]]
        else:
            raise ValueError("Unknown move: %s" % self._id)

    @property
    def flags(self) -> Set[str]:
        flags = set(self.entry["flags"])
        flags.update(set(self.entry.keys()).intersection(self.MISC_FLAGS))
        return flags

    @property
    def force_switch(self) -> bool:
        return self.entry.get("forceSwitch", False)

    @property
    def heal(self) -> float:
        if "heal" in self.entry:
            return self.entry["heal"][0] / self.entry["heal"][1]
        return 0

    @property
    def id(self) -> str:
        return self._id

    @property
    def ignore_ability(self) -> bool:
        return self.entry.get("ignoreAbility", False)

    @property
    def ignore_defensive(self) -> bool:
        return self.entry.get("ignoreDefensive", False)

    @property
    def ignore_evasion(self) -> bool:
        return self.entry.get("ignoreEvasion", False)

    @property
    def ignore_immunity(self) -> bool:
        return self.entry.get("ignoreImmunity", False)

    @property
    def is_z(self) -> bool:
        return self.entry.get("isZ", False)

    @property
    def max_pp(self) -> int:
        return self.entry["pp"]

    @property
    def n_hit(self) -> Tuple[int, int]:
        if "multihit" in self.entry:
            if isinstance(self.entry["multihit"], list):
                return (self.entry["multihit"][0], self.entry["multihit"][1])
            else:
                return (self.entry["multihit"], self.entry["multihit"])
        return (1, 1)

    @property
    def no_pp_boosts(self) -> bool:
        return "noPPBoosts" in self.entry

    @property
    def non_ghost_target(self) -> bool:
        return "nonGhostTarget" in self.entry

    @property
    def priority(self) -> int:
        return self.entry["priority"]

    @property
    def pseudo_weather(self) -> str:
        return self.entry.get("pseudoWeather", None)

    @property
    def recoil(self) -> float:
        if "recoil" in self.entry:
            return self.entry["recoil"] / self.entry["recoil"][1]
        elif "struggleRecoil" in self.entry:
            return 0.25
        return 0

    @staticmethod
    @lru_cache(maxsize=4096)
    def retrieve_id(move_name) -> str:
        move_name = to_id_str(move_name)
        if move_name.startswith("hiddenpower"):
            return "hiddenpower"
        if move_name.startswith("return"):
            return "return"
        return move_name

    @property
    def secondary(self):
        if "secondary" in self.entry:
            return self.entry["secondary"]
        if "secondaries" in self.entry:
            return self.entry["secondaries"]
        return None

    @property
    def self_boost(self) -> Dict:
        return self.entry.get("selfBoost", None)

    @property
    def self_destruct(self) -> bool:
        return self.entry.get("selfdestruct", False)

    @property
    def self_switch(self) -> bool:
        return self.entry.get("selfSwitch", False)

    @staticmethod
    def should_be_stored(move_id) -> bool:
        if move_id not in special_moves:
            return True
        else:
            return False

    @property
    def side_condition(self) -> str:
        return self.entry.get("sideCondition", None)

    @property
    def sleep_usable(self) -> bool:
        return self.entry.get("sleepUsable", False)

    @property
    def slot_condition(self) -> str:
        return self.entry.get("slotCondition", False)

    @property
    def stalling_move(self) -> bool:
        return self.entry.get("stallingMove", False)

    @property
    def status(self) -> Optional[Status]:
        if "status" in self.entry:
            return Status(self.entry["status"].upper())
        return None

    @property
    def steals_boosts(self) -> bool:
        return self.entry.get("stealsBoosts", False)

    @property
    def target(self) -> str:
        return self.entry["target"]

    @property
    def terrain(self) -> Optional[str]:
        return self.entry.get("terrain", None)

    @property
    def thaws_target(self) -> bool:
        return self.entry.get("thawsTarget", False)

    @property
    def type(self) -> PokemonType:
        return PokemonType[self.entry["type"].upper()]

    @property
    def use_target_offensive(self) -> bool:
        return self.entry.get("useTargetOffensive", False)

    @property
    def volatile_status(self) -> str:
        return self.entry.get("volatileStatus", None)

    @property
    def weather(self) -> Optional[Weather]:
        if "weather" in self.entry:
            return Weather(self.entry["weather"].upper())
        return None

    @property
    def z_move_boost(self) -> Dict:
        return self.entry.get("zMoveBoost", None)

    @property
    def z_move_effect(self) -> str:
        return self.entry.get("zMoveEffect", None)

    @property
    def z_move_power(self) -> int:
        return self.entry.get("zMovePower", None)


class EmptyMove(Move):
    def __init__(self, move_id):
        self._id: str = move_id

    # def __getattr__(self, name):
    # return 0

    def __getattribute__(self, name):
        try:
            return super(Move, self).__getattribute__(name)
        except (ValueError, TypeError):
            return 0


special_moves = {"struggle": Move("struggle"), "recharge": EmptyMove("recharge")}
