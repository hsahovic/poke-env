import json
import os
import re
from copy import deepcopy

try:
    from .data_script_utils import (
        CURRENT_GEN,
        MAX_MON_IDX_PER_GEN,
        STATIC_DATA_ROOT,
        fetch_and_clean_ps_data,
    )
except ImportError:
    from data_script_utils import (
        CURRENT_GEN,
        MAX_MON_IDX_PER_GEN,
        STATIC_DATA_ROOT,
        fetch_and_clean_ps_data,
    )


def _to_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def resolve_pokedex_entry_num(value, data):
    if "num" in value:
        return value["num"]

    if value.get("isCosmeticForme", False):
        base_species = data.get(_to_id(value["baseSpecies"]))
        if base_species is not None:
            return base_species.get("num")

    return None


def merge_next_gen_data_into_this_gen_data(this_gen_data, next_gen_data, gen):
    for mon, value in next_gen_data.items():
        value_num = resolve_pokedex_entry_num(value, next_gen_data)
        if value_num is None:
            if value.get("inherit", False):
                continue

            raise AssertionError(f"Unhandled pokedex entry without num: {mon} {value}")
        elif value_num > MAX_MON_IDX_PER_GEN[gen]:
            continue

        if mon not in this_gen_data:
            this_gen_data[mon] = value
        elif this_gen_data[mon].get("inherit", False):
            this_gen_data[mon] = {**value, **this_gen_data[mon]}
            this_gen_data[mon].pop("inherit")

        if gen == 4 and "abilities" in this_gen_data[mon]:
            this_gen_data[mon]["abilities"].pop("H", None)

    return this_gen_data


data_by_gen = {
    CURRENT_GEN: fetch_and_clean_ps_data(
        "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/pokedex.ts"
    )
}

for gen in range(CURRENT_GEN - 1, 0, -1):
    next_gen_data = deepcopy(data_by_gen[gen + 1])
    this_gen_data = fetch_and_clean_ps_data(
        f"https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/mods/gen{gen}/pokedex.ts"
    )

    data_by_gen[gen] = merge_next_gen_data_into_this_gen_data(
        this_gen_data, next_gen_data, gen
    )

for gen, data in data_by_gen.items():
    with open(
        os.path.join(STATIC_DATA_ROOT, "pokedex", f"gen{gen}pokedex.json"), "w+"
    ) as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))
