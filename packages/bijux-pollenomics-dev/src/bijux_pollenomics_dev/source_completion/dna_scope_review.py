"""Reconcile human and animal ancient-DNA source posture without merging units."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

INPUTS = (
    "data/aadr/v66/release_manifest.json",
    "data/adna/species/homo_sapiens/review/aadr_v66_source_accountability.json",
    "data/adna/governance/animal_sample_foundation_truth.json",
    "data/adna/final/atlas/animal_atlas_point_candidates.json",
    "data/adna/final/atlas/animal_atlas_candidate_accountability.json",
    "docs/report/animal_foundation_validation.json",
)


def _read(root: Path, name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    path = root / name
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {name}")
    return value, {
        "path": name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _source_paths(value: str) -> list[str]:
    paths = [part.strip() for part in value.split(" || ")]
    if not paths or any(
        not part or part.startswith("/") or ".." in Path(part).parts for part in paths
    ):
        raise ValueError("Unsafe source evidence path")
    return [part if part.startswith("data/") else f"data/{part}" for part in paths]


def derive(root: Path, values: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Refuse broken identities; retain explicit unresolved scientific review."""
    release, human, foundation, animal, accountability, validation = (
        values[name] for name in INPUTS
    )
    if release.get("source") != "AADR" or release.get("requested_version") != "v66":
        raise ValueError("Human release identity changed")
    if (
        human.get("source_release") != release["requested_version"]
        or human.get("source_family") != "AADR"
    ):
        raise ValueError("Human accountability release differs")
    if any(
        human.get(key) is not False
        for key in (
            "scientifically_admitted",
            "map_admitted",
            "country_assignment_admitted",
        )
    ):
        raise ValueError("Human source-accountability admission posture changed")
    for item in human["input_artifacts"]:
        path = root / item["path"]
        raw = path.read_bytes()
        if (
            len(raw) != item["byte_count"]
            or hashlib.sha256(raw).hexdigest() != item["sha256"]
        ):
            raise ValueError(f"Human captured input changed: {item['path']}")
    summary = human["accountability_projection"]["summary"]
    denominators = summary["denominators"]
    if denominators["source_row_count"] != sum(
        summary["dataset_counts"]["source_rows"].values()
    ):
        raise ValueError("Human panel source rows do not reconcile")
    if denominators["source_file_count"] != len(release["anno_files"]):
        raise ValueError("Human release member count differs")

    points = animal["rows"]
    audit_rows = accountability["rows"]
    if animal["row_count"] != len(points) or accountability[
        "candidate_row_count"
    ] != len(audit_rows):
        raise ValueError("Animal point or accountability denominator differs")
    audits = {row["evidence_row_id"]: row for row in audit_rows}
    if len(audits) != len(audit_rows) or {
        row["evidence_row_id"] for row in points
    } != set(audits):
        raise ValueError("Animal point/accountability identities differ")
    if not accountability.get("overall_ok") or accountability.get(
        "passed_row_count"
    ) != len(points):
        raise ValueError("Animal point accountability incomplete")
    if foundation["summary"]["sample_row_count"] != validation["sample_row_count"]:
        raise ValueError("Animal foundation denominator differs")
    if validation["atlas_row_count"] != len(points):
        raise ValueError("Animal atlas/foundation denominator differs")
    if len({row["feature_id"] for row in points}) != len(points):
        raise ValueError("Animal feature identities collide")
    sample_ids: set[str] = set()
    scope = Counter[str]()
    chronology = Counter[str]()
    source_path_posture = Counter[str]()
    path_issues: list[dict[str, str]] = []
    source_artifacts: set[str] = set()
    project_papers: set[tuple[str, str]] = set()
    nordic_features = 0
    nordic_sample_ids: set[str] = set()
    for row in points:
        audit = audits[row["evidence_row_id"]]
        if (
            not audit["fully_accountable"]
            or audit["sample_record_ids"] != row["sample_record_ids"]
            or audit["site_record_id"] != row["site_record_id"]
            or audit["project_accession"] != row["primary_project_accession"]
        ):
            raise ValueError("Animal feature loses sample/site/project lineage")
        ids = row["sample_record_ids"]
        if (
            not ids
            or len(ids) != row["sample_count"]
            or any(item in sample_ids for item in ids)
        ):
            raise ValueError("Animal sample identity/count collision")
        sample_ids.update(ids)
        if row["nordic_inclusion"]:
            nordic_features += 1
            nordic_sample_ids.update(ids)
        if (
            not row["paper_doi"]
            or not row["source_locator"]
            or not row["chronology"]["original_text"]
        ):
            raise ValueError(
                "Animal point lacks paper, source locator, or native chronology"
            )
        if (
            not row["chronology"]["dating_basis"]
            or not row["chronology"]["evidence_class"]
        ):
            raise ValueError("Animal chronology basis is missing")
        scope[row["animal_scope"]] += 1
        chronology[row["chronology"]["evidence_class"]] += 1
        project_papers.add((row["primary_project_accession"], row["paper_doi"]))
        for field in ("source_artifact_path", "coordinate_source_artifact_path"):
            choices = _source_paths(row[field])
            present = [name for name in choices if (root / name).is_file()]
            source_artifacts.update(present)
            if len(present) == len(choices):
                source_path_posture["all_paths_present"] += 1
            elif present:
                source_path_posture["partial_alternative_paths"] += 1
                path_issues.append(
                    {
                        "feature_id": row["feature_id"],
                        "field": field,
                        "issue": "partial_alternative_paths",
                    }
                )
            else:
                source_path_posture["no_path_present"] += 1
                path_issues.append(
                    {
                        "feature_id": row["feature_id"],
                        "field": field,
                        "issue": "no_path_present",
                    }
                )
    if source_path_posture["no_path_present"]:
        raise ValueError("Animal point source artifact missing")
    missing_paper = next(
        check
        for check in validation["checks"]
        if check["check_id"] == "sample_paper_linkage_present"
    )
    return {
        "schema_version": "dna-source-scope-review.v1",
        "requirement_id": "SRC-007",
        "human": {
            "source_family": "AADR",
            "release": release["requested_version"],
            "persistent_id": release["persistent_id"],
            "source_rows": denominators["source_row_count"],
            "genetic_ids": denominators["genetic_id_count"],
            "annotation_members": summary["dataset_counts"]["source_rows"],
            "scientifically_admitted": False,
            "genotype_analysis": False,
        },
        "animal": {
            "source_family": "animal_adna",
            "foundation_sample_rows": foundation["summary"]["sample_row_count"],
            "point_features": len(points),
            "distinct_point_sample_ids": len(sample_ids),
            "nordic_point_features": nordic_features,
            "nordic_point_sample_ids": len(nordic_sample_ids),
            "point_scope_counts": dict(sorted(scope.items())),
            "point_chronology_evidence_counts": dict(sorted(chronology.items())),
            "point_source_path_field_status_counts": dict(
                sorted(source_path_posture.items())
            ),
            "point_source_path_issues": path_issues,
            "point_source_artifacts": [
                {
                    "path": name,
                    "bytes": (root / name).stat().st_size,
                    "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest(),
                }
                for name in sorted(source_artifacts)
            ],
            "point_project_paper_pairs": [
                {"project_accession": project, "paper_doi": paper}
                for project, paper in sorted(project_papers)
            ],
            "foundation_validation_overall_ok": validation["overall_ok"],
            "foundation_missing_paper_link_rows": missing_paper["finding_count"],
            "foundation_missing_paper_link_projects": sorted(
                set(missing_paper["findings"])
            ),
        },
        "cross_source_comparison_admitted": False,
        "pollen_evidence_admitted": False,
        "scientific_closure": "pending_qualified_review_and_source_lineage_gaps",
    }


def build(root: Path, output: Path) -> dict[str, Any]:
    values: dict[str, dict[str, Any]] = {}
    inputs = []
    for name in INPUTS:
        values[name], identity = _read(root, name)
        inputs.append(identity)
    report = derive(root, values)
    report["inputs"] = inputs
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.repository.resolve(), args.output.resolve())
    print(
        json.dumps(
            {
                "human_source_rows": result["human"]["source_rows"],
                "animal_point_features": result["animal"]["point_features"],
                "scientific_closure": result["scientific_closure"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
