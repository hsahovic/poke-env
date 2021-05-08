# -*- coding: utf-8 -*-
"""This module contains constant values used in the repository.
"""

import orjson
import os

from functools import lru_cache
from typing import Any, Union
from typing import Dict


def _compute_type_chart(chart_path: str) -> Dict[str, Dict[str, float]]:
    """Returns the pokemon type_chart.

    Returns a dictionnary representing the Pokemon type chart, loaded from a json file
    in `data`. This dictionnary is computed in this file as `TYPE_CHART`.

    :return: The pokemon type chart
    :rtype: Dict[str, Dict[str, float]]
    """
    with open(chart_path) as chart:
        json_chart = orjson.loads(chart.read())

    types = [str(entry["name"]).upper() for entry in json_chart]

    type_chart = {type_1: {type_2: 1.0 for type_2 in types} for type_1 in types}

    for entry in json_chart:
        type_ = entry["name"].upper()
        for immunity in entry["immunes"]:
            type_chart[type_][immunity.upper()] = 0.0
        for weakness in entry["weaknesses"]:
            type_chart[type_][weakness.upper()] = 0.5
        for strength in entry["strengths"]:
            type_chart[type_][strength.upper()] = 2.0

    return type_chart


@lru_cache(2 ** 13)
def to_id_str(name: str) -> str:
    """Converts a full-name to its corresponding id string.
    :param name: The name to convert.
    :type name: str
    :return: The corresponding id string.
    :rtype: str
    """
    return "".join(char for char in name if char.isalnum()).lower()


_TYPE_CHART_PATH: str = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "data", "typeChart.json"
)
"Path to the json file containing type informations."


POKEDEX: Dict[str, Any] = {}

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "pokedex.json")
) as pokedex:
    POKEDEX = orjson.loads(pokedex.read())

_missing_dex: Dict[str, Any] = {}
for key, value in POKEDEX.items():
    if "cosmeticFormes" in value:
        for other_form in value["cosmeticFormes"]:
            _missing_dex[to_id_str(other_form)] = value

# Alternative pikachu gmax forms
for name, value in POKEDEX.items():
    if name.startswith("pikachu") and name not in {"pikachu", "pikachugmax"}:
        _missing_dex[name + "gmax"] = POKEDEX["pikachugmax"]

POKEDEX.update(_missing_dex)

for name, value in POKEDEX.items():
    if "baseSpecies" in value:
        value["species"] = value["baseSpecies"]
    else:
        value["baseSpecies"] = to_id_str(name)


GEN4_POKEDEX: Dict[str, Any] = {}

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "pokedex_by_gen",
        "gen4_pokedex.json",
    )
) as pokedex:
    GEN4_POKEDEX = orjson.loads(pokedex.read())

_missing_g4_dex: Dict[str, Any] = {}
for key, value in GEN4_POKEDEX.items():
    if "cosmeticFormes" in value:
        for other_form in value["cosmeticFormes"]:
            _missing_g4_dex[to_id_str(other_form)] = value

GEN4_POKEDEX.update(_missing_g4_dex)

for name, value in GEN4_POKEDEX.items():
    if "baseSpecies" in value:
        value["species"] = value["baseSpecies"]
    else:
        value["baseSpecies"] = to_id_str(name)


GEN5_POKEDEX: Dict[str, Any] = {}

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "pokedex_by_gen",
        "gen5_pokedex.json",
    )
) as pokedex:
    GEN5_POKEDEX = orjson.loads(pokedex.read())

_missing_g5_dex: Dict[str, Any] = {}
for key, value in GEN5_POKEDEX.items():
    if "cosmeticFormes" in value:
        for other_form in value["cosmeticFormes"]:
            _missing_g5_dex[to_id_str(other_form)] = value

GEN5_POKEDEX.update(_missing_g5_dex)

for name, value in GEN5_POKEDEX.items():
    if "baseSpecies" in value:
        value["species"] = value["baseSpecies"]
    else:
        value["baseSpecies"] = to_id_str(name)


GEN6_POKEDEX: Dict[str, Any] = {}

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "pokedex_by_gen",
        "gen6_pokedex.json",
    )
) as pokedex:
    GEN6_POKEDEX = orjson.loads(pokedex.read())

_missing_g6_dex: Dict[str, Any] = {}
for key, value in GEN6_POKEDEX.items():
    if "cosmeticFormes" in value:
        for other_form in value["cosmeticFormes"]:
            _missing_g6_dex[to_id_str(other_form)] = value

GEN6_POKEDEX.update(_missing_g6_dex)

for name, value in GEN6_POKEDEX.items():
    if "baseSpecies" in value:
        value["species"] = value["baseSpecies"]
    else:
        value["baseSpecies"] = to_id_str(name)


GEN7_POKEDEX: Dict[str, Any] = {}

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "pokedex_by_gen",
        "gen7_pokedex.json",
    )
) as pokedex:
    GEN7_POKEDEX = orjson.loads(pokedex.read())

_missing_g7_dex: Dict[str, Any] = {}
for key, value in GEN7_POKEDEX.items():
    if "cosmeticFormes" in value:
        for other_form in value["cosmeticFormes"]:
            _missing_g7_dex[to_id_str(other_form)] = value

GEN7_POKEDEX.update(_missing_g7_dex)

for name, value in GEN7_POKEDEX.items():
    if "baseSpecies" in value:
        value["species"] = value["baseSpecies"]
    else:
        value["baseSpecies"] = to_id_str(name)


GEN8_POKEDEX: Dict[str, Any] = {}

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "pokedex_by_gen",
        "gen8_pokedex.json",
    )
) as pokedex:
    GEN8_POKEDEX = orjson.loads(pokedex.read())

_missing_g8_dex: Dict[str, Any] = {}
for key, value in GEN8_POKEDEX.items():
    if "cosmeticFormes" in value:
        for other_form in value["cosmeticFormes"]:
            _missing_g8_dex[to_id_str(other_form)] = value

GEN8_POKEDEX.update(_missing_g8_dex)

for name, value in GEN8_POKEDEX.items():
    if "baseSpecies" in value:
        value["species"] = value["baseSpecies"]
    else:
        value["baseSpecies"] = to_id_str(name)


GEN_TO_POKEDEX: Dict[int, Dict[str, Any]] = {
    4: GEN4_POKEDEX,
    5: GEN5_POKEDEX,
    6: GEN6_POKEDEX,
    7: GEN7_POKEDEX,
    8: GEN8_POKEDEX,
}


MOVES: Dict[str, Any] = {}

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "moves.json")
) as moves:
    MOVES = orjson.loads(moves.read())


GEN4_MOVES: Dict[str, Any] = {}

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "moves_by_gen",
        "gen4_moves.json",
    )
) as moves:
    GEN4_MOVES = orjson.loads(moves.read())


GEN5_MOVES: Dict[str, Any] = {}

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "moves_by_gen",
        "gen5_moves.json",
    )
) as moves:
    GEN5_MOVES = orjson.loads(moves.read())


GEN6_MOVES: Dict[str, Any] = {}

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "moves_by_gen",
        "gen6_moves.json",
    )
) as moves:
    GEN6_MOVES = orjson.loads(moves.read())


GEN7_MOVES: Dict[str, Any] = {}

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "moves_by_gen",
        "gen7_moves.json",
    )
) as moves:
    GEN7_MOVES = orjson.loads(moves.read())


GEN8_MOVES: Dict[str, Any] = {}

with open(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "moves_by_gen",
        "gen8_moves.json",
    )
) as moves:
    GEN8_MOVES = orjson.loads(moves.read())


GEN_TO_MOVES: Dict[int, Dict[str, Any]] = {
    4: GEN4_MOVES,
    5: GEN5_MOVES,
    6: GEN6_MOVES,
    7: GEN7_MOVES,
    8: GEN8_MOVES,
}


TYPE_CHART: Dict[str, Dict[str, float]] = _compute_type_chart(_TYPE_CHART_PATH)


NATURES: Dict[str, Dict[str, Union[int, float]]] = {}

with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "natures.json")
) as natures:
    NATURES = orjson.loads(natures.read())


"""
A dictionnary representing the Pokemon type chart.

Each key is a string representing a type (corresponding to `Type` names), and each value
is a dictionnary whose keys are string representation of types, and whose values are
floats.

TYPE_CHART[type_1][type_2] corresponds to the damage multiplier of an attack of type_1
on a Pokemon of type_2. This dictionnary isncomputed using the `compute_type_chart`
function.
"""
