#!/usr/bin/env python3
"""Lightweight docs link validation for repository-local references.

Checks:
- GitHub blob links pointing to this repository resolve to existing local files.
- Relative markdown links in docs notebooks resolve to existing local files.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs" / "source"
BLOB_PREFIX = "https://github.com/hsahovic/poke-env/blob/master/"

BLOB_LINK_RE = re.compile(
    r"https://github\.com/hsahovic/poke-env/blob/master/([^\s`)<>'\"]+)"
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _iter_rst_files() -> Iterable[Path]:
    yield from DOCS_ROOT.rglob("*.rst")


def _iter_notebook_files() -> Iterable[Path]:
    yield from DOCS_ROOT.rglob("*.ipynb")


def _strip_fragment_and_query(link: str) -> str:
    link = link.split("#", 1)[0]
    link = link.split("?", 1)[0]
    return link


def _check_blob_links(path: Path, text: str, errors: list[str]):
    for match in BLOB_LINK_RE.finditer(text):
        rel_path = _strip_fragment_and_query(match.group(1))
        candidate = ROOT / rel_path
        if not candidate.exists():
            errors.append(
                f"{path}: broken repo blob link target '{rel_path}' (missing locally)"
            )


def _check_notebook_relative_links(path: Path, errors: list[str]):
    with path.open(encoding="utf-8") as f:
        notebook = json.load(f)

    for idx, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") != "markdown":
            continue
        text = "".join(cell.get("source", []))
        for match in MARKDOWN_LINK_RE.finditer(text):
            link = match.group(1).strip()
            if not link or link.startswith("#"):
                continue
            if "://" in link or link.startswith("mailto:"):
                continue

            rel = _strip_fragment_and_query(link)
            candidate = (path.parent / rel).resolve()
            if not candidate.exists():
                errors.append(
                    f"{path}: markdown cell {idx} points to missing relative target '{link}'"
                )


def main() -> int:
    errors: list[str] = []

    for rst in _iter_rst_files():
        text = rst.read_text(encoding="utf-8")
        _check_blob_links(rst, text, errors)

    for notebook in _iter_notebook_files():
        text = notebook.read_text(encoding="utf-8")
        _check_blob_links(notebook, text, errors)
        _check_notebook_relative_links(notebook, errors)

    if errors:
        print("Documentation link checks failed:\n")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Documentation link checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
