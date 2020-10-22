# -*- coding: utf-8 -*-
from poke_env.data import MOVES
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.status import Status
from poke_env.environment.weather import Weather
from poke_env.utils import to_id_str

from functools import lru_cache
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union


SPECIAL_MOVES: Dict


class Move:
    _MISC_FLAGS = [
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

    __slots__ = "_id", "_current_pp", "_is_empty"

    def __init__(self, move: str = "", move_id: Optional[str] = None):
        if move_id:
            self._id = move_id
        else:
            self._id: str = self.retrieve_id(move)
        self._current_pp = self.max_pp
        self._is_empty: bool = False

    def __repr__(self) -> str:
        return f"{self._id} (Move object)"

    def use(self) -> None:
        self._current_pp -= 1

    @staticmethod
    def is_id_z(id_) -> bool:
        if id_.startswith("z") and id_[1:] in MOVES:
            return True
        return "isZ" in MOVES[id_]

    @staticmethod
    @lru_cache(4096)
    def should_be_stored(move_id: str) -> bool:
        if move_id in SPECIAL_MOVES:
            return False
        if move_id not in MOVES:
            return False
        return not Move.is_id_z(move_id)

    @property
    def accuracy(self) -> float:
        """
        :return: The move's accuracy (0 to 1 scale).
        :rtype: float
        """
        accuracy = self.entry["accuracy"]
        if accuracy is True:
            return 1.0
        return accuracy / 100

    @property
    def base_power(self) -> int:
        """
        :return: The move's base power.
        :rtype: int
        """
        return self.entry.get("basePower", 0)

    @property
    def boosts(self) -> Optional[Dict[str, float]]:
        """
        :return: Boosts conferred to the target by using the move.
        :rtype: Optional[Dict[str, float]]
        """
        return self.entry.get("boosts", None)

    @property
    def breaks_protect(self) -> bool:
        """
        :return: Whether the move breaks proect-like defenses.
        :rtype: bool
        """
        return self.entry.get("breaksProtect", False)

    @property
    def can_z_move(self) -> bool:
        """
        :return: Wheter there exist a z-move version of this move.
        :rtype: bool
        """
        return self.id not in SPECIAL_MOVES

    @property
    def category(self) -> MoveCategory:
        """
        :return: The move category.
        :rtype: MoveCategory
        """
        return MoveCategory[self.entry["category"].upper()]

    @property
    def crit_ratio(self) -> int:
        """
        :return: The move's crit ratio. If the move is guaranteed to crit, returns 6.
        :rtype:
        """
        if "critRatio" in self.entry:
            return int(self.entry["critRatio"])
        elif "willCrit" in self.entry:
            return 6
        return 0

    @property
    def current_pp(self) -> int:
        """
        :return: Remaining PP.
        :rtype: int
        """
        return self._current_pp

    @property
    def damage(self) -> Union[int, str]:
        """
        :return: The move's fix damages. Can be an int or 'level' for moves such as
            Seismic Toss.
        :rtype: Union[int, str]
        """
        return self.entry.get("damage", 0)

    @property
    def defensive_category(self) -> MoveCategory:
        """
        :return: Move's defender category.
        :rtype: MoveCategory
        """
        if "defensiveCategory" in self.entry:
            return MoveCategory[self.entry["defensiveCategory"].upper()]
        return self.category

    @property
    def drain(self) -> float:
        """
        :return: Ratio of HP of inflicted damages, between 0 and 1.
        :rtype: float
        """
        if "drain" in self.entry:
            return self.entry["drain"][0] / self.entry["drain"][1]
        return 0.0

    @property
    def entry(self) -> dict:
        """
        Should not be used directly.

        :return: The data entry corresponding to the move
        :rtype: dict
        """
        if self._id in MOVES:
            return MOVES[self._id]
        elif self._id.startswith("z") and self._id[1:] in MOVES:
            return MOVES[self._id[1:]]
        else:
            raise ValueError("Unknown move: %s" % self._id)

    @property
    def expected_hits(self) -> float:
        """
        :return: Expected number of hits, between 1 and 5. Equal to n_hits if n_hits is
            constant.
        :rtype: float
        """

        if self._id == "triplekick" or self._id == "tripleaxel":
            # Triple Kick and Triple Axel have an accuracy check for each hit, and also
            # rise in BP for each hit
            return 1 + 2 * 0.9 + 3 * 0.81
        min_hits, max_hits = self.n_hit
        if min_hits == max_hits:
            return min_hits
        else:
            # It hits 2-5 times
            assert min_hits == 2 and max_hits == 5
            return (2 + 3) / 3 + (4 + 5) / 6

    @property
    def flags(self) -> Set[str]:
        """
        This property is not well defined, and may be missing some information.
        If you need more information on some flag, please open an issue in the project.

        :return: Flags associated with this move. These can come from the data or be
            custom.
        :rtype: Set[str]
        """
        flags = set(self.entry["flags"])
        flags.update(set(self.entry.keys()).intersection(self._MISC_FLAGS))
        return flags

    @property
    def force_switch(self) -> bool:
        """
        :return: Whether this move forces switches.
        :rtype: bool
        """
        return self.entry.get("forceSwitch", False)

    @property
    def heal(self) -> float:
        """
        :return: Proportion of the user's HP recovered.
        :rtype: float
        """
        if "heal" in self.entry:
            return self.entry["heal"][0] / self.entry["heal"][1]
        return 0.0

    @property
    def id(self) -> str:
        """
        :return: Move id.
        :rtype: str
        """
        return self._id

    @property
    def ignore_ability(self) -> bool:
        """
        :return: Whether the move ignore its target's ability.
        :rtype: bool
        """
        return self.entry.get("ignoreAbility", False)

    @property
    def ignore_defensive(self) -> bool:
        """
        :return: Whether the opponent's stat boosts are ignored.
        :rtype: bool
        """
        return self.entry.get("ignoreDefensive", False)

    @property
    def ignore_evasion(self) -> bool:
        """
        :return: Wheter the opponent's evasion is ignored.
        :rtype: bool
        """
        return self.entry.get("ignoreEvasion", False)

    @property
    def ignore_immunity(self) -> Union[bool, Set[PokemonType]]:
        """
        :return: Whether the opponent's immunity is ignored, or a list of ignored
            immunities.
        :rtype: bool or set of Types
        """
        if "ignoreImmunity" in self.entry:
            if isinstance(self.entry["ignoreImmunity"], bool):
                return self.entry["ignoreImmunity"]
            else:
                return {
                    PokemonType[t.upper().replace("'", "")]
                    for t in self.entry["ignoreImmunity"].keys()
                }
        return False

    @property
    def is_empty(self) -> bool:
        """
        :return: Whether the move is an empty move.
        :rtype: bool
        """
        return self._is_empty

    @property
    def is_z(self) -> bool:
        """
        :return: Whether the move is a z move.
        :rtype: bool
        """
        return Move.is_id_z(self.id)

    @property
    def max_pp(self) -> int:
        """
        :return: The move's max pp.
        :rtype: int
        """
        return self.entry["pp"]

    @property
    def n_hit(self) -> Tuple:
        """
        :return: How many hits this move lands. Tuple of the form (min, max).
        :rtype: Tuple
        """
        if "multihit" in self.entry:
            if isinstance(self.entry["multihit"], list):
                return tuple(self.entry["multihit"])
            else:
                return self.entry["multihit"], self.entry["multihit"]
        return 1, 1

    @property
    def no_pp_boosts(self) -> bool:
        """
        :return: Whether the move uses PPs.
        :rtype: bool
        """
        return "noPPBoosts" in self.entry

    @property
    def non_ghost_target(self) -> bool:
        """
        :return: True for curse.
        :rtype: bool
        """
        return "nonGhostTarget" in self.entry

    @property
    def priority(self) -> int:
        """
        :return: Move priority.
        :rtype: int
        """
        return self.entry["priority"]

    @property
    def pseudo_weather(self) -> str:
        """
        :return: Pseudo-weather activated by this move.
        :rtype: str
        """
        return self.entry.get("pseudoWeather", None)

    @property
    def recoil(self) -> float:
        """
        :return: Proportion of the move's damage inflicted as recoil.
        :rtype: float
        """
        if "recoil" in self.entry:
            return self.entry["recoil"][0] / self.entry["recoil"][1]
        elif "struggleRecoil" in self.entry:
            return 0.25
        return 0.0

    @staticmethod
    @lru_cache(maxsize=4096)
    def retrieve_id(move_name: str) -> str:
        """Retrieve the id of a move based on its full name.

        :param move_name: The string to convert into a move id.
        :type move_name: str
        :return: The corresponding move id.
        :rtype: str
        """
        move_name = to_id_str(move_name)
        if move_name.startswith("hiddenpower"):
            return "hiddenpower"
        if move_name.startswith("return"):
            return "return"
        if move_name.startswith("frustration"):
            return "frustration"
        return move_name

    @property
    def secondary(self) -> List[dict]:
        """
        :return: Secondary effects. At this point, the precise content of this property
            is not too clear.
        :rtype: Optional[Dict]
        """
        if "secondary" in self.entry and self.entry["secondary"]:
            return [self.entry["secondary"]]
        elif "secondaries" in self.entry:
            return self.entry["secondaries"]
        return []

    @property
    def self_boost(self) -> Optional[Dict[str, int]]:
        """
        :return: Boosts applied to the move's user.
        :rtype: Dict[str, int]
        """
        if "selfBoost" in self.entry:
            return self.entry["selfBoost"].get("boosts", None)
        elif "self" in self.entry and "boosts" in self.entry["self"]:
            return self.entry["self"]["boosts"]
        return None

    @property
    def self_destruct(self) -> Optional[str]:
        """
        :return: Move's self destruct consequences.
        :rtype: Optional[str]
        """
        return self.entry.get("selfdestruct", None)

    @property
    def self_switch(self) -> Union[str, bool]:
        """
        :return: What kind of self swtich this move implies for the user.
        :rtype: Optional[str]
        """
        return self.entry.get("selfSwitch", False)

    @property
    def side_condition(self) -> Optional[str]:
        """
        :return: Side condition inflicted by the move.
        :rtype: Optional[str]
        """
        return self.entry.get("sideCondition", None)

    @property
    def sleep_usable(self) -> bool:
        """
        :return: Whether the move can be user by a sleeping pokemon.
        :rtype: bool
        """
        return self.entry.get("sleepUsable", False)

    @property
    def slot_condition(self) -> Optional[str]:
        """
        :return: Which slot condition is started by this move.
        :rtype: Optional[str]
        """
        return self.entry.get("slotCondition", None)

    @property
    def stalling_move(self) -> bool:
        """
        :return: Showdown classification of the move as a stalling move.
        :rtype: bool
        """
        return self.entry.get("stallingMove", False)

    @property
    def status(self) -> Optional[Status]:
        """
        :return: The status inflicted by the move.
        :rtype: Optional[Status]
        """
        if "status" in self.entry:
            return Status[self.entry["status"].upper()]
        return None

    @property
    def steals_boosts(self) -> bool:
        """
        :return: Whether the move steals its target's boosts.
        :rtype: bool
        """
        return self.entry.get("stealsBoosts", False)

    @property
    def target(self) -> str:
        """
        :return: Move target.
        :rtype: str
        """
        return self.entry["target"]

    @property
    def terrain(self) -> Optional[str]:
        """
        :return: Terrain started by the move.
        :rtype: Optional[str]
        """
        return self.entry.get("terrain", None)

    @property
    def thaws_target(self) -> bool:
        """
        :return: Whether the move thaws its target.
        :rtype: bool
        """
        return self.entry.get("thawsTarget", False)

    @property
    def type(self) -> PokemonType:
        """
        :return: Move type.
        :rtype: PokemonType
        """
        return PokemonType[self.entry["type"].upper()]

    @property
    def use_target_offensive(self) -> bool:
        """
        :return: Whether the move uses the target's offensive statistics.
        :rtype: bool
        """
        return self.entry.get("useTargetOffensive", False)

    @property
    def volatile_status(self) -> Optional[str]:
        """
        :return: Volatile status inflicted by the move.
        :rtype: Optional[str]
        """
        return self.entry.get("volatileStatus", None)

    @property
    def weather(self) -> Optional[Weather]:
        """
        :return: Weather started by the move.
        :rtype: Optional[Weather]
        """
        if "weather" in self.entry:
            return Weather[self.entry["weather"].upper()]
        return None

    @property
    def z_move_boost(self) -> Optional[Dict[str, int]]:
        """
        :return: Boosts associated with the z-move version of this move.
        :rtype: Dict[str, int]
        """
        if "zMove" in self.entry and "boost" in self.entry["zMove"]:
            return self.entry["zMove"]["boost"]
        return None

    @property
    def z_move_effect(self) -> Optional[str]:
        """
        :return: Effects associated with the z-move version of this move.
        :rtype: Optional[str]
        """
        if "zMove" in self.entry and "effect" in self.entry["zMove"]:
            return self.entry["zMove"]["effect"]
        return None

    @property
    def z_move_power(self) -> int:
        """
        :return: Base power of the z-move version of this move.
        :rtype: int
        """
        if "zMove" in self.entry and "basePower" in self.entry["zMove"]:
            return self.entry["zMove"]["basePower"]
        elif self.category == MoveCategory.STATUS:
            return 0
        base_power = self.base_power
        if self.n_hit != (1, 1):
            base_power *= 3
        elif base_power <= 55:
            return 100
        elif base_power <= 65:
            return 120
        elif base_power <= 75:
            return 140
        elif base_power <= 85:
            return 160
        elif base_power <= 95:
            return 175
        elif base_power <= 100:
            return 180
        elif base_power <= 110:
            return 185
        elif base_power <= 125:
            return 190
        elif base_power <= 130:
            return 195
        return 200


class EmptyMove(Move):
    def __init__(self, move_id):
        self._id: str = move_id
        self._is_empty: bool = True

    def __getattribute__(self, name):
        try:
            return super(Move, self).__getattribute__(name)
        except (AttributeError, TypeError, ValueError):
            return 0


SPECIAL_MOVES = {"struggle": Move("struggle"), "recharge": EmptyMove("recharge")}
