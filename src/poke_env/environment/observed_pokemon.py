"""This module defines the ObservedPokmon class, which stores
what we have observed about a pokemon throughout a battle
"""

import sys
from copy import copy
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Union

from poke_env.environment.effect import Effect
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.pokemon_gender import PokemonGender
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.status import Status


@dataclass
class ObservedPokemon:
    species: str
    level: int

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
    moves: Dict[str, Move] = field(default_factory=dict)
    tera_type: Optional[PokemonType] = None
    shiny: Optional[bool] = None
    stats: Optional[Mapping[str, Union[List[int], int, None]]] = None
    status: Optional[Status] = None

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

        stats: Optional[Mapping[str, Union[List[int], int, None]]] = (
            ObservedPokemon.initial_stats()
        )
        if mon.stats is not None:
            stats = {k: v for (k, v) in mon.stats.items()}

        return ObservedPokemon(
            species=mon.species,
            level=mon.level,
            ability=mon.ability,
            boosts={k: v for (k, v) in mon.boosts.items()},
            current_hp_fraction=mon.current_hp_fraction,
            effects={k: v for (k, v) in mon.effects.items()},
            is_dynamaxed=mon.is_dynamaxed,
            is_terastallized=mon.is_terastallized,
            item=mon.item,
            gender=mon.gender,
            moves={k: copy(v) for (k, v) in mon.moves.items()},
            tera_type=mon.tera_type,
            shiny=mon.shiny,
            stats=stats,
            status=mon.status,
        )
