"""This module defines the ObservedPokemon class, which stores
what we have observed about a pokemon throughout a battle, offering
a more efficient serialization of a pokemon
"""

import sys
from collections import OrderedDict
from copy import copy
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Union

from poke_env.battle.effect import Effect
from poke_env.battle.move import Move
from poke_env.battle.pokemon import Pokemon
from poke_env.battle.pokemon_gender import PokemonGender
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.status import Status


@dataclass
class ObservedPokemon:
    species: str
    level: int
    name: str

    ability: Optional[str] = None
    boosts: Dict[str, int] = field(
        default_factory=lambda: {
            "accuracy": 0,
            "atk": 0,
            "def": 0,
            "evasion": 0,
            "spa": 0,
            "spd": 0,
            "spe": 0,
        }
    )
    current_hp_fraction: float = 1.0
    effects: Dict[Effect, int] = field(default_factory=dict)
    is_dynamaxed: bool = False
    is_terastallized: bool = False
    item: Optional[str] = None
    gender: Optional[PokemonGender] = None
    moves: "OrderedDict[str, Move]" = field(default_factory=OrderedDict)
    tera_type: Optional[PokemonType] = None
    shiny: Optional[bool] = None
    stats: Optional[Mapping[str, Union[List[int], int, None]]] = None
    status: Optional[Status] = None

    def to_pokemon(self, gen=9) -> Pokemon:
        mon = Pokemon(gen=gen, species=self.species, name=self.name)
        mon._item = self.item
        mon._level = self.level
        mon._moves = self.moves
        mon._ability = self.ability
        mon._terastallized_type = self.tera_type

        mon._stats = {}
        if self.stats:
            for stat in self.stats:
                if isinstance(self.stats[stat], int):
                    mon._stats[stat] = self.stats[stat]  # type: ignore

        mon._gender = self.gender
        mon._shiny = self.shiny
        return mon

    @staticmethod
    def initial_stats() -> Dict[str, List[int]]:
        return {
            "atk": [0, sys.maxsize],
            "def": [0, sys.maxsize],
            "spa": [0, sys.maxsize],
            "spd": [0, sys.maxsize],
            "spe": [0, sys.maxsize],
        }

    @staticmethod
    def from_pokemon(mon: Optional[Pokemon]):
        if mon is None:
            return None

        stats: Optional[Mapping[str, Union[List[int], int, None]]] = (
            ObservedPokemon.initial_stats()
        )
        if mon.stats is not None:
            stats = {k: v for (k, v) in mon.stats.items()}

        return ObservedPokemon(
            species=mon.species,
            level=mon.level,
            name=mon.name,
            ability=mon.ability,
            boosts={k: v for (k, v) in mon.boosts.items()},
            current_hp_fraction=mon.current_hp_fraction,
            effects={k: v for (k, v) in mon.effects.items()},
            is_dynamaxed=mon.is_dynamaxed,
            is_terastallized=mon.is_terastallized,
            item=mon.item,
            gender=mon.gender,
            moves=OrderedDict({k: copy(v) for (k, v) in mon.moves.items()}),
            tera_type=mon.tera_type,
            shiny=mon.shiny,
            stats=stats,
            status=mon.status,
        )
