import json

from data_script_utils import (
    CURRENT_GEN,
    STATIC_DATA_ROOT,
    fetch_and_clean_ps_data,
)

data_by_gen = {
    CURRENT_GEN: fetch_and_clean_ps_data(
        "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/items.ts"
    )
}

for gen in range(1, CURRENT_GEN):
    data_by_gen[gen] = fetch_and_clean_ps_data(
        f"https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/mods/gen{gen}/items.ts"
    )

for gen in range(CURRENT_GEN, 0, -1):
    with open(f"{STATIC_DATA_ROOT}/items/gen{gen}items.json", "w+") as f:
        f.write(json.dumps(data_by_gen[gen], indent=4, sort_keys=True))
