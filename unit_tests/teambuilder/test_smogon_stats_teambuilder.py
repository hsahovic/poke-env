from random import Random

import orjson
import pytest

from poke_env.data.smogon import SmogonStats
from poke_env.teambuilder import SmogonStatsTeambuilder, TeambuilderPokemon
from poke_env.teambuilder.teambuilder import Teambuilder


@pytest.fixture
def smogon_stats():
    def pokemon(usage, teammates):
        return {
            "Raw count": 100,
            "Abilities": {"abilityone": 8, "abilitytwo": 2},
            "Items": {"itemone": 7, "itemtwo": 3},
            "Spreads": {"Jolly:0/252/4/0/0/252": 7, "Impish:252/0/252/0/4/0": 3},
            "Moves": {
                "moveone": 10,
                "movetwo": 9,
                "movethree": 8,
                "movefour": 7,
                "movefive": 6,
            },
            "Tera Types": {"Steel": 8, "Water": 2},
            "Teammates": teammates,
            "usage": usage,
        }

    return SmogonStats.from_json(
        orjson.dumps(
            {
                "info": {
                    "metagame": "gen9ou",
                    "cutoff": 1695,
                    "number of battles": 1000,
                },
                "data": {
                    "Alpha": pokemon(0.4, {"Beta": 8, "Gamma": -8}),
                    "Beta": pokemon(0.3, {"Alpha": 0.1}),
                    "Gamma": pokemon(0.5, {"Alpha": 0.1}),
                    "Delta": pokemon(0.2, {}),
                    "Epsilon": pokemon(0.1, {}),
                    "Zeta": pokemon(0.05, {}),
                },
            }
        ),
        month="2026-06",
    )


def test_greedy_builder_completes_observed_set_and_team(smogon_stats):
    builder = SmogonStatsTeambuilder(
        smogon_stats, [TeambuilderPokemon(species="Alpha", moves=["Observed Move"])]
    )

    team = Teambuilder.parse_packed_team(builder.yield_team())

    assert [pokemon.species for pokemon in team[:2]] == ["alpha", "beta"]
    assert len(team) == len({pokemon.species for pokemon in team}) == 6
    assert team[0].moves == ["observedmove", "moveone", "movetwo", "movethree"]
    assert team[0].ability == "abilityone"
    assert team[0].item == "itemone"
    assert team[0].nature == "Jolly"
    assert team[0].evs == [0, 252, 4, 0, 0, 252]
    assert team[0].tera_type == "steel"


def test_sample_builder_is_seeded_and_preserves_observed_values(smogon_stats):
    team = [TeambuilderPokemon(species="Alpha", item="Kept Item", moves=["Move One"])]
    first = SmogonStatsTeambuilder(smogon_stats, team, strategy="sample", rng=Random(7))
    second = SmogonStatsTeambuilder(
        smogon_stats, team, strategy="sample", rng=Random(7)
    )

    first_team = Teambuilder.parse_packed_team(first.yield_team())
    second_team = Teambuilder.parse_packed_team(second.yield_team())
    assert [pokemon.packed for pokemon in first_team] == [
        pokemon.packed for pokemon in second_team
    ]
    assert first_team[0].item == "keptitem"
    assert first_team[0].moves[0] == "moveone"
    assert len(first_team[0].moves) == len(set(first_team[0].moves)) == 4


@pytest.mark.parametrize(
    "team, message",
    [
        ([TeambuilderPokemon(species="Missing")], "not present"),
        (
            [TeambuilderPokemon(species="Alpha"), TeambuilderPokemon(species="alpha")],
            "duplicate",
        ),
        ([TeambuilderPokemon(species="Alpha", moves=["a", "a"])], "duplicate"),
    ],
)
def test_builder_rejects_invalid_partial_teams(smogon_stats, team, message):
    with pytest.raises(ValueError, match=message):
        builder = SmogonStatsTeambuilder(smogon_stats, team)
        builder.yield_team()
