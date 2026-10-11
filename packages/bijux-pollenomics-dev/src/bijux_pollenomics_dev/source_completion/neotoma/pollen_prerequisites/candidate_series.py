"""Retain the fixed sixteen-sample Neotoma source series without LRA admission."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.analysis.lra.materialization.api import (
    inspect_neotoma_lra_candidate_series,
)

from .writer_execution import arguments, confined_paths, write_new

SAMPLE_IDS = tuple(f"neotoma:sample:{number}" for number in range(355236, 355252))


def run(repository: Path, output: Path) -> None:
    """Retain the fixed sixteen-sample Neotoma source series without LRA admission."""
    _, raw, relational, destination = confined_paths(repository, output)
    result = inspect_neotoma_lra_candidate_series(
        raw_root=raw, normalized_root=relational, selected_sample_ids=SAMPLE_IDS
    )
    write_new(destination, result.canonical_json)


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and retain the fixed sixteen-sample Neotoma source series without LRA admission."""
    run(*arguments(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
