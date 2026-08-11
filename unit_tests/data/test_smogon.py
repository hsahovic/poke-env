from pathlib import Path

import orjson
import pytest
import requests

from poke_env.data.smogon import (
    SmogonStats,
    SmogonStatsError,
    SmogonStatsNotFoundError,
    SmogonStatsParseError,
    Spread,
)


@pytest.fixture
def chaos_document():
    return {
        "info": {
            "metagame": "gen9ou",
            "cutoff": 1695,
            "cutoff deviation": 0,
            "team type": None,
            "number of battles": 1234,
        },
        "data": {
            "Great Tusk": {
                "Raw count": 400,
                "Abilities": {"protosynthesis": 4.0},
                "Items": {"heavydutyboots": 2.5, "rockyhelmet": 1.5},
                "Spreads": {
                    "Jolly:0/252/4/0/0/252": 3.0,
                    "Impish:252/0/252/0/4/0": 1.0,
                },
                "Moves": {
                    "headlongrush": 4.0,
                    "rapidspin": 3.5,
                    "icespinner": 3.0,
                    "stealthrock": 2.0,
                    "closecombat": 2.0,
                    "knockoff": 1.5,
                    "unusedmove": 0.0,
                },
                "Tera Types": {"Steel": 3.0, "Water": 1.0},
                "Teammates": {"Gholdengo": 1.2, "Corviknight": -0.4, "Kingambit": 0.0},
                "Checks and Counters": {},
                "usage": 0.25,
            },
            "Pikachu": {
                "Raw count": 20,
                "Abilities": {"static": 0.5},
                "Items": {"lightball": 0.5},
                "Spreads": {"Timid:0/0/0/252/4/252": 0.5},
                "Moves": {
                    "thunderbolt": 0.5,
                    "voltswitch": 0.5,
                    "surf": 0.5,
                    "grassknot": 0.5,
                },
                "Teammates": {},
                "Checks and Counters": {},
                "usage": 0.01,
            },
        },
    }


@pytest.fixture
def chaos_payload(chaos_document):
    return orjson.dumps(chaos_document)


def test_from_json_parses_and_normalizes_chaos_data(chaos_payload):
    stats = SmogonStats.from_json(
        chaos_payload,
        month="2026-06",
        source_url="https://example.test/gen9ou-1695.json",
    )

    assert stats.battle_format == "gen9ou"
    assert stats.month == "2026-06"
    assert stats.cutoff == 1695
    assert stats.battle_count == 1234
    assert stats.source_url == "https://example.test/gen9ou-1695.json"

    great_tusk = stats["Great Tusk"]
    assert great_tusk is stats["greattusk"]
    assert great_tusk.name == "Great Tusk"
    assert great_tusk.usage == 0.25
    assert great_tusk.raw_count == 400
    assert great_tusk.abilities == {"protosynthesis": 1.0}
    assert great_tusk.items == {"heavydutyboots": 0.625, "rockyhelmet": 0.375}
    assert great_tusk.moves["rapidspin"] == 0.875
    assert "unusedmove" not in great_tusk.moves
    assert great_tusk.tera_types == {"steel": 0.75, "water": 0.25}
    assert great_tusk.teammate_scores == {
        "gholdengo": pytest.approx(0.3),
        "corviknight": pytest.approx(-0.1),
    }
    assert great_tusk.spreads == {
        Spread("Jolly", (0, 252, 4, 0, 0, 252)): 0.75,
        Spread("Impish", (252, 0, 252, 0, 4, 0)): 0.25,
    }

    assert stats["Pikachu"].tera_types == {}
    assert stats.get("missingno") is None


def test_snapshot_mappings_are_read_only(chaos_payload):
    stats = SmogonStats.from_json(chaos_payload, month="2026-06")

    with pytest.raises(TypeError):
        stats.pokemon["eevee"] = stats["pikachu"]
    with pytest.raises(TypeError):
        stats["pikachu"].moves["thunder"] = 1.0


def test_top_pokemon_filters_and_orders(chaos_payload):
    stats = SmogonStats.from_json(chaos_payload, month="2026-06")

    assert [pokemon.id for pokemon in stats.top_pokemon()] == ["greattusk", "pikachu"]
    assert [pokemon.id for pokemon in stats.top_pokemon(1)] == ["greattusk"]
    assert stats.top_pokemon(min_usage=0.1) == (stats["greattusk"],)
    assert stats.top_pokemon(min_raw_count=100) == (stats["greattusk"],)
    assert stats.top_pokemon(limit=0) == ()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"limit": -1}, "limit"),
        ({"min_usage": -0.1}, "min_usage"),
        ({"min_usage": float("nan")}, "min_usage"),
        ({"min_raw_count": -1}, "min_raw_count"),
    ],
)
def test_top_pokemon_rejects_invalid_filters(chaos_payload, kwargs, message):
    stats = SmogonStats.from_json(chaos_payload, month="2026-06")

    with pytest.raises(ValueError, match=message):
        stats.top_pokemon(**kwargs)


def test_from_file_reads_local_snapshot(tmp_path: Path, chaos_payload):
    snapshot = tmp_path / "gen9ou-1695.json"
    snapshot.write_bytes(chaos_payload)

    stats = SmogonStats.from_file(snapshot, month="2026-06")

    assert stats["Great Tusk"].usage == 0.25
    assert stats.source_url == snapshot.resolve().as_uri()


def test_fetch_uses_explicit_snapshot(monkeypatch, chaos_payload):
    class Response:
        status_code = 200
        content = chaos_payload

        @staticmethod
        def raise_for_status():
            return None

    request = {}

    def get(url, *, timeout):
        request["url"] = url
        request["timeout"] = timeout
        return Response()

    monkeypatch.setattr("poke_env.data.smogon.requests.get", get)

    stats = SmogonStats.fetch("Gen 9 OU", month="2026-06", cutoff=1695, timeout=12)

    assert request == {
        "url": "https://www.smogon.com/stats/2026-06/chaos/gen9ou-1695.json",
        "timeout": 12,
    }
    assert stats.battle_format == "gen9ou"


def test_fetch_reports_missing_snapshot(monkeypatch):
    class Response:
        status_code = 404

    monkeypatch.setattr(
        "poke_env.data.smogon.requests.get", lambda *args, **kwargs: Response()
    )

    with pytest.raises(SmogonStatsNotFoundError, match="not found"):
        SmogonStats.fetch("gen9ou", month="2026-06", cutoff=1825)


def test_fetch_wraps_request_errors(monkeypatch):
    def fail(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr("poke_env.data.smogon.requests.get", fail)

    with pytest.raises(SmogonStatsError, match="Failed to fetch"):
        SmogonStats.fetch("gen9ou", month="2026-06", cutoff=1695)


@pytest.mark.parametrize("month", ["2026-6", "2026-13", "latest", ""])
def test_snapshot_requires_explicit_valid_month(chaos_payload, month):
    with pytest.raises(ValueError, match="YYYY-MM"):
        SmogonStats.from_json(chaos_payload, month=month)


def test_parser_rejects_invalid_json():
    with pytest.raises(SmogonStatsParseError, match="Invalid"):
        SmogonStats.from_json(b"not json", month="2026-06")


def test_parser_rejects_zero_weight_pokemon(chaos_document):
    chaos_document["data"]["Pikachu"]["Abilities"] = {"static": 0}

    with pytest.raises(SmogonStatsParseError, match="positive total weight"):
        SmogonStats.from_json(orjson.dumps(chaos_document), month="2026-06")


def test_parser_rejects_invalid_spread(chaos_document):
    chaos_document["data"]["Pikachu"]["Spreads"] = {"Timid:252/252": 0.5}

    with pytest.raises(SmogonStatsParseError, match="Invalid spread"):
        SmogonStats.from_json(orjson.dumps(chaos_document), month="2026-06")
