"""Publish capability and materialization without conflating either with admission."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any

from .capability_evidence import CONTRACT, STAGES, _read, derive

REVIEW = Path("docs/report/source-relations/source-capability-evidence/report.json")


def render(report: dict[str, Any], review_sha256: str) -> str:
    """Render all source dimensions with independent support and presence states."""
    rows = report["rows"]
    if not isinstance(rows, list) or len(rows) != report["audit_row_count"]:
        raise ValueError("Capability review rows changed")
    by_source: dict[str, Counter[str]] = defaultdict(Counter)
    lines = [
        "---",
        "title: Source Capability and Materialization",
        "audience: reader",
        "type: reference",
        "status: canonical",
        "owner: bijux-pollenomics-docs",
        "last_reviewed: 2026-09-28",
        "---",
        "",
        "# Source Capability and Materialization",
        "",
        "This generated page separates what each governed source can support from "
        "which declared evidence files are present. The [evidence review]"
        "(../../../report/source-relations/source-capability-evidence/README.md) "
        "checks every declared path against current bytes. A complete file set "
        "does not admit a scientific claim, and a missing file does not make a "
        "source dimension inherently unsupported.",
        "",
        f"The matrix has {report['source_count']} source families, "
        f"{report['dimension_count']} dimensions, and {report['audit_row_count']} "
        "source–dimension cells. Each summary count uses cells as its unit.",
        "",
        "| Source | Supported | Partial support | Unsupported | Complete files | Partial files | Missing files | Not applicable | Human review |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Capability review row is not an object")
        source = row["source_key"]
        if not isinstance(source, str):
            raise ValueError("Capability source key changed")
        by_source[source][f"support:{row['support']}"] += 1
        by_source[source][f"materialization:{row['materialization']}"] += 1
        by_source[source]["review"] += bool(row["human_review_required"])
    for source, counts in sorted(by_source.items()):
        values = [
            counts[key]
            for key in (
                "support:supported",
                "support:partial",
                "support:unsupported",
                "materialization:complete",
                "materialization:partial",
                "materialization:missing",
                "materialization:not_applicable",
                "review",
            )
        ]
        lines.append("| " + " | ".join([source, *map(str, values)]) + " |")
    lines.extend(
        [
            "",
            "## Each source dimension",
            "",
            "| Source | Dimension | Source support | File materialization | Present paths | Missing paths | Review |",
            "| --- | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Capability review row is not an object")
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["source_key"]),
                    str(row["dimension"]),
                    str(row["support"]),
                    str(row["materialization"]),
                    str(len(row["present_evidence_paths"])),
                    str(len(row["missing_evidence_paths"])),
                    "required" if row["human_review_required"] else "not flagged",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "The source contract and materialization audit assign these states. "
            "The [retained machine-readable review]"
            "(../../../report/source-relations/source-capability-evidence/report.json) "
            "names the evidence paths, file digests, coverage metrics, and reason "
            "codes for each cell. Source-specific lifecycle and four-country "
            "availability remain in the [source-family matrix]"
            "(source-family-matrix.md) and [country limitations]"
            "(country-source-limitations.md).",
            "",
            f"Review SHA-256: `{review_sha256}`.",
            "",
        ]
    )
    return "\n".join(lines)


def require_current_review(
    current: dict[str, Any],
    reviewed: dict[str, Any],
    input_identities: list[dict[str, int | str]],
) -> None:
    """Refuse a retained report whose inputs or evidence bytes have drifted."""
    if reviewed.get("inputs") != input_identities:
        raise ValueError("Capability evidence review input identities are stale")
    for field, value in current.items():
        if value != reviewed.get(field):
            raise ValueError(f"Capability evidence review is stale: {field}")


def run(repository: Path, output: Path) -> Path:
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    contract, contract_identity = _read(repository, CONTRACT)
    stage, stage_identity = _read(repository, STAGES)
    current = derive(repository, contract, stage)
    review_path = repository / REVIEW
    review_bytes = review_path.read_bytes()
    reviewed = json.loads(review_bytes)
    require_current_review(current, reviewed, [contract_identity, stage_identity])
    output.mkdir(parents=True)
    path = output / "source-capability-and-materialization.md"
    path.write_text(render(current, hashlib.sha256(review_bytes).hexdigest()))
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.repository, args.output))


if __name__ == "__main__":
    main()
