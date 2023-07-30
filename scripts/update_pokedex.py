import json
import os
from copy import deepcopy

from data_script_utils import (
    CURRENT_GEN,
    MAX_MON_IDX_PER_GEN,
    STATIC_DATA_ROOT,
    fetch_and_clean_ps_data,
)

data_by_gen = {
    CURRENT_GEN: fetch_and_clean_ps_data(
        "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/pokedex.ts"
    )
}


def merge_next_gen_data_into_this_gen_data(this_gen_data, next_gen_data):
    for mon, value in next_gen_data.items():
        if "num" not in value:
            assert mon in {
                "kleavor",
                "basculegion",
                "basculegionf",
                "sneasler",
                "enamorus",
            }
            continue
        elif value["num"] > MAX_MON_IDX_PER_GEN[gen]:
            continue

        if mon not in this_gen_data:
            this_gen_data[mon] = value
        elif this_gen_data[mon].get("inherit", False):
            this_gen_data[mon] = {**value, **this_gen_data[mon]}
            this_gen_data[mon].pop("inherit")

        if gen == 4:
            this_gen_data[mon]["abilities"].pop("H", None)

    return this_gen_data


for gen in range(CURRENT_GEN - 1, 0, -1):
    next_gen_data = deepcopy(data_by_gen[gen + 1])
    this_gen_data = fetch_and_clean_ps_data(
        f"https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/mods/gen{gen}/pokedex.ts"
    )

    data_by_gen[gen] = merge_next_gen_data_into_this_gen_data(
        this_gen_data, next_gen_data
    )

for gen, data in data_by_gen.items():
    with open(
        os.path.join(STATIC_DATA_ROOT, "pokedex", f"gen{gen}pokedex.json"), "w+"
    ) as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))
