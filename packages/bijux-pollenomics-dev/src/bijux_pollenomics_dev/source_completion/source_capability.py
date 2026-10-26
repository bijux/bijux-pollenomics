"""Read the governed source-stage and country ledgers without merging meanings."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import stat
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
AVAILABILITY_STATUSES = frozenset(
    {
        "available_collected",
        "available_not_collected",
        "available_partial",
        "blocked",
        "not_applicable",
        "not_available_from_source",
        "unresolved",
        "zero_observations",
    }
)
NULL_ONLY_STATUSES = frozenset(
    {
        "available_not_collected",
        "blocked",
        "not_applicable",
        "not_available_from_source",
    }
)
SOURCE_ROLE_BOUNDARIES = {
    "landclim": "primary_context",
    "sead": "contextual_domain",
    "raa": "contextual_domain",
    "hyde": "external_model_comparison",
}


def _validate_status_counts(status: object, counts: dict[str, Any]) -> None:
    """Keep absent, unavailable, blocked and observed-zero states distinct."""
    if not isinstance(status, str) or status not in AVAILABILITY_STATUSES:
        raise ValueError(f"Unknown country coverage availability status: {status}")
    values = [value for value in counts.values() if value is not None]
    if status in NULL_ONLY_STATUSES and values:
        raise ValueError(f"{status} country coverage must not carry numeric counts")
    if status == "zero_observations" and (not values or any(values)):
        raise ValueError("Explicit zero country coverage requires only observed zeros")
    if (
        status in {"available_collected", "available_partial", "unresolved"}
        and not values
    ):
        raise ValueError(f"{status} country coverage requires source counts")


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


def _parent_specs(coverage: dict[str, Any]) -> tuple[tuple[str, int, str], ...]:
    """Freeze exact declared parent identities before derivation can run."""
    items = coverage.get("input_artifacts")
    if not isinstance(items, list) or not items:
        raise ValueError("Country coverage parent inventory missing")
    specs: list[tuple[str, int, str]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Country coverage parent identity invalid")
        relative = item.get("path")
        size = item.get("byte_count")
        digest = item.get("sha256")
        if (
            not isinstance(relative, str)
            or relative.startswith("/")
            or "\\" in relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))
            or type(size) is not int
            or size < 0
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError("Country coverage parent identity invalid")
        specs.append((relative, size, digest))
    if len({path for path, _, _ in specs}) != len(specs):
        raise ValueError("Country coverage parent paths are not unique")
    return tuple(specs)


def _verify_parents(repository: Path, specs: tuple[tuple[str, int, str], ...]) -> None:
    """Check each confined parent before derivation and again before publication."""
    for relative, size, digest in specs:
        path = repository
        try:
            for part in relative.split("/")[:-1]:
                path /= part
                if not stat.S_ISDIR(path.lstat().st_mode):
                    raise ValueError(f"Country coverage parent is linked: {relative}")
            path /= relative.split("/")[-1]
            if not stat.S_ISREG(path.lstat().st_mode):
                raise ValueError(f"Country coverage parent is linked: {relative}")
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(
                f"Country coverage parent unavailable: {relative}"
            ) from error
        if len(payload) != size or hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError(f"Country coverage parent changed: {relative}")


def _stage_projection(family: str, source: dict[str, Any]) -> dict[str, Any]:
    result = {
        "source_family": family,
        **{
            key: source[key]
            for key in (
                "evidence_role",
                "raw_status",
                "normalized_status",
                "reviewed_status",
                "published_status",
                "authority_status",
                "blocking_reasons",
            )
        },
    }
    if "source_context_profile" in source:
        profile = source["source_context_profile"]
        if (
            family != "raa"
            or not isinstance(profile, dict)
            or profile.get("source_id") != "raa/lamningar-v1"
            or profile.get("evidence_role") != "source_context_only"
            or profile.get("status") not in {"admitted_source_context", "not_admitted"}
            or any(
                profile.get(key) is not False
                for key in (
                    "scientific_admission",
                    "chronology_admission",
                    "event_admission",
                    "legacy_density_admission",
                    "publication_admission",
                    "archaeological_interpretation_admission",
                )
            )
        ):
            raise ValueError("RAÄ native source context scope changed")
        if profile["status"] == "admitted_source_context" and (
            type(profile.get("source_record_count")) is not int
            or profile["source_record_count"] < 0
        ):
            raise ValueError("RAÄ native source context count invalid")
        result["source_context_profile"] = deepcopy(profile)
    return result


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
    by_key = dict(zip(actual, cells, strict=True))
    by_stage = {row["source_key"]: row for row in rows}
    for family, role in SOURCE_ROLE_BOUNDARIES.items():
        if by_stage[family]["evidence_role"] != role:
            raise ValueError(f"Source evidence role changed: {family}")
    for country in COUNTRIES:
        for dimension in DIMENSIONS:
            raa = by_key[("raa", country, dimension)]
            expected_status = (
                "blocked" if country == "SE" else "not_available_from_source"
            )
            if raa["availability_status"] != expected_status:
                raise ValueError(f"National RAÄ country scope changed: {country}")
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
                _validate_status_counts(cell["availability_status"], counts)
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
            _stage_projection(family, by_stage[family]) for family in FAMILIES
        ],
        "coverage_build_id": coverage["build_id"],
    }


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Read the governed source-stage and country ledgers without merging meanings."""
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    stage, stage_sha = _read(repository / STAGE_PATH)
    coverage, coverage_sha = _read(repository / COVERAGE_PATH)
    parents = _parent_specs(coverage)
    _verify_parents(repository, parents)
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
    _verify_parents(repository, parents)
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return report


def main() -> int:
    """Run the CLI to read the governed source-stage and country ledgers without merging meanings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
