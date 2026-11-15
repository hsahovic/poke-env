import json
import re
from pathlib import Path

import requests

from poke_env.data.normalize import to_id_str

try:
    from .data_script_utils import STATIC_DATA_ROOT
except ImportError:
    from data_script_utils import STATIC_DATA_ROOT

response = requests.get(
    "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/aliases.ts",
    timeout=10.0,
)
response.raise_for_status()

moves = set()
for path in Path(STATIC_DATA_ROOT, "moves").glob("gen*moves.json"):
    moves.update(json.loads(path.read_text()))

aliases = {}
for line in response.text.split("};", 1)[0].splitlines()[1:]:
    if not line.strip() or line.strip().startswith("//"):
        continue
    match = re.fullmatch(r'\s*"?(\w+)"?:\s*("(?:[^"\\]|\\.)*"),\s*(?://.*)?', line)
    if match is None:
        raise ValueError(f"Unexpected alias data: {line}")
    alias, name = match.groups()
    move_id = to_id_str(json.loads(name))
    if move_id in moves:
        aliases[alias] = move_id

Path(STATIC_DATA_ROOT, "move_aliases.json").write_text(
    json.dumps(aliases, indent=4, sort_keys=True) + "\n"
)
