# -*- coding: utf-8 -*-
"""This module contains objects related ot z-crystal management. It should not be used
directly.
"""
from typing import Dict
from typing import Optional
from typing import Tuple

from poke_env.environment.pokemon_type import PokemonType


Z_CRYSTAL: Dict[str, Tuple[Optional[PokemonType], Optional[str]]] = {
    "buginiumz": (PokemonType.BUG, None),
    "darkiniumz": (PokemonType.DARK, None),
    "dragoniumz": (PokemonType.DRAGON, None),
    "electriumz": (PokemonType.ELECTRIC, None),
    "fairiumz": (PokemonType.FAIRY, None),
    "fightiniumz": (PokemonType.FIGHTING, None),
    "firiumz": (PokemonType.FIRE, None),
    "flyiniumz": (PokemonType.FLYING, None),
    "ghostiumz": (PokemonType.GHOST, None),
    "grassiumz": (PokemonType.GRASS, None),
    "groundiumz": (PokemonType.GROUND, None),
    "iciumz": (PokemonType.ICE, None),
    "normaliumz": (PokemonType.NORMAL, None),
    "poisoniumz": (PokemonType.POISON, None),
    "psychiumz": (PokemonType.PSYCHIC, None),
    "rockiumz": (PokemonType.ROCK, None),
    "steeliumz": (PokemonType.STEEL, None),
    "wateriumz": (PokemonType.WATER, None),
    "aloraichiumz": (None, "thunderbolt"),
    "decidiumz": (None, "spiritshackle"),
    "eeviumz": (None, "lastresort"),
    "inciniumz": (None, "darkestlariat"),
    "kommoniumz": (None, "clangingscales"),
    "lunaliumz": (None, "moongeistbeam"),
    "lycaniumz": (None, "stoneedge"),
    "marshadiumz": (None, "spectralthief"),
    "mewniumz": (None, "psychic"),
    "mimikiumz": (None, "playrough"),
    "pikaniumz": (None, "volttackle"),
    "pikashuniumz": (None, "thunderbolt"),
    "primariumz": (None, "sparklingaria"),
    "snorliumz": (None, "gigaimpact"),
    "solganiumz": (None, "sunsteelstrike"),
    "tapuniumz": (None, "naturesmadness"),
    "ultranecroziumz": (None, "photongeyser"),
}
