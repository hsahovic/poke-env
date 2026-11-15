import json

import pytest

from scripts.data_script_utils import clean_ps_data_text


@pytest.mark.parametrize("deserialize", [False, True])
def test_clean_ps_data_preserves_quoted_values(deserialize):
    source = """export const Pokedex: SpeciesDataTable = {
    kleavor: {
        "num": 900,
        evoCondition: "in Legends: Arceus or Legends: Z-A",
        description: "Use \\"a move\\" with target: Pokemon // unchanged",
        abilities: {0: "Swarm", H: "Sheer Force"},
    },
};
"""
    result = clean_ps_data_text(source, deserialize=deserialize)
    if not deserialize:
        result = json.loads(result)
    assert result == {
        "kleavor": {
            "num": 900,
            "evoCondition": "in Legends: Arceus or Legends: Z-A",
            "description": 'Use "a move" with target: Pokemon // unchanged',
            "abilities": {"0": "Swarm", "H": "Sheer Force"},
        }
    }
