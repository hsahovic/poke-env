# -*- coding: utf-8 -*-
"""This module contains constant values used in the repository.
"""

import json
import os

from typing import Dict


TYPE_CHART_PATH: str = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "data", "typeChart.json"
)
"Path to the json file containing type informations."

POKEDEX: Dict = {}

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "pokedex.json")
) as pokedex:
    POKEDEX = json.load(pokedex)

MOVES: Dict = {}

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "moves.json")
) as moves:
    MOVES = json.load(moves)
