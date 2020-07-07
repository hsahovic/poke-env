# -*- coding: utf-8 -*-

from poke_env.data import TYPE_CHART, _TYPE_CHART_PATH, _compute_type_chart
from poke_env.environment.pokemon_type import PokemonType


def test_type_chart_corresponds_to__compute_type_chart():
    assert _compute_type_chart(_TYPE_CHART_PATH) == TYPE_CHART


def test_types_correspond_to_type_chart_entries():
    for type_1 in list(PokemonType):
        assert type_1.name in TYPE_CHART
        for type_2 in list(PokemonType):
            assert type_2.name in TYPE_CHART

    for type_ in TYPE_CHART.keys():
        assert PokemonType[type_] is not None


def test_some_type_weaknesses():
    assert TYPE_CHART["WATER"]["WATER"] == 0.5
    assert TYPE_CHART["FIRE"]["DRAGON"] == 0.5
    assert TYPE_CHART["ELECTRIC"]["DRAGON"] == 0.5


def test_some_type_strengths():
    assert TYPE_CHART["WATER"]["FIRE"] == 2
    assert TYPE_CHART["DRAGON"]["DRAGON"] == 2
    assert TYPE_CHART["ELECTRIC"]["WATER"] == 2


def test_some_type_immunities():
    assert TYPE_CHART["GROUND"]["FLYING"] == 0
    assert TYPE_CHART["DRAGON"]["FAIRY"] == 0
    assert TYPE_CHART["ELECTRIC"]["GROUND"] == 0
