"""This module defines the Observation class, which stores the state of the battle
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from poke_env.environment.field import Field
from poke_env.environment.observed_pokemon import ObservedPokemon
from poke_env.environment.side_condition import SideCondition
from poke_env.environment.weather import Weather


@dataclass
class Observation:
    side_conditions: Dict[SideCondition, int] = field(default_factory=dict)
    opponent_side_conditions: Dict[SideCondition, int] = field(default_factory=dict)

    weather: Dict[Weather, int] = field(default_factory=dict)
    fields: Dict[Field, int] = field(default_factory=dict)

    active_pokemon: Union[ObservedPokemon, List[Optional[ObservedPokemon]], None] = None
    opponent_active_pokemon: Union[
        ObservedPokemon, List[Optional[ObservedPokemon]], None
    ] = None

    # The opponent's team that has been exposed to the player, for VGC
    opponent_team: Dict[str, ObservedPokemon] = field(default_factory=dict)

    events: List[List[str]] = field(default_factory=list)
