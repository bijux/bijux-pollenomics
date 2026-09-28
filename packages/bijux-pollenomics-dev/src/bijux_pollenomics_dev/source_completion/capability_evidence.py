"""Re-audit every governed source capability against present evidence bytes."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT = Path("data/source_family_contracts.json")
STAGES = Path("data/source_family_evidence_stage_matrix.json")


def _digest(path: Path) -> dict[str, int | str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"bytes": size, "sha256": digest.hexdigest()}


def _read(root: Path, relative: Path) -> tuple[dict[str, Any], dict[str, int | str]]:
    path = root / relative
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"Expected object: {relative}")
    return value, {
        "path": relative.as_posix(),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _safe_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if (
        not path.parts
        or path.is_absolute()
        or ".." in path.parts
        or path.parts[0] not in {"data", "docs"}
        or not (root / path).resolve().is_relative_to(root.resolve())
    ):
        raise ValueError(f"Unsafe capability evidence path: {relative}")
    return root / path


def derive(
    root: Path,
    contract: dict[str, Any],
    stage: dict[str, Any],
) -> dict[str, Any]:
    """Require every source/dimension and retain absent evidence as absent."""
    capability = contract["capability_contract"]
    audit = stage["capability_materialization_audit"]
    if (
        capability["schema_version"] != "source-capability-contract.v1"
        or audit["schema_version"] != "source-capability-materialization-audit.v1"
    ):
        raise ValueError("Capability contract or audit schema changed")
    sources = capability["sources"]
    dimensions = capability["dimensions"]
    rows = audit["rows"]
    if (
        len(sources) != capability["source_count"]
        or len(dimensions) != capability["dimension_count"]
        or len(rows) != audit["row_count"]
        or len(sources) != audit["source_count"]
        or len(dimensions) != audit["dimension_count"]
    ):
        raise ValueError("Capability source/dimension denominator changed")
    source_keys = [source["source_key"] for source in sources]
    if len(source_keys) != len(set(source_keys)) or len(dimensions) != len(
        set(dimensions)
    ):
        raise ValueError("Capability source or dimension duplicated")
    expected = {
        (source, dimension) for source in source_keys for dimension in dimensions
    }
    actual = [(row["source_key"], row["dimension"]) for row in rows]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Capability audit cube is incomplete or duplicated")
    contract_by_source = {source["source_key"]: source for source in sources}
    path_digests: dict[str, dict[str, int | str]] = {}
    missing_paths: set[str] = set()
    materialization_counts: Counter[str] = Counter()
    support_counts: Counter[str] = Counter()
    findings = []
    for row in sorted(rows, key=lambda item: (item["source_key"], item["dimension"])):
        source = contract_by_source[row["source_key"]]
        dimension = row["dimension"]
        support = source["support_by_dimension"][dimension]
        declared_paths = source["evidence_paths_by_dimension"][dimension]
        if row["support"] != support or row["evidence_paths"] != declared_paths:
            raise ValueError(
                f"Capability support/evidence differs: {row['source_key']}:{dimension}"
            )
        if len(declared_paths) != len(set(declared_paths)):
            raise ValueError("Duplicate capability evidence path")
        present = [name for name in declared_paths if _safe_path(root, name).is_file()]
        missing = [name for name in declared_paths if name not in present]
        missing_paths.update(missing)
        if (
            present != row["present_evidence_paths"]
            or missing != row["missing_evidence_paths"]
            or row["evidence_file_count"] != len(present)
            or row["required_evidence_count"] != len(declared_paths)
        ):
            raise ValueError(
                f"Capability materialization differs: {row['source_key']}:{dimension}"
            )
        materialization = (
            "not_applicable"
            if support == "unsupported"
            else "complete"
            if present and not missing
            else "partial"
            if present
            else "missing"
        )
        if row["materialization"] != materialization:
            raise ValueError(
                f"Capability materialization status differs: {row['source_key']}:{dimension}"
            )
        if support == "unsupported" and declared_paths:
            raise ValueError("Unsupported capability has evidence paths")
        if any(
            value is not None
            and (not isinstance(value, int) or isinstance(value, bool) or value < 0)
            for value in row["coverage_metrics"].values()
        ):
            raise ValueError("Capability coverage metric invalid")
        for name in present:
            if name not in path_digests:
                path_digests[name] = _digest(_safe_path(root, name))
        support_counts[support] += 1
        materialization_counts[materialization] += 1
        findings.append(
            {
                "source_key": row["source_key"],
                "dimension": dimension,
                "support": support,
                "materialization": materialization,
                "present_evidence_paths": present,
                "missing_evidence_paths": missing,
                "coverage_metrics": row["coverage_metrics"],
                "reason_codes": row["reason_codes"],
                "human_review_required": row["human_review_required"],
            }
        )
    return {
        "schema_version": "source-capability-evidence-review.v1",
        "requirement_id": "SRC-001",
        "source_count": len(sources),
        "dimension_count": len(dimensions),
        "audit_row_count": len(findings),
        "support_counts": dict(sorted(support_counts.items())),
        "materialization_counts": dict(sorted(materialization_counts.items())),
        "evidence_path_count": len(path_digests),
        "missing_evidence_path_count": len(missing_paths),
        "missing_evidence_paths": sorted(missing_paths),
        "human_review_required_row_count": sum(
            bool(row["human_review_required"]) for row in findings
        ),
        "evidence_paths": [
            {"path": name, **identity}
            for name, identity in sorted(path_digests.items())
        ],
        "rows": findings,
        "scientific_admission": "unchanged_source_specific_review_required",
    }


def build(root: Path, output: Path) -> dict[str, Any]:
    contract, contract_identity = _read(root, CONTRACT)
    stage, stage_identity = _read(root, STAGES)
    report = derive(root, contract, stage)
    report["inputs"] = [contract_identity, stage_identity]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.repository.resolve(), args.output.resolve())
    print(
        json.dumps(
            {
                "sources": report["source_count"],
                "rows": report["audit_row_count"],
                "evidence_paths": report["evidence_path_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
