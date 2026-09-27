"""Read the governed source-stage and country ledgers without merging meanings."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

COUNTRIES = ("SE", "DK", "NO", "FI", "UNASSIGNED", "OUTSIDE")
DIMENSIONS = ("source_reported", "governed_assignment", "publication")
FAMILIES = (
    "aadr",
    "animal_adna",
    "boundaries",
    "empd2",
    "hyde",
    "landclim",
    "neotoma",
    "nfi",
    "raa",
    "sead",
    "svar",
)
STAGE_PATH = Path("data/source_family_evidence_stage_matrix.json")
COVERAGE_PATH = Path("data/country_dimension_coverage.json")


def _object_unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _read(path: Path) -> tuple[dict[str, Any], str]:
    data = path.read_bytes()
    value = json.loads(data, object_pairs_hook=_object_unique)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value, hashlib.sha256(data).hexdigest()


def derive(stage: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    """Require a complete Cartesian inventory and retain each native dimension."""
    if stage.get("schema_version") != "source-family-evidence-stage-matrix.v2":
        raise ValueError("Source stage schema changed")
    rows = stage.get("rows")
    audit = stage.get("capability_materialization_audit")
    if not isinstance(rows, list) or stage.get("row_count") != len(rows):
        raise ValueError("Source stage row denominator changed")
    if {row["source_key"] for row in rows} != set(FAMILIES) or len(rows) != len(
        FAMILIES
    ):
        raise ValueError("Source stage family inventory changed")
    if not isinstance(audit, dict) or audit.get("source_count") != len(FAMILIES):
        raise ValueError("Source capability audit unavailable")
    audit_rows = audit.get("rows")
    dimension_count = audit.get("dimension_count")
    if (
        not isinstance(audit_rows, list)
        or audit.get("row_count") != len(audit_rows)
        or not isinstance(dimension_count, int)
        or dimension_count * len(FAMILIES) != len(audit_rows)
        or len({(row["source_key"], row["dimension"]) for row in audit_rows})
        != len(audit_rows)
    ):
        raise ValueError("Source capability audit denominator changed")
    if coverage.get("schema_version") != "country-dimension-coverage-ledger.v1":
        raise ValueError("Country coverage schema changed")
    cells = coverage.get("cells")
    if not isinstance(cells, list) or coverage.get("cell_count") != len(cells):
        raise ValueError("Country coverage cell denominator changed")
    expected = {
        (family, country, dimension)
        for family in FAMILIES
        for country in COUNTRIES
        for dimension in DIMENSIONS
    }
    actual = [
        (cell["source_family"], cell["country_code"], cell["country_dimension"])
        for cell in cells
    ]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Country coverage Cartesian inventory changed")
    by_key = {key: cell for key, cell in zip(actual, cells, strict=True)}
    by_stage = {row["source_key"]: row for row in rows}
    entries = []
    for family in FAMILIES:
        for country in COUNTRIES:
            dimensions = {}
            for dimension in DIMENSIONS:
                cell = by_key[(family, country, dimension)]
                counts = cell["counts"]
                if not isinstance(counts, dict) or any(
                    value is not None
                    and (
                        isinstance(value, bool)
                        or not isinstance(value, int)
                        or value < 0
                    )
                    for value in counts.values()
                ):
                    raise ValueError("Country coverage counts invalid")
                dimensions[dimension] = {
                    "availability_status": cell["availability_status"],
                    "lifecycle_status": cell["lifecycle_status"],
                    "counts": counts,
                    "reason_codes": cell["reason_codes"],
                    "source_snapshot_id": cell["source_snapshot_id"],
                    "boundary_artifact_digest": cell["boundary_artifact_digest"],
                }
            entries.append(
                {
                    "source_family": family,
                    "country_code": country,
                    "dimensions": dimensions,
                }
            )
    support = Counter((row["support"], row["materialization"]) for row in audit_rows)
    return {
        "schema_version": "source-country-capability-consumer.v1",
        "posture": "source-stage and country-dimension replay; no new scientific admission",
        "source_families": len(FAMILIES),
        "country_partitions": len(COUNTRIES),
        "country_dimensions": len(DIMENSIONS),
        "source_capability_audit_rows": len(audit_rows),
        "source_capability_support_materialization": [
            {"support": support_key, "materialization": materialization, "rows": count}
            for (support_key, materialization), count in sorted(support.items())
        ],
        "country_cells": len(cells),
        "country_entries": entries,
        "source_stages": [
            {
                "source_family": family,
                "evidence_role": by_stage[family]["evidence_role"],
                "raw_status": by_stage[family]["raw_status"],
                "normalized_status": by_stage[family]["normalized_status"],
                "reviewed_status": by_stage[family]["reviewed_status"],
                "published_status": by_stage[family]["published_status"],
                "authority_status": by_stage[family]["authority_status"],
                "blocking_reasons": by_stage[family]["blocking_reasons"],
            }
            for family in FAMILIES
        ],
        "coverage_build_id": coverage["build_id"],
    }


def run(repository: Path, output: Path) -> dict[str, Any]:
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
    report = derive(stage, coverage)
    report["inputs"] = {
        STAGE_PATH.as_posix(): stage_sha,
        COVERAGE_PATH.as_posix(): coverage_sha,
    }
    if (
        hashlib.sha256((repository / STAGE_PATH).read_bytes()).hexdigest() != stage_sha
        or hashlib.sha256((repository / COVERAGE_PATH).read_bytes()).hexdigest()
        != coverage_sha
    ):
        raise ValueError("Source capability input changed during derivation")
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
