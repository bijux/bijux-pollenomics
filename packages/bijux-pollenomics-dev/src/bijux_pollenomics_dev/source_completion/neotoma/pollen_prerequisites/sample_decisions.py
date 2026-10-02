"""Retain source-wide Neotoma pollen prerequisite decisions without admission."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.analysis.lra.materialization.api import (
    inspect_neotoma_lra_pollen_screen,
)

from .writer_execution import arguments, confined_paths, write_new


def run(repository: Path, output: Path) -> None:
    _, raw, relational, destination = confined_paths(repository, output)
    result = inspect_neotoma_lra_pollen_screen(raw_root=raw, normalized_root=relational)
    write_new(destination, result.canonical_json)


def main(argv: list[str] | None = None) -> int:
    run(*arguments(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
