# -*- coding: utf-8 -*-
"""This module contains constant values used in the repository.
"""

import json
import os

from typing import Any
from typing import Dict

from poke_env.utils import _compute_type_chart


_TYPE_CHART_PATH: str = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "data", "typeChart.json"
)
"Path to the json file containing type informations."

POKEDEX: Dict[str, Any] = {}

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "pokedex.json")
) as pokedex:
    POKEDEX = json.load(pokedex)

_missing_dex: Dict[str, Any] = {}
for key, value in POKEDEX.items():
    if "otherForms" in value:
        for other_form in value["otherForms"]:
            _missing_dex[other_form] = value

POKEDEX.update(_missing_dex)

_equivalent_forms = {"darmanitangalarzen": "darmanitanzengalar"}

POKEDEX.update({k: POKEDEX[v] for k, v in _equivalent_forms.items()})

MOVES: Dict[str, Any] = {}

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "moves.json")
) as moves:
    MOVES = json.load(moves)

TYPE_CHART: Dict[str, Dict[str, float]] = _compute_type_chart(_TYPE_CHART_PATH)
"""
A dictionnary representing the Pokemon type chart.

Each key is a string representing a type (corresponding to `Type` names), and each value
is a dictionnary whose keys are string representation of types, and whose values are
floats.

TYPE_CHART[type_1][type_2] corresponds to the damage multiplier of an attack of type_1
on a Pokemon of type_2. This dictionnary isncomputed using the `compute_type_chart`
function.
"""
