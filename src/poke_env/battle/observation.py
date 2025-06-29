"""This module defines the Observation class, which stores the state of the battle.
It is updated whenever a new event is received and processed from showdown. Each observation
records a turn. Each property is the state of the battle at the beginning of the turn, and
the events are ones that occurred that turn. In this way, you can instanciate a new battle
with the Observations' properties, and then recreate that turn with the events property.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from poke_env.battle.field import Field
from poke_env.battle.observed_pokemon import ObservedPokemon
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.weather import Weather


@dataclass
class Observation:
    side_conditions: Dict[SideCondition, int] = field(default_factory=dict)
    opponent_side_conditions: Dict[SideCondition, int] = field(default_factory=dict)

    weather: Dict[Weather, int] = field(default_factory=dict)
    fields: Dict[Field, int] = field(default_factory=dict)

    active_pokemon: Union[ObservedPokemon, None, List[Optional[ObservedPokemon]]] = None
    opponent_active_pokemon: Union[
        ObservedPokemon, List[Optional[ObservedPokemon]], None
    ] = None

    # The player's team, so we can track states of mons throughout the battle
    team: Dict[str, Optional[ObservedPokemon]] = field(default_factory=dict)

    # The opponent's team that has been exposed to the player, for VGC
    opponent_team: Dict[str, Optional[ObservedPokemon]] = field(default_factory=dict)

    events: List[List[str]] = field(default_factory=list)
