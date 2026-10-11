"""Retain scoped Neotoma concept-priority workload without taxon approval."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
from bijux_pollenomics.analysis.lra.materialization.neotoma.taxon_priority import (
    prioritize_neotoma_candidate_taxa,
)
from bijux_pollenomics.analysis.lra.materialization.reading import (
    read_neotoma_evidence,
)

from .writer_execution import (
    arguments,
    confined_paths,
    retained_object,
    write_new,
)

SCREEN = Path("docs/report/source-relations/neotoma/pollen-screen/report.json")
REVIEW = Path("data/neotoma/review/source_taxon_concepts.json")


def run(repository: Path, output: Path) -> None:
    """Retain scoped Neotoma concept-priority workload without taxon approval."""
    repository, raw, relational, destination = confined_paths(repository, output)
    evidence = read_neotoma_evidence(raw, relational)
    screen = retained_object(repository, SCREEN)
    review = retained_object(repository, REVIEW)
    priority = prioritize_neotoma_candidate_taxa(evidence, screen, review)
    write_new(destination, canonical_bytes(priority))


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and retain scoped Neotoma concept-priority workload without taxon approval."""
    run(*arguments(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
