"""Render source-bound Nordic country limitations from the governed ledgers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.source_completion.source_capability import (
    DIMENSIONS,
    FAMILIES,
    _read,
    derive,
)

STAGE_PATH = Path("data/source_family_evidence_stage_matrix.json")
COVERAGE_PATH = Path("data/country_dimension_coverage.json")
COUNTRY_LABELS = {"SE": "Sweden", "DK": "Denmark", "NO": "Norway", "FI": "Finland"}
FAMILY_LABELS = {
    "aadr": "AADR",
    "animal_adna": "animal aDNA",
    "boundaries": "boundaries",
    "empd2": "EMPD2",
    "hyde": "HYDE",
    "landclim": "LandClim",
    "neotoma": "Neotoma",
    "nfi": "NFI",
    "raa": "RAÄ",
    "sead": "SEAD",
    "svar": "SVAR",
}


def _count_summary(counts: dict[str, int | None]) -> str:
    present = [
        f"{key.replace('_', ' ')} {value:,}"
        for key, value in sorted(counts.items())
        if value is not None
    ]
    return "; ".join(present) if present else "count unresolved"


def _cell(cell: dict[str, Any]) -> str:
    return f"`{cell['availability_status']}`; {_count_summary(cell['counts'])}"


def render(
    stage: dict[str, Any], coverage: dict[str, Any], identities: dict[str, str]
) -> str:
    """Keep source, assignment and publication denominators visibly distinct."""
    report = derive(stage, coverage)
    by_key = {
        (cell["source_family"], cell["country_code"], cell["country_dimension"]): cell
        for cell in coverage["cells"]
    }
    lines = [
        "---",
        "title: Nordic Source and Country Limitations",
        "audience: reader",
        "type: reference",
        "status: canonical",
        "owner: bijux-pollenomics-docs",
        "last_reviewed: 2026-09-28",
        "---",
        "",
        "# Nordic Source and Country Limitations",
        "",
        "This table is generated from the repository source-stage matrix "
        "`data/source_family_evidence_stage_matrix.json` and country-dimension "
        "ledger `data/country_dimension_coverage.json`. "
        "It retains source-reported coverage, governed country assignment, and "
        "publication as separate claims. Each count belongs to its named dimension "
        "and observation unit; `count unresolved` is not zero. An `available_collected` "
        "publication is a product record, not universal scientific admission.",
        "",
        f"The ledgers cover {report['source_families']} families, {len(COUNTRY_LABELS)} Nordic "
        f"countries plus `UNASSIGNED` and `OUTSIDE`, and {report['country_cells']} "
        "family/partition/dimension cells. The source-stage matrix distinguishes "
        "capability from materialization across "
        f"{report['source_capability_audit_rows']} audit rows. Country cells use "
        "the ledger's `source` resolution; this says nothing about site or grid "
        "precision within a country.",
        "",
        "| Family | Country | Source-reported | Governed assignment | Publication | Refusal and qualification codes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for family in FAMILIES:
        for country in COUNTRY_LABELS:
            cells = [by_key[family, country, dim] for dim in DIMENSIONS]
            if any(cell["resolution"] != "source" for cell in cells):
                raise ValueError(
                    "Country cell resolution changed; revise the public interpretation"
                )
            reasons = sorted({code for cell in cells for code in cell["reason_codes"]})
            lines.append(
                "| "
                + " | ".join(
                    [FAMILY_LABELS[family], COUNTRY_LABELS[country]]
                    + [_cell(cell) for cell in cells]
                    + [", ".join(f"`{code}`" for code in reasons) or "—"]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## How to read the limits",
            "",
            "A source-reported zero, a governed assignment, and a published member "
            "can all coexist. SEAD reports zero country cells in its native source "
            "partition while governed and published site assignments are nonzero. "
            "EMPD2 source metadata is partial, yet its governed country assignment "
            "and publication remain blocked. HYDE private archive custody does not "
            "satisfy the governed repository or country projection contracts. "
            "NFI country access leads do not become admitted pollen–vegetation pairs.",
            "",
            "For lifecycle stages and source roles, see the [source-family matrix](source-family-matrix.md). "
            "For count definitions and denied inferences, see [coverage and naming](../overview/coverage-and-naming.md). "
            "The [retained replay](../../../report/regions/nordic/source-capability/README.md) "
            "includes all six partitions and parent-artifact identities.",
            "",
            "## Bound input identity",
            "",
            f"- `{STAGE_PATH}` SHA-256 `{identities[STAGE_PATH.as_posix()]}`",
            f"- `{COVERAGE_PATH}` SHA-256 `{identities[COVERAGE_PATH.as_posix()]}`",
            "",
            "From the repository root, regenerate to an absent artifact directory:",
            "",
            "```sh",
            "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \\",
            "  bijux_pollenomics_dev.source_completion.country_limitations \\",
            "  --repository . --output artifacts/jobs/country-source-limitations/reproduction",
            "```",
            "",
            "The command verifies every parent artifact digest. Compare its Markdown "
            "with this governed page before replacing the page.",
            "",
        ]
    )
    return "\n".join(lines)


def run(repository: Path, output: Path) -> Path:
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    stage, stage_sha = _read(repository / STAGE_PATH)
    coverage, coverage_sha = _read(repository / COVERAGE_PATH)
    for item in coverage["input_artifacts"]:
        path = repository / item["path"]
        payload = path.read_bytes()
        if (
            len(payload) != item["byte_count"]
            or hashlib.sha256(payload).hexdigest() != item["sha256"]
        ):
            raise ValueError(f"Country coverage parent changed: {item['path']}")
    identities = {
        STAGE_PATH.as_posix(): stage_sha,
        COVERAGE_PATH.as_posix(): coverage_sha,
    }
    result = render(stage, coverage, identities)
    if any(
        hashlib.sha256((repository / path).read_bytes()).hexdigest() != digest
        for path, digest in identities.items()
    ):
        raise ValueError("Source capability inputs changed during derivation")
    output.mkdir(parents=True)
    destination = output / "country-source-limitations.md"
    destination.write_text(result)
    (output / "input-identity.json").write_text(json.dumps(identities, indent=2) + "\n")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
