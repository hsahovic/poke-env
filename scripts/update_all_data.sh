#!/usr/bin/env bash

set -euo pipefail

python scripts/update_learnset.py
python scripts/update_moves.py
python scripts/update_pokedex.py
