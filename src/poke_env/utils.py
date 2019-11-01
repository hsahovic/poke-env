# -*- coding: utf-8 -*-
"""This module contains utility functions and objects.
"""

import json

from typing import Dict


def _compute_type_chart(chart_path: str) -> Dict[str, Dict[str, float]]:
    """Returns the pokemon type_chart.

    Returns a dictionnary representing the Pokemon type chart, loaded from a json file
    in `data`. This dictionnary is computed in this file as `TYPE_CHART`.

    :return: The pokemon type chart
    :rtype: Dict[str, Dict[str, float]]
    """
    with open(chart_path) as chart:
        json_chart = json.load(chart)

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


def to_id_str(name: str) -> str:
    """Converts a full-name to its corresponding id string.

    :param name: The name to convert.
    :type name: str
    :return: The corresponding id string.
    :rtype: str
    """
    name = name.lower()

    for c in " -%:'.":
        name = name.replace(c, "")

    return name
