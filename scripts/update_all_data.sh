#!/usr/bin/env bash

set -euo pipefail

uv run python scripts/update_learnset.py
uv run python scripts/update_moves.py
uv run python scripts/update_move_aliases.py
uv run python scripts/update_pokedex.py
