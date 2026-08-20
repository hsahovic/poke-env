from random import Random

import orjson
import pytest

from poke_env.data.smogon import SmogonStats
from poke_env.teambuilder import (
    SmogonStatsTeambuilder,
    TeambuilderPokemon,
    complete_team,
    generate_team,
)
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
            "Checks and Counters": {},
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


def test_species_selection_uses_geometric_mean_of_teammates():
    def pokemon(usage, teammates):
        return {
            "Raw count": 100,
            "Abilities": {"ability": 10},
            "Items": {},
            "Spreads": {"Jolly:0/252/0/0/0/252": 10},
            "Moves": {"moveone": 10, "movetwo": 10, "movethree": 10, "movefour": 10},
            "Tera Types": {},
            "Teammates": teammates,
            "Checks and Counters": {},
            "usage": usage,
        }

    stats = SmogonStats.from_json(
        orjson.dumps(
            {
                "info": {
                    "metagame": "gen9ou",
                    "cutoff": 1695,
                    "number of battles": 1000,
                },
                "data": {
                    "Alpha": pokemon(0.4, {"Gamma": 9, "Delta": 4}),
                    "Beta": pokemon(0.3, {"Gamma": 1, "Delta": 4}),
                    "Gamma": pokemon(0.2, {}),
                    "Delta": pokemon(0.1, {}),
                },
            }
        ),
        month="2026-06",
    )

    builder = SmogonStatsTeambuilder(stats)

    assert builder._select_species([stats["Alpha"], stats["Beta"]]).id == "delta"


def test_sample_builder_is_seeded_and_preserves_observed_values(smogon_stats):
    team = [TeambuilderPokemon(species="Alpha", item="Kept Item", moves=["Move One"])]
    first = SmogonStatsTeambuilder(
        smogon_stats,
        team,
        team_strategy="sample",
        pokemon_strategy="sample",
        rng=Random(7),
    )
    second = SmogonStatsTeambuilder(
        smogon_stats,
        team,
        team_strategy="sample",
        pokemon_strategy="sample",
        rng=Random(7),
    )

    first_team = Teambuilder.parse_packed_team(first.yield_team())
    second_team = Teambuilder.parse_packed_team(second.yield_team())
    assert [pokemon.packed for pokemon in first_team] == [
        pokemon.packed for pokemon in second_team
    ]
    assert first_team[0].item == "keptitem"
    assert first_team[0].moves[0] == "moveone"
    assert len(first_team[0].moves) == len(set(first_team[0].moves)) == 4


def test_team_and_pokemon_strategies_are_independent(smogon_stats):
    team = [TeambuilderPokemon(species="Alpha")]
    greedy_team = SmogonStatsTeambuilder(
        smogon_stats,
        team,
        team_strategy="greedy",
        pokemon_strategy="sample",
        rng=Random(7),
    )
    sample_team = SmogonStatsTeambuilder(
        smogon_stats,
        team,
        team_strategy="sample",
        pokemon_strategy="greedy",
        rng=Random(7),
    )

    assert greedy_team.team_strategy == "greedy"
    assert greedy_team.pokemon_strategy == "sample"
    assert sample_team.team_strategy == "sample"
    assert sample_team.pokemon_strategy == "greedy"
    assert len(Teambuilder.parse_packed_team(greedy_team.yield_team())) == 6
    assert len(Teambuilder.parse_packed_team(sample_team.yield_team())) == 6


def test_pokemon_with_fewer_than_four_reported_moves_is_completed(smogon_stats):
    builder = SmogonStatsTeambuilder(smogon_stats)

    assert builder._choose_moves({"transform": 1.0}, []) == ["transform"]


def test_from_format_fetches_snapshot(monkeypatch, smogon_stats):
    calls = {}

    def fetch(cls, battle_format, **kwargs):
        calls["battle_format"] = battle_format
        calls["kwargs"] = kwargs
        return smogon_stats

    monkeypatch.setattr(SmogonStats, "fetch", classmethod(fetch))

    builder = SmogonStatsTeambuilder.from_format(
        "gen9ou",
        month="2026-06",
        cutoff=1695,
        timeout=12,
        cache_dir=None,
        refresh=True,
        team_strategy="sample",
        pokemon_strategy="greedy",
        rng=Random(7),
    )

    assert calls == {
        "battle_format": "gen9ou",
        "kwargs": {
            "month": "2026-06",
            "cutoff": 1695,
            "timeout": 12,
            "cache_dir": None,
            "refresh": True,
        },
    }
    assert builder.stats is smogon_stats
    assert builder.team_strategy == "sample"
    assert builder.pokemon_strategy == "greedy"


def test_convenience_helpers_return_structured_teams(monkeypatch, smogon_stats):
    monkeypatch.setattr(
        SmogonStats,
        "fetch",
        classmethod(lambda cls, battle_format, **kwargs: smogon_stats),
    )

    generated = generate_team("gen9ou", rng=Random(7))
    assert len(generated) == 6
    assert all(isinstance(pokemon, TeambuilderPokemon) for pokemon in generated)

    partial = [TeambuilderPokemon(species="Alpha", moves=["Observed Move"])]
    completed = complete_team(partial, "gen9ou", rng=Random(7))

    assert len(completed) == 6
    assert completed[0].moves[0] == "Observed Move"
    assert partial[0].moves == ["Observed Move"]


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
