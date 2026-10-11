"""Retain source-wide Neotoma pollen prerequisite decisions without admission."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.analysis.lra.materialization.api import (
    inspect_neotoma_lra_pollen_screen,
)

from .writer_execution import arguments, confined_paths, write_new


def run(repository: Path, output: Path) -> None:
    """Retain source-wide Neotoma pollen prerequisite decisions without admission."""
    _, raw, relational, destination = confined_paths(repository, output)
    result = inspect_neotoma_lra_pollen_screen(raw_root=raw, normalized_root=relational)
    content = (
        json.dumps(
            json.loads(result.canonical_json),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    write_new(destination, content)


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and retain source-wide Neotoma pollen prerequisite decisions without admission."""
    run(*arguments(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
