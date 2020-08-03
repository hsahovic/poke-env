# -*- coding: utf-8 -*-
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from poke_env.data import POKEDEX
from poke_env.environment.effect import Effect
from poke_env.environment.pokemon_gender import PokemonGender
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.move import Move
from poke_env.environment.status import Status
from poke_env.environment.z_crystal import Z_CRYSTAL
from poke_env.utils import to_id_str


class Pokemon:

    __slots__ = (
        "_ability",
        "_active",
        "_active",
        "_base_ability",
        "_base_stats",
        "_boosts",
        "_current_hp",
        "_effects",
        "_gender",
        "_heightm",
        "_item",
        "_last_request",
        "_level",
        "_max_hp",
        "_moves",
        "_must_recharge",
        "_pokeball",
        "_possible_abilities",
        "_preparing",
        "_shiny",
        "_species",
        "_stats",
        "_status",
        "_type_1",
        "_type_2",
        "_weightkg",
    )

    def __init__(
        self,
        *,
        species: Optional[str] = None,
        request_pokemon: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None,
    ) -> None:
        # Species related attributes
        self._base_stats: Dict[str, int]
        self._heightm: int
        self._possible_abilities: List[str]
        self._species: str
        self._stats: Dict[str, Optional[int]] = {
            "atk": None,
            "def": None,
            "spa": None,
            "spd": None,
            "spe": None,
        }
        self._type_1: PokemonType
        self._type_2: Optional[PokemonType] = None
        self._weightkg: int

        # Individual related attributes
        self._ability: Optional[str] = None
        self._active: bool
        self._base_ability: str
        self._gender: Optional[PokemonGender] = None
        self._level: int = 100
        self._max_hp: int = 0
        self._moves: Dict[str, Move] = {}
        self._pokeball: Optional[str] = None
        self._shiny: Optional[bool] = False

        # Battle related attributes

        self._active: bool = False
        self._boosts: Dict[str, int] = {
            "accuracy": 0,
            "atk": 0,
            "def": 0,
            "evasion": 0,
            "spa": 0,
            "spd": 0,
            "spe": 0,
        }
        self._current_hp: int = 0
        self._effects: Set[Effect] = set()
        self._item: Optional[str]
        self._last_request: dict = {}
        self._must_recharge = False
        self._preparing = False
        self._status: Optional[Status] = None

        if details and not species:
            species = details.split(", ")[0]
        if species:
            self._update_from_pokedex(species)
            self._species = species
        elif request_pokemon:
            self._update_from_request(request_pokemon)
        elif details:
            self._update_from_details(details)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{self._species} (pokemon object) "
        "[Active: {self._active}, Status: {self._status}]"

    def _add_move(self, move_id: str, use: bool = False) -> None:
        """Store the move if applicable."""
        id_ = Move.retrieve_id(move_id)

        if not Move.should_be_stored(id_):
            return

        if id_ not in self._moves:
            move = Move(id_)
            self._moves[id_] = move
        if use:
            self._moves[id_].use()

    def _boost(self, stat, amount):
        self._boosts[stat] += int(amount)
        if self._boosts[stat] > 6:
            self._boosts[stat] = 6
        elif self._boosts[stat] < -6:
            self._boosts[stat] = -6

    def _clear_boosts(self):
        for stat in self._boosts:
            self._boosts[stat] = 0

    def _clear_effects(self):
        self._effects = set()

    def _clear_negative_boosts(self):
        for stat, value in self._boosts.items():
            if value < 0:
                self._boosts[stat] = 0

    def _clear_positive_boosts(self):
        for stat, value in self._boosts.items():
            if value > 0:
                self._boosts[stat] = 0

    def _copy_boosts(self, mon):
        self._boosts = dict(mon._boosts.items())

    def _cure_status(self, status):
        if Status[status.upper()] == self._status:
            self._status = None

    def _damage(self, hp_status):
        self._set_hp_status(hp_status)

    def _end_effect(self, effect):
        effect = Effect.from_showdown_message(effect)
        if effect in self._effects:
            self._effects.remove(effect)

    def _end_item(self, item):
        self._item = None

    def _faint(self):
        self._current_hp = 0
        self.status = Status.FNT

    def _forme_change(self, species):
        species = species.split(",")[0]
        self._update_from_pokedex(species)

    def _heal(self, hp_status):
        self._set_hp_status(hp_status)

    def _invert_boosts(self):
        self._boosts = {k: -v for k, v in self._boosts.items()}

    def _mega_evolve(self, stone):
        mega_species = self.species + "mega"
        if mega_species in POKEDEX:
            self._species = mega_species
            self._update_from_pokedex(mega_species)
        elif stone[-1] in "XY":
            mega_species = self.species + "mega" + stone[-1].lower()
            self._species = mega_species
            self._update_from_pokedex(mega_species)

    def _moved(self, move):
        self._must_recharge = False
        self._preparing = False
        self._add_move(move, use=True)

    def _prepare(self, move, target):
        self._preparing = (move, target)

    def _primal(self):
        primal_species = self._species + "primal"
        self._update_from_pokedex(primal_species)

    def _set_boost(self, stat, amount):
        assert abs(int(amount)) <= 6
        self._boosts[stat] = int(amount)

    def _set_hp(self, hp_status):
        self._set_hp_status(hp_status)

    def _set_hp_status(self, hp_status):
        if " " in hp_status:
            hp, status = hp_status.split(" ")
        else:
            hp = hp_status
            status = None

        if status == "fnt":
            self.status = Status.FNT
            self._current_hp = 0
            return
        elif status:
            self.status = status
        self._current_hp, self._max_hp = hp.split("/")
        self._current_hp = int(self._current_hp)
        self._max_hp = int(self._max_hp)

    def _start_effect(self, effect):
        effect = Effect.from_showdown_message(effect)
        self._effects.add(effect)

    def _swap_boosts(self):
        self._boosts["atk"], self._boosts["spa"] = (
            self._boosts["spa"],
            self._boosts["atk"],
        )

    def _switch_in(self):
        self._last_request = {}
        self._active = True

    def _switch_out(self):
        self._last_request = {}
        self._active = False
        self._clear_boosts()
        self._clear_effects()
        self._must_recharge = False
        self._preparing = False

    def _transform(self, into):
        current_hp = self.current_hp
        self._update_from_pokedex(into.species)
        self._current_hp = int(current_hp)

    def _update_from_pokedex(self, species: str) -> None:
        dex_entry = POKEDEX[to_id_str(species)]
        self._base_stats = dex_entry["baseStats"]

        self._type_1 = PokemonType.from_name(dex_entry["types"][0])
        if len(dex_entry["types"]) == 1:
            self._type_2 = None
        else:
            self._type_2 = PokemonType.from_name(dex_entry["types"][1])

        self._possible_abilities = dex_entry["abilities"]
        self._heightm = dex_entry["heightm"]
        self._weightkg = dex_entry["weightkg"]

    def _update_from_details(self, details: str) -> None:
        if ", shiny" in details:
            self._shiny = True
            details = details.replace(", shiny", "")
        else:
            self._shiny = False

        split_details = details.split(", ")

        gender = None
        level = None

        if len(split_details) == 3:
            species, level, gender = split_details
        elif len(split_details) == 2:
            if split_details[1].startswith("L"):
                species, level = split_details
            else:
                species, gender = split_details
        else:
            species = split_details[0]

        if gender:
            self._gender = PokemonGender.from_request_details(gender)
        else:
            self._gender = PokemonGender.NEUTRAL

        if level:
            self._level = int(level[1:])
        else:
            self._level = 100

        if species != self._species:
            self._update_from_pokedex(species)

    def _update_from_request(self, request_pokemon: Dict[str, Any]) -> None:
        if request_pokemon == self._last_request:
            return
        self._last_request = request_pokemon

        self._ability = request_pokemon["ability"]
        self._active = request_pokemon["active"]
        self._base_ability = request_pokemon["baseAbility"]

        condition = request_pokemon["condition"]
        if condition == "0 fnt":
            self._current_hp = 0
            self.status = Status.FNT
        else:
            if " " in condition:
                hps, status = condition.split(" ")
                self.status = status
            else:
                hps = condition
                self.status = None
            current_hp, max_hp = hps.split("/")
            self._current_hp = int(current_hp)
            self._max_hp = int(max_hp)

        self._item = request_pokemon["item"]

        details = request_pokemon["details"]
        self._update_from_details(details)

        for move in request_pokemon["moves"]:
            self._add_move(move)

        if len(self._moves) > 4:
            self._moves = {}
            for move in request_pokemon["moves"]:
                self._add_move(move)

        ident = request_pokemon["ident"].split(": ")

        if len(ident) == 2:
            self._species = ident[1]
        elif len(ident) == 3:
            self._species = ": ".join(ident[1:])
        else:
            raise NotImplementedError("Unmanaged pokemon ident: %s" % ident)
        self._pokeball = request_pokemon["pokeball"]
        self._stats = request_pokemon["stats"]

    def _used_z_move(self):
        self._item = None

    def _was_illusionned(self):
        self._current_hp = None
        self._max_hp = None
        self._status = None
        self._switch_out()

    def damage_multiplier(self, type_or_move: Union[PokemonType, Move]) -> float:
        """
        Returns the damage multiplier associated with a given type or move on this
        pokemon.

        This method is a shortcut for PokemonType.damage_multiplier with relevant types.

        :param type_or_move: The type or move of interest.
        :type type_or_move: PokemonType or Move
        :return: The damage multiplier associated with given type on the pokemon.
        :rtype: float
        """
        if isinstance(type_or_move, Move):
            type_or_move = type_or_move.type
        if isinstance(type_or_move, PokemonType):
            return type_or_move.damage_multiplier(self._type_1, self._type_2)
        # This can happen with special moves, which do not necessarily have a type
        return 1

    @property
    def ability(self) -> Optional[str]:
        """
        :return: The pokemon's ability. None if unknown.
        :rtype: str, optional
        """
        return self._ability

    @ability.setter
    def ability(self, ability: Optional[str]):
        self._ability = ability

    @property
    def active(self) -> Optional[bool]:
        """
        :return: Boolean indicating whether the pokemon is active.
        :rtype: bool
        """
        return self._active

    @property
    def available_z_moves(self) -> List[Move]:
        """
        Caution: this property is not properly tested yet.

        :return: The set of moves that pokemon can use as z-moves.
        :rtype: List[Move]
        """
        if isinstance(self.item, str) and self.item.endswith("iumz"):  # pyre-ignore
            type_, move = Z_CRYSTAL[self.item]  # pyre-ignore
            if type_:
                return [
                    move
                    for move_id, move in self._moves.items()
                    if move.type == type_ and move.can_z_move
                ]
            elif move in self._moves:
                return [self._moves[move]]
        return []

    @property
    def base_stats(self) -> Dict[str, int]:
        """
        :return: The pokemon's base stats.
        :rtype: Dict[str, int]
        """
        return self._base_stats

    @property
    def boosts(self) -> Dict[str, int]:
        """
        :return: The pokemon's boosts.
        :rtype: Dict[str, int]
        """
        return self._boosts

    @property
    def current_hp(self) -> int:
        """
        :return: The pokemon's current hp. For your pokemons, this is the actual value.
            For opponent's pokemon, this value depends on showdown information: it can
            be on a scale from 0 to 100 or on a pixel scale.
        :rtype: int
        """
        return self._current_hp

    @property
    def current_hp_fraction(self) -> float:
        """
        :return: The pokemon's current remaining hp fraction.
        :rtype: float
        """
        if self.current_hp:
            return self.current_hp / self.max_hp
        return 0

    @property
    def effects(self) -> Set[Effect]:
        """
        :return: The effects currently affecting the pokemon.
        :rtype: Set[Effect]
        """
        return self._effects

    @property
    def fainted(self) -> bool:
        """
        :return: Wheter the pokemon has fainted.
        :rtype: bool
        """
        return Status.FNT == self._status

    @property
    def gender(self) -> Optional[PokemonGender]:
        """
        :return: The pokemon's gender.
        :rtype: PokemonGender, optional
        """
        return self._gender

    @property
    def height(self) -> float:
        """
        :return: The pokemon's height, in meters.
        :rtype: float
        """
        return self._heightm

    @property
    def is_dynamaxed(self) -> bool:
        """
        :return: Whether the pokemon is currently dynamaxed
        :rtype: bool
        """
        return Effect.DYNAMAX in self.effects

    @property
    def item(self) -> Optional[str]:
        """
        :return: The pokemon's item.
        :rtype: Optional[str]
        """
        return self._item

    @item.setter
    def item(self, item: str):
        self._item = item

    @property
    def level(self) -> int:
        """
        :return: The pokemon's level.
        :rtype: int
        """
        return self._level

    @property
    def max_hp(self) -> int:
        """
        :return: The pokemon's max hp. For your pokemons, this is the actual value.
            For opponent's pokemon, this value depends on showdown information: it can
            be on a scale from 0 to 100 or on a pixel scale.
        :rtype: int
        """
        return self._max_hp

    @property
    def moves(self) -> Dict[str, Move]:
        """
        :return: A dictionary of the pokemon's known moves.
        :rtype: Dict[str, Move]
        """
        return self._moves

    @property
    def must_recharge(self) -> bool:
        """
        :return: A boolean indicating whether the pokemon must recharge.
        :rtype: bool
        """
        return self._must_recharge

    @must_recharge.setter
    def must_recharge(self, value) -> None:
        self._must_recharge = value

    @property
    def pokeball(self) -> Optional[str]:
        """
        :return: The pokeball in which is the pokemon.
        :rtype: Optional[str]
        """
        return self._pokeball

    @property
    def possible_abilities(self) -> List[str]:
        """
        :return: The list of possible abilities for this pokemon.
        :rtype: List[str]
        """
        return self._possible_abilities

    @property
    def preparing(self) -> bool:
        """
        :return: Whether this pokemon is preparing a multi-turn move.
        :rtype: bool
        """
        return self._preparing

    @property
    def shiny(self) -> bool:
        """
        :return: Whether this pokemon is shiny.
        :rtype: bool
        """
        return bool(self._shiny)

    @property
    def species(self) -> str:
        """
        :return: The pokemon's species.
        :rtype: Optional[str]
        """
        return self._species

    @property
    def stats(self) -> Dict[str, Optional[int]]:
        """
        :return: The pokemon's stats, as a dictionary.
        :rtype: Dict[str, Optional[int]]
        """
        return self._stats

    @property
    def status(self) -> Optional[Status]:
        """
        :return: The pokemon's status.
        :rtype: Optional[Status]
        """
        return self._status

    @status.setter
    def status(self, status):
        if isinstance(status, str):
            status = Status[status.upper()]
        self._status = status

    @property
    def type_1(self) -> PokemonType:
        """
        :return: The pokemon's first type.
        :rtype: PokemonType
        """
        return self._type_1

    @property
    def type_2(self) -> Optional[PokemonType]:
        """
        :return: The pokemon's second type.
        :rtype: Optional[PokemonType]
        """
        return self._type_2

    @property
    def types(self) -> Tuple[PokemonType, Optional[PokemonType]]:
        """
        :return: The pokemon's types, as a tuple.
        :rtype: Tuple[PokemonType, Optional[PokemonType]]
        """
        return self.type_1, self._type_2

    @property
    def weight(self) -> float:
        """
        :return: The pokemon's weight, in kilograms.
        :rtype: float
        """
        return self._weightkg
