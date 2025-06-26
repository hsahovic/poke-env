import pytest

from poke_env.battle import PokemonType
from poke_env.data import GenData


def test_types_correspond_to_type_chart_entries():
    type_chart = GenData.from_gen(8).type_chart

    for type_1 in list(PokemonType):
        if type_1 in {PokemonType.THREE_QUESTION_MARKS, PokemonType.STELLAR}:
            continue

        assert type_1.name in type_chart
        for type_2 in list(PokemonType):
            if type_2 in {PokemonType.THREE_QUESTION_MARKS, PokemonType.STELLAR}:
                continue

            assert type_2.name in type_chart

    for type_ in type_chart.keys():
        assert PokemonType[type_] is not None


def test_some_type_weaknesses():
    type_chart = GenData.from_gen(8).type_chart

    assert type_chart["WATER"]["WATER"] == 0.5
    assert type_chart["DRAGON"]["FIRE"] == 0.5
    assert type_chart["DRAGON"]["ELECTRIC"] == 0.5


def test_some_type_strengths():
    type_chart = GenData.from_gen(8).type_chart

    assert type_chart["FIRE"]["WATER"] == 2
    assert type_chart["DRAGON"]["DRAGON"] == 2
    assert type_chart["WATER"]["ELECTRIC"] == 2


def test_some_type_immunities():
    type_chart = GenData.from_gen(8).type_chart

    assert type_chart["FLYING"]["GROUND"] == 0
    assert type_chart["FAIRY"]["DRAGON"] == 0
    assert type_chart["GROUND"]["ELECTRIC"] == 0


def test_gen_data_from_gen_is_unique():
    for gen in range(1, 9):
        assert GenData.from_gen(gen) == GenData.from_gen(gen)


def test_gen_data_from_format():
    assert GenData.from_format("gen1ou") == GenData.from_gen(1)
    assert GenData.from_format("gen2randombattle") == GenData.from_gen(2)
    assert GenData.from_format("gen3uber") == GenData.from_gen(3)
    assert GenData.from_format("gen4ou") == GenData.from_gen(4)
    assert GenData.from_format("gen5randombattle") == GenData.from_gen(5)
    assert GenData.from_format("gen6ou") == GenData.from_gen(6)
    assert GenData.from_format("gen7randombattle") == GenData.from_gen(7)
    assert GenData.from_format("gen8doubleou") == GenData.from_gen(8)
    assert GenData.from_format("gen9doubleou") == GenData.from_gen(9)


def test_cant_init_same_gen_twice():
    for gen in range(1, 9):
        GenData.from_gen(gen)

        with pytest.raises(ValueError):
            GenData(gen=gen)
