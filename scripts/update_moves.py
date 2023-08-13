import json

from data_script_utils import (
    CURRENT_GEN,
    MAX_MOVE_IDX_PER_GEN,
    STATIC_DATA_ROOT,
    fetch_and_clean_ps_data,
)

data_by_gen = {
    CURRENT_GEN: fetch_and_clean_ps_data(
        "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/moves.ts"
    )
}

for gen in range(1, CURRENT_GEN):
    data_by_gen[gen] = fetch_and_clean_ps_data(
        f"https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/mods/gen{gen}/moves.ts"
    )

if "block" in data_by_gen[2]:
    data_by_gen[2].pop("block")


for gen in range(CURRENT_GEN, 0, -1):
    if gen != CURRENT_GEN:
        new_gen = data_by_gen[gen + 1]
        old_gen = data_by_gen[gen]

        for move, value in new_gen.items():
            if "num" not in value:
                assert "inherit" in value and value["inherit"], (gen, move, value)
            elif value["num"] >= 1000 and gen >= 8:
                pass
            elif value["num"] > MAX_MOVE_IDX_PER_GEN[gen]:
                continue

            if move not in old_gen:
                old_gen[move] = value
            elif old_gen[move].get("inherit", False):
                old_gen[move] = {**value, **old_gen[move]}
                old_gen[move].pop("inherit")

    with open(f"{STATIC_DATA_ROOT}/moves/gen{gen}moves.json", "w+") as f:
        f.write(json.dumps(data_by_gen[gen], indent=4, sort_keys=True))
