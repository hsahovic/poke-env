from __future__ import annotations

import os
from typing import Any, Dict, FrozenSet, Optional, Set, Union

import orjson

from poke_env.data.normalize import to_id_str


class GenData:
    __slots__ = (
        "gen",
        "moves",
        "natures",
        "raw_learnset",
        "pokedex",
        "type_chart",
        "learnset",
        "_learnset_cache",
    )

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
        # Keep the new name as an alias while preserving the public learnset
        # attribute's original raw-data semantics.
        self.raw_learnset = self.learnset
        self._learnset_cache: Dict[str, FrozenSet[str]] = {}

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

    def load_learnset(self) -> Dict[str, Dict[str, Any]]:
        with open(os.path.join(self._static_files_root, "learnset.json")) as f:
            return orjson.loads(f.read())

    def load_raw_learnset(self) -> Dict[str, Dict[str, Any]]:
        return self.load_learnset()

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
    def from_gen(cls, gen: int) -> GenData:
        if gen not in cls._gen_data_per_gen:
            cls._gen_data_per_gen[gen] = GenData(gen)
        return cls._gen_data_per_gen[gen]

    @classmethod
    def from_format(cls, format: str) -> GenData:
        gen = int(format[3])  # Update when Gen 10 comes
        return cls.from_gen(gen)

    @classmethod
    def obtain_learnset(cls, pokemon_species: str, gen: int) -> FrozenSet[str]:
        gen_data = cls.from_gen(gen)

        if pokemon_species not in gen_data._learnset_cache:
            gen_data.generate_learnset(pokemon_species)

        return gen_data._learnset_cache[pokemon_species]

    @staticmethod
    def _source_generation(source: Any) -> Optional[int]:
        if isinstance(source, str) and source and source[0].isdigit():
            return int(source[0])
        return None

    def _learnset_for_generation(self, species: str, generation: int) -> Set[str]:
        species_data = self.raw_learnset.get(species, {})
        learnset = species_data.get("learnset")
        if not isinstance(learnset, dict):
            return set()

        available_moves = GenData.from_gen(generation).moves
        result: Set[str] = set()
        for move, sources in learnset.items():
            move_data = available_moves.get(move)
            if (
                not isinstance(move_data, dict)
                or move_data.get("isNonstandard") == "Past"
                or not isinstance(sources, list)
            ):
                continue

            if any(
                (source_generation := self._source_generation(source)) is not None
                and source_generation <= generation
                for source in sources
            ):
                result.add(move)

        return result

    def generate_learnset(self, pokemon_species: str) -> None:
        """
        Update the learnset of the Pokemon based on its species and the gen.

        This function is used to obtain a non empty learnset for the Pokémon
        by going backwards if it has been Dexited. The learnset is not
        available for the Gens 1 and 2 so this function would do nothing
        for those Gens.

        Args:
            - species (str): the species to update the learnset for

        Returns:
            - None: this method updates the learnset in place and does not return anything
        """
        current_gen = self.gen
        learnset: Set[str] = set()

        while current_gen >= 3 and not learnset:
            dex_entry = self.pokedex[pokemon_species]

            # Moveset from the current form
            learnset.update(self._learnset_for_generation(pokemon_species, current_gen))

            # Moveset from the form without the item
            if "species" in dex_entry and ("battleOnly" in dex_entry or not learnset):
                dex_species = to_id_str(dex_entry["species"])
                learnset.update(self._learnset_for_generation(dex_species, current_gen))

            # Moveset from the form it comes from
            if "changesFrom" in dex_entry:
                previous_form = to_id_str(dex_entry["changesFrom"])
                learnset.update(
                    self._learnset_for_generation(previous_form, current_gen)
                )

            # Moveset from its prevolution line
            prevolution = (
                to_id_str(dex_entry["prevo"]) if "prevo" in dex_entry else None
            )
            while prevolution:
                learnset.update(self._learnset_for_generation(prevolution, current_gen))

                prevo_dex_entry = self.pokedex.get(prevolution, {})
                prevolution = (
                    to_id_str(prevo_dex_entry["prevo"])
                    if "prevo" in prevo_dex_entry
                    else None
                )

            current_gen -= 1

        self._learnset_cache[pokemon_species] = frozenset(learnset)
