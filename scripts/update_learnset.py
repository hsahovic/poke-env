import os

from data_script_utils import STATIC_DATA_ROOT, fetch_and_clean_ps_data

# Fetch latest version
data = fetch_and_clean_ps_data(
    "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/learnsets.ts",
    deserialize=False,
)

with open(os.path.join(STATIC_DATA_ROOT, "learnset.json"), "w+") as f:
    f.write(data)
