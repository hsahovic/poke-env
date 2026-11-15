import json
import os
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

from poke_env.data import GenData, to_id_str
from scripts import update_items
from scripts.data_script_utils import clean_ps_data_text


def test_item_lookup():
    items = GenData.from_format("gen9ou").items
    assert items[to_id_str("Leftovers")]["fling"]["basePower"] == 10
    assert items["sitrusberry"]["isBerry"] is True
    assert items["charizarditex"]["megaStone"]["Charizard"] == "Charizard-Mega-X"


@pytest.mark.parametrize("gen", range(1, 10))
def test_item_generations(gen):
    items = GenData.from_gen(gen).items
    assert all(item["gen"] <= gen for item in items.values())
    assert ("leftovers" in items) == (gen >= 2)
    assert ("heavydutyboots" in items) == (gen >= 8)
    assert ("clearamulet" in items) == (gen >= 9)


def test_item_generation_overrides():
    assert GenData.from_gen(1).items["firestone"]["gen"] == 1
    assert GenData.from_gen(5).items["sitrusberry"]["naturalGift"]["basePower"] == 60
    assert GenData.from_gen(6).items["sitrusberry"]["naturalGift"]["basePower"] == 80
    assert GenData.from_gen(3).items["sitrusberry"]["onUpdate"] is None
    assert GenData.from_gen(4).items["sitrusberry"]["onUpdate"] == "onUpdate"


def test_item_generator(tmp_path, monkeypatch):
    current = {
        "old": {
            "gen": 2,
            "name": "Old",
            "onUpdate": "onUpdate",
            "fling": {"basePower": 10},
        },
        "new": {"gen": 3, "name": "New"},
    }
    sources = {
        "items.ts": current,
        "mods/gen2/items.ts": {"old": {"inherit": True, "onUpdate": None}},
        "mods/gen1/items.ts": {},
    }
    monkeypatch.setattr(update_items, "CURRENT_GEN", 3)
    monkeypatch.setattr(update_items, "STATIC_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(
        update_items,
        "fetch_and_clean_ps_data",
        lambda url: sources[url.split("/data/")[1]],
    )
    update_items.main()
    gen2 = json.loads((tmp_path / "items/gen2items.json").read_text())
    assert gen2 == {"old": {**current["old"], "onUpdate": None}}
    assert json.loads((tmp_path / "items/gen1items.json").read_text()) == {}
    assert json.loads((tmp_path / "items/gen3items.json").read_text()) == current


def test_item_effect_callback():
    source = """export const Items = {
 mentalherb: {
  fling: {
   basePower: 10,
   effect(pokemon) {
    pokemon.cureStatus();
   },
  },
 },
};
"""
    assert clean_ps_data_text(source)["mentalherb"]["fling"] == {
        "basePower": 10,
        "effect": "effect",
    }


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[2] / "src").exists(),
    reason="Wheel building requires the source tree",
)
def test_wheel_item_lookup(tmp_path):
    root = Path(__file__).resolve().parents[2]
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from setuptools.build_meta import build_wheel; "
            f"build_wheel({str(tmp_path)!r})",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    wheel = next(tmp_path.glob("*.whl"))
    installed = tmp_path / "installed"
    with ZipFile(wheel) as archive:
        archive.extractall(installed)
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from poke_env.data import GenData; "
            "assert GenData.from_gen(1).items['firestone']['gen'] == 1; "
            "assert GenData.from_gen(5).items['sitrusberry']['naturalGift']['basePower'] == 60; "
            "assert GenData.from_gen(9).items['leftovers']['name'] == 'Leftovers'",
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(installed)},
        check=True,
        capture_output=True,
    )
