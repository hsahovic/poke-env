"""This module defines the ObservedPokmon class, which stores
what we have observed about a pokemon throughout a battle
"""

import sys
from copy import copy
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Union

from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.pokemon_gender import PokemonGender
from poke_env.environment.pokemon_type import PokemonType


@dataclass
class ObservedPokemon:

    species: str
    level: int
    stats: Optional[Mapping[str, Union[List[int], int, None]]] = None
    moves: Dict[str, Move] = field(default_factory=dict)
    ability: Optional[str] = ""
    item: Optional[str] = None
    gender: Optional[PokemonGender] = None
    tera_type: Optional[PokemonType] = None
    shiny: Optional[bool] = None

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
    def from_pokemon(mon: Pokemon):
        if mon is None:
            return None

        stats = ObservedPokemon.initial_stats()
        if mon.stats is not None:
            stats = {k: v for (k, v) in mon.stats.items()}

        return ObservedPokemon(
            species=mon.species,
            stats=stats,
            moves={k: copy(v) for (k, v) in mon.moves.items()},
            ability=mon.ability,
            item=mon.item,
            gender=mon.gender,
            tera_type=mon.tera_type,
            shiny=mon.shiny,
            level=mon.level,
        )
