from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, Optional, Union

import orjson

from poke_env.data.normalize import to_id_str


class GenData:
    __slots__ = ("gen", "moves", "natures", "pokedex", "type_chart", "learnset")

    UNKNOWN_ITEM = "unknown_item"

    _gen_data_per_gen: Dict[int, GenData] = {}

    def __init__(self, gen: int):
        if gen in self._gen_data_per_gen:
            raise ValueError(f"GenData for gen {gen} already initialized.")

        self.gen = gen
        self.moves = self.load_moves(gen)
        self.natures = self.load_natures()
        self.pokedex = self.load_pokedex(gen)
        self.type_chart = self.load_type_chart(gen)
        self.learnset = self.load_learnset()

    def __deepcopy__(self, memodict: Optional[Dict[int, Any]] = None) -> GenData:
        return self

    def load_moves(self, gen: int) -> Dict[str, Any]:
        with open(
            os.path.join(self._static_files_root, "moves", f"gen{gen}moves.json")
        ) as f:
            return orjson.loads(f.read())

    def load_natures(self) -> Dict[str, Dict[str, Union[int, float]]]:
        with open(os.path.join(self._static_files_root, "natures.json")) as f:
            return orjson.loads(f.read())

    def load_learnset(self) -> Dict[str, Dict[str, Union[int, float]]]:
        with open(os.path.join(self._static_files_root, "learnset.json")) as f:
            return orjson.loads(f.read())

    def load_pokedex(self, gen: int) -> Dict[str, Any]:
        with open(
            os.path.join(self._static_files_root, "pokedex", f"gen{gen}pokedex.json")
        ) as f:
            dex = orjson.loads(f.read())

        other_forms_dex: Dict[str, Any] = {}
        for value in dex.values():
            if "cosmeticFormes" in value:
                for other_form in value["cosmeticFormes"]:
                    other_forms_dex[to_id_str(other_form)] = value

        # Alternative pikachu gmax forms
        for name, value in dex.items():
            if name.startswith("pikachu") and name not in {"pikachu", "pikachugmax"}:
                other_forms_dex[name + "gmax"] = dex["pikachugmax"]

        dex.update(other_forms_dex)

        for name, value in dex.items():
            if "baseSpecies" in value:
                value["species"] = value["baseSpecies"]
            else:
                value["baseSpecies"] = to_id_str(name)

        return dex

    def load_type_chart(self, gen: int) -> Dict[str, Dict[str, float]]:
        with open(
            os.path.join(
                self._static_files_root, "typechart", f"gen{gen}typechart.json"
            )
        ) as chart:
            json_chart = orjson.loads(chart.read())

        types = [str(type_).upper() for type_ in json_chart]
        type_chart = {type_1: {type_2: 1.0 for type_2 in types} for type_1 in types}

        for type_, data in json_chart.items():
            type_ = type_.upper()

            for other_type, damage_taken in data["damageTaken"].items():
                if other_type.upper() not in types:
                    continue

                assert damage_taken in {0, 1, 2, 3}, (data["damageTaken"], type_)

                if damage_taken == 0:
                    type_chart[type_][other_type.upper()] = 1
                elif damage_taken == 1:
                    type_chart[type_][other_type.upper()] = 2
                elif damage_taken == 2:
                    type_chart[type_][other_type.upper()] = 0.5
                elif damage_taken == 3:
                    type_chart[type_][other_type.upper()] = 0

            assert set(types).issubset(set(type_chart))

        assert len(type_chart) == len(types)

        for effectiveness in type_chart.values():
            assert len(effectiveness) == len(types)

        return type_chart

    @property
    def _static_files_root(self) -> str:
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), "static")

    @classmethod
    @lru_cache(None)
    def from_gen(cls, gen: int) -> GenData:
        gen_data = GenData(gen)
        cls._gen_data_per_gen[gen] = gen_data

        return gen_data

    @classmethod
    @lru_cache(None)
    def from_format(cls, format: str) -> GenData:
        gen = int(format[3])  # Update when Gen 10 comes
        return cls.from_gen(gen)
