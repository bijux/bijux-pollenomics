"""Retain source dataset attribution leads without rights or publication approval."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
from bijux_pollenomics.analysis.lra.materialization.neotoma.taxon_provenance import (
    attribute_neotoma_priority_datasets,
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
PRIORITY = Path("docs/report/source-relations/neotoma/taxon-priority/priority.json")


def run(repository: Path, output: Path) -> None:
    """Retain source dataset attribution leads without rights or publication approval."""
    repository, raw, relational, destination = confined_paths(repository, output)
    evidence = read_neotoma_evidence(raw, relational)
    screen = retained_object(repository, SCREEN)
    review = retained_object(repository, REVIEW)
    priority = retained_object(repository, PRIORITY)
    attribution = attribute_neotoma_priority_datasets(
        evidence, screen, review, priority
    )
    write_new(destination, canonical_bytes(attribution))


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and retain source dataset attribution leads without rights or publication approval."""
    run(*arguments(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
