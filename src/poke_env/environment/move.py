import copy
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from poke_env.data import GenData, to_id_str
from poke_env.environment.field import Field
from poke_env.environment.move_category import MoveCategory
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.status import Status
from poke_env.environment.weather import Weather

SPECIAL_MOVES: Set[str] = {"struggle", "recharge"}

_PROTECT_MOVES = {
    "protect",
    "detect",
    "endure",
    "spikyshield",
    "kingsshield",
    "banefulbunker",
    "obstruct",
    "maxguard",
}
_SIDE_PROTECT_MOVES = {"wideguard", "quickguard", "matblock"}
_PROTECT_COUNTER_MOVES = _PROTECT_MOVES | _SIDE_PROTECT_MOVES


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

    _MOVE_CATEGORY_PER_TYPE_PRE_SPLIT = {
        PokemonType.BUG: MoveCategory.PHYSICAL,
        PokemonType.DARK: MoveCategory.SPECIAL,
        PokemonType.DRAGON: MoveCategory.SPECIAL,
        PokemonType.ELECTRIC: MoveCategory.SPECIAL,
        PokemonType.FIGHTING: MoveCategory.PHYSICAL,
        PokemonType.FIRE: MoveCategory.SPECIAL,
        PokemonType.FLYING: MoveCategory.PHYSICAL,
        PokemonType.GHOST: MoveCategory.PHYSICAL,
        PokemonType.GRASS: MoveCategory.SPECIAL,
        PokemonType.GROUND: MoveCategory.PHYSICAL,
        PokemonType.ICE: MoveCategory.SPECIAL,
        PokemonType.NORMAL: MoveCategory.PHYSICAL,
        PokemonType.POISON: MoveCategory.PHYSICAL,
        PokemonType.PSYCHIC: MoveCategory.SPECIAL,
        PokemonType.ROCK: MoveCategory.PHYSICAL,
        PokemonType.STEEL: MoveCategory.PHYSICAL,
        PokemonType.WATER: MoveCategory.SPECIAL,
    }

    __slots__ = (
        "_id",
        "_base_power_override",
        "_current_pp",
        "_dynamaxed_move",
        "_gen",
        "_is_empty",
        "_moves_dict",
        "_request_target",
    )

    def __init__(self, move_id: str, gen: int, raw_id: Optional[str] = None):
        self._id = move_id
        self._base_power_override = None
        self._gen = gen
        self._moves_dict = GenData.from_gen(gen).moves

        if move_id.startswith("hiddenpower") and raw_id is not None:
            base_power = "".join([c for c in raw_id if c.isdigit()])
            self._id = "".join([c for c in to_id_str(raw_id) if not c.isdigit()])

            if base_power:
                try:
                    base_power = int(base_power)
                    self._base_power_override = base_power
                except ValueError:
                    pass

        self._current_pp = self.max_pp
        self._is_empty: bool = False

        self._dynamaxed_move = None
        self._request_target = None

    def __repr__(self) -> str:
        return f"{self._id} (Move object)"

    def use(self):
        self._current_pp -= 1

    @staticmethod
    def is_id_z(id_: str, gen: int) -> bool:
        move_data = GenData.from_gen(gen).moves
        if id_.startswith("z") and id_[1:] in move_data:
            return True
        elif id_ in move_data:
            return "isZ" in move_data[id_]
        return False

    @staticmethod
    def is_max_move(id_: str, gen: int) -> bool:
        if id_.startswith("max"):
            return True
        elif (
            GenData.from_gen(gen).moves[id_].get("isNonstandard", None) == "Gigantamax"
        ):
            return True
        elif GenData.from_gen(gen).moves[id_].get("isMax", None) is not None:
            return True
        return False

    @staticmethod
    @lru_cache(4096)
    def should_be_stored(move_id: str, gen: int) -> bool:
        if move_id in SPECIAL_MOVES:
            return False
        if move_id not in GenData.from_gen(gen).moves:
            return False
        if Move.is_id_z(move_id, gen):
            return False
        if Move.is_max_move(move_id, gen):
            return False
        return True

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
        if self._base_power_override is not None:
            return self._base_power_override
        return self.entry.get("basePower", 0)

    @property
    def boosts(self) -> Optional[Dict[str, int]]:
        """
        :return: Boosts conferred to the target by using the move.
        :rtype: Dict[str, float] | None
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
        if "category" not in self.entry:
            print(self, self.entry)

        if self._gen <= 3 and self.entry["category"].upper() in {
            "PHYSICAL",
            "SPECIAL",
        }:
            return self._MOVE_CATEGORY_PER_TYPE_PRE_SPLIT[self.type]
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
    def deduced_target(self) -> Optional[str]:
        """
        :return: Move deduced target, based on Move.target and showdown's request
            messages.
        :rtype: str, optional
        """
        if self.id in SPECIAL_MOVES:
            return self.target
        elif self.request_target:
            return self.request_target
        elif self.target == "randomNormal":
            return self.request_target
        return self.target

    @property
    def defensive_category(self) -> MoveCategory:
        """
        :return: Move's defender category.
        :rtype: MoveCategory
        """
        if "overrideDefensiveStat" in self.entry:
            if self.entry["overrideDefensiveStat"] == "def":
                return MoveCategory["PHYSICAL"]
            elif self.entry["overrideDefensiveStat"] == "spd":
                return MoveCategory["SPECIAL"]
            else:
                raise ValueError(
                    f"Unsupported value for overrideDefensiveStat: {self.entry['overrideDefensiveStat']}"
                )
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
    def dynamaxed(self):
        """
        :return: The dynamaxed version of the move.
        :rtype: DynamaxMove
        """
        if self._dynamaxed_move:
            return self._dynamaxed_move

        self._dynamaxed_move = DynamaxMove(self)
        return self._dynamaxed_move

    @property
    def entry(self) -> Dict[str, Any]:
        """
        Should not be used directly.

        :return: The data entry corresponding to the move
        :rtype: Dict
        """
        if self._id in self._moves_dict:
            return self._moves_dict[self._id]
        elif self._id.startswith("z") and self._id[1:] in self._moves_dict:
            return self._moves_dict[self._id[1:]]
        elif self._id == "recharge":
            return {"pp": 1, "type": "normal", "category": "Special", "priority" : 0, "target" : "self", "accuracy": 1}
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
            assert (
                min_hits == 2 and max_hits == 5
            ), f"Move {self._id} expected to hit 2-5 times. Got {min_hits}-{max_hits}"
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
    def is_protect_counter(self) -> bool:
        """
        :return: Wheter this move increments a mon's protect counter.
        :rtype: int
        """
        return self._id in _PROTECT_COUNTER_MOVES

    @property
    def is_protect_move(self) -> bool:
        """
        :return: Wheter this move is a protect-like move.
        :rtype: int
        """
        return self._id in _PROTECT_MOVES

    @property
    def is_side_protect_move(self) -> bool:
        """
        :return: Wheter this move is a side-protect move.
        :rtype: int
        """
        return self._id in _SIDE_PROTECT_MOVES

    @property
    def is_z(self) -> bool:
        """
        :return: Whether the move is a z move.
        :rtype: bool
        """
        return Move.is_id_z(self.id, gen=self._gen)

    @property
    def max_pp(self) -> int:
        """
        :return: The move's max pp.
        :rtype: int
        """
        return self.entry["pp"] * 8 // 5

    @property
    def n_hit(self) -> Tuple[int, int]:
        """
        :return: How many hits this move lands. Tuple of the form (min, max).
        :rtype: Tuple
        """
        if "multihit" in self.entry:
            if isinstance(self.entry["multihit"], list):
                assert len(self.entry["multihit"]) == 2
                min_hits, max_hits = self.entry["multihit"]
                return min_hits, max_hits
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

    @property
    def request_target(self) -> Optional[str]:
        """
        :return: Target information sent by showdown in a request message, if any.
        :rtype: str, optional
        """
        return self._request_target

    @request_target.setter
    def request_target(self, request_target: Optional[str]):
        """
        :param request_target: Target information received from showdown in a request
            message.
        "type request_target: str, optional
        """
        self._request_target = request_target

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
        if move_name.startswith("return"):
            return "return"
        if move_name.startswith("frustration"):
            return "frustration"
        if move_name.startswith("hiddenpower"):
            return "hiddenpower"
        return move_name

    @property
    def secondary(self) -> List[Dict[str, Any]]:
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
        :rtype: str | None
        """
        return self.entry.get("selfdestruct", None)

    @property
    def self_switch(self) -> Union[str, bool]:
        """
        :return: What kind of self swtich this move implies for the user.
        :rtype: str | None
        """
        return self.entry.get("selfSwitch", False)

    @property
    def side_condition(self) -> Optional[str]:
        """
        :return: Side condition inflicted by the move.
        :rtype: str | None
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
        :rtype: str | None
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
        :return: Move target. Possible targets (copied from PS codebase):

            * adjacentAlly - Only relevant to Doubles or Triples, the move only
              targets an ally of the user.
            * adjacentAllyOrSelf - The move can target the user or its ally.
            * adjacentFoe - The move can target a foe, but not (in Triples)
              a distant foe.
            * all - The move targets the field or all Pokémon at once.
            * allAdjacent - The move is a spread move that also hits the user's ally.
            * allAdjacentFoes - The move is a spread move.
            * allies - The move affects all active Pokémon on the user's team.
            * allySide - The move adds a side condition on the user's side.
            * allyTeam - The move affects all unfainted Pokémon on the user's team.
            * any - The move can hit any other active Pokémon, not just those adjacent.
            * foeSide - The move adds a side condition on the foe's side.
            * normal - The move can hit one adjacent Pokémon of your choice.
            * randomNormal - The move targets an adjacent foe at random.
            * scripted - The move targets the foe that damaged the user.
            * self - The move affects the user of the move.
        :rtype: str
        """
        return self.entry["target"]

    @property
    def terrain(self) -> Optional[Field]:
        """
        :return: Terrain started by the move.
        :rtype: Optional[Field]
        """
        terrain = self.entry.get("terrain", None)
        if terrain is not None:
            terrain = Field.from_showdown_message(terrain)
        return terrain

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
        return PokemonType.from_name(self.entry["type"])

    @property
    def use_target_offensive(self) -> bool:
        """
        :return: Whether the move uses the target's offensive statistics.
        :rtype: bool
        """
        return self.entry.get("overrideOffensivePokemon", False) == "target"

    @property
    def volatile_status(self) -> Optional[str]:
        """
        :return: Volatile status inflicted by the move.
        :rtype: str | None
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
        :rtype: str | None
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
    def __init__(self, move_id: str):
        self._id = move_id
        self._is_empty: bool = True

    def __getattribute__(self, name: str):
        try:
            return super(Move, self).__getattribute__(name)
        except (AttributeError, TypeError, ValueError):
            return 0

    def __deepcopy__(self, memodict: Optional[Dict[int, Any]] = {}):
        return EmptyMove(copy.deepcopy(self._id, memodict))


class DynamaxMove(Move):
    BOOSTS_MAP = {
        PokemonType.BUG: {"spa": -1},
        PokemonType.DARK: {"spd": -1},
        PokemonType.DRAGON: {"atk": -1},
        PokemonType.GHOST: {"def": -1},
        PokemonType.NORMAL: {"spe": -1},
    }
    SELF_BOOSTS_MAP = {
        PokemonType.FIGHTING: {"atk": +1},
        PokemonType.FLYING: {"spe": +1},
        PokemonType.GROUND: {"spd": +1},
        PokemonType.POISON: {"spa": +1},
        PokemonType.STEEL: {"def": +1},
    }
    TERRAIN_MAP = {
        PokemonType.ELECTRIC: Field.ELECTRIC_TERRAIN,
        PokemonType.FAIRY: Field.MISTY_TERRAIN,
        PokemonType.GRASS: Field.GRASSY_TERRAIN,
        PokemonType.PSYCHIC: Field.PSYCHIC_TERRAIN,
    }
    WEATHER_MAP = {
        PokemonType.FIRE: Weather.SUNNYDAY,
        PokemonType.ICE: Weather.HAIL,
        PokemonType.ROCK: Weather.SANDSTORM,
        PokemonType.WATER: Weather.RAINDANCE,
    }

    def __init__(self, parent: Move):
        self._parent: Move = parent

    def __getattr__(self, name: str):
        if name[:2] == "__":
            raise AttributeError(name)
        return getattr(self._parent, name)

    @property
    def accuracy(self):
        return 1

    @property
    def base_power(self) -> int:
        if self.category != MoveCategory.STATUS:
            base_power = self._parent.base_power
            if self.type in {PokemonType.POISON, PokemonType.FIGHTING}:
                if base_power < 40:
                    return 70
                if base_power < 50:
                    return 75
                if base_power < 60:
                    return 80
                if base_power < 70:
                    return 85
                if base_power < 100:
                    return 90
                if base_power < 140:
                    return 95
                return 100
            else:
                if base_power < 40:
                    return 90
                if base_power < 50:
                    return 100
                if base_power < 60:
                    return 110
                if base_power < 70:
                    return 120
                if base_power < 100:
                    return 130
                if base_power < 140:
                    return 140
                return 150
        return 0

    @property
    def boosts(self) -> Optional[Dict[str, int]]:
        if self.category != MoveCategory.STATUS:
            return self.BOOSTS_MAP.get(self.type, None)
        return None

    @property
    def breaks_protect(self):
        return False

    @property
    def crit_ratio(self):
        return 0

    @property
    def damage(self):
        return 0

    @property
    def defensive_category(self):
        return self.category

    @property
    def expected_hits(self):
        return 1

    @property
    def force_switch(self):
        return False

    @property
    def heal(self):
        return 0

    @property
    def is_protect_counter(self):
        return self.category == MoveCategory.STATUS

    @property
    def is_protect_move(self):
        return self.category == MoveCategory.STATUS

    @property
    def n_hit(self):
        return 1, 1

    @property
    def priority(self):
        return 0

    @property
    def recoil(self):
        return 0

    @property
    def self_boost(self) -> Optional[Dict[str, int]]:
        if self.category != MoveCategory.STATUS:
            return self.SELF_BOOSTS_MAP.get(self.type, None)
        return None

    @property
    def status(self):
        return None

    @property
    def terrain(self) -> Optional[Field]:
        if self.category != MoveCategory.STATUS:
            return self.TERRAIN_MAP.get(self.type, None)
        return None

    @property
    def weather(self) -> Optional[Weather]:
        if self.category != MoveCategory.STATUS:
            return self.WEATHER_MAP.get(self.type, None)
        return None
