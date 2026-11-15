import json
from pathlib import Path

try:
    from .data_script_utils import (
        CURRENT_GEN,
        STATIC_DATA_ROOT,
        fetch_and_clean_ps_data,
    )
except ImportError:
    from data_script_utils import (
        CURRENT_GEN,
        STATIC_DATA_ROOT,
        fetch_and_clean_ps_data,
    )


def main():
    root = Path(STATIC_DATA_ROOT) / "items"
    root.mkdir(exist_ok=True)
    base_url = "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data"
    items = fetch_and_clean_ps_data(f"{base_url}/items.ts")
    for gen in range(CURRENT_GEN, 0, -1):
        if gen < CURRENT_GEN:
            overrides = fetch_and_clean_ps_data(f"{base_url}/mods/gen{gen}/items.ts")
            for name, value in overrides.items():
                value = value.copy()
                inherit = value.pop("inherit", False)
                items[name] = {**items[name], **value} if inherit else value
        items = {name: value for name, value in items.items() if value["gen"] <= gen}
        with (root / f"gen{gen}items.json").open("w") as f:
            json.dump(items, f, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()
