"""Attribute the Neotoma datasets used in Nordic direct-pollen development."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra.materialization.neotoma.publication_intake import (
    parse_dataset_publications,
)

ENTITY = Path(
    "docs/report/regions/nordic/source-capability/neotoma-entities/report.json"
)
DATASETS = Path("data/neotoma/relational/surfaces/datasets/part-00001.json")
POLICY_REVIEW = Path("docs/public/pollenomics-data/sources/neotoma.md")
POLICY_CAPTURE_SHA256 = (
    "ba75c8f22491f5b5e83a835f964aedea53b62e526cf6ea36bb10b376e774b3a4"
)


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def build(repository: Path, capture_root: Path) -> dict[str, Any]:
    """Join only used datasets to exact captured provider publication responses."""
    repository, capture_root = repository.resolve(), capture_root.resolve()
    policy_review_bytes = (repository / POLICY_REVIEW).read_bytes()
    if POLICY_CAPTURE_SHA256.encode() not in policy_review_bytes:
        raise ValueError("The governed Neotoma policy review changed")
    entity_bytes = (repository / ENTITY).read_bytes()
    entity = json.loads(entity_bytes)
    dataset_bytes = (repository / DATASETS).read_bytes()
    if (
        entity.get("schema_version") != "neotoma-nordic-entity-decisions.v1"
        or entity.get("direct_pollen_included_datasets") != 85
        or entity["inputs"][DATASETS.as_posix()] != _sha(dataset_bytes)
    ):
        raise ValueError("Nordic dataset decisions differ from their source part")
    datasets = {row["dataset_id"]: row for row in json.loads(dataset_bytes)["rows"]}
    if len(datasets) != 209:
        raise ValueError("Neotoma dataset identity denominator changed")
    used = [
        row
        for row in entity["decisions"]
        if row["direct_pollen_study_disposition"] == "included"
    ]
    if len(used) != 85 or len({row["dataset_id"] for row in used}) != 85:
        raise ValueError("The used direct-pollen dataset set changed")

    capture_bytes = (capture_root / "capture-manifest.json").read_bytes()
    capture = json.loads(capture_bytes)
    capture_rows = capture.get("responses")
    if (
        capture.get("schema_version") != "neotoma-candidate-publication-capture.v1"
        or not isinstance(capture_rows, list)
        or capture.get("response_count") != len(capture_rows)
    ):
        raise ValueError("Provider publication capture manifest changed")
    by_source_id = {row["dataset_id"]: row for row in capture_rows}
    if len(by_source_id) != len(capture_rows):
        raise ValueError("Duplicate captured publication response identity")

    decisions = []
    for selected in sorted(used, key=lambda row: row["dataset_id"]):
        identity = selected["dataset_id"]
        source = datasets.get(identity)
        if (
            source is None
            or _sha(json.dumps(source, sort_keys=True, separators=(",", ":")).encode())
            != selected["source_dataset_row_sha256"]
        ):
            raise ValueError(f"Source dataset row changed: {identity}")
        source_id = source["source_dataset_id"]
        capture_row = by_source_id.get(source_id)
        relative = f"responses/dataset-{source_id}-publications.json"
        if (
            capture_row is None
            or capture_row.get("path") != relative
            or capture_row.get("http_status") != 200
        ):
            raise ValueError(f"Missing captured provider response: {identity}")
        response_path = capture_root / relative
        if response_path.is_symlink():
            raise ValueError(f"Symbolic provider response: {identity}")
        response = response_path.read_bytes()
        if (
            len(response) != capture_row["bytes"]
            or _sha(response) != capture_row["sha256"]
        ):
            raise ValueError(f"Captured provider bytes changed: {identity}")
        links = parse_dataset_publications(source_id, response)
        primary_count = sum(link["source_primary_flag"] is True for link in links)
        status = (
            "no_publication_link"
            if not links
            else "one_source_primary_publication"
            if primary_count == 1
            else "multiple_source_primary_publications"
            if primary_count > 1
            else "no_source_primary_flag"
        )
        payload = source["source_payload"]
        dataset_dois = payload["doi"]
        investigators = [row["contactname"] for row in payload["datasetpi"]]
        if (
            payload["database"] != "European Pollen Database"
            or not dataset_dois
            or not investigators
            or any(
                not isinstance(value, str) or not value or not value.isascii()
                for value in dataset_dois
            )
            or any(not isinstance(value, str) or not value for value in investigators)
        ):
            raise ValueError(f"Used dataset attribution fields changed: {identity}")
        doi_status = (
            "one_source_doi"
            if len(dataset_dois) == 1
            else "ascii_case_equivalent_source_dois"
            if len({value.lower() for value in dataset_dois}) == 1
            else "distinct_source_dois"
        )
        if status == "one_source_primary_publication":
            primary = next(
                link for link in links if link["source_primary_flag"] is True
            )
            if not all(
                primary.get(field)
                for field in ("source_citation", "source_year", "source_authors")
            ):
                raise ValueError(f"Provider primary citation incomplete: {identity}")
        decisions.append(
            {
                "dataset_id": identity,
                "site_id": selected["site_id"],
                "country_code": selected["country_code"],
                "dataset_dois": dataset_dois,
                "dataset_doi_status": doi_status,
                "dataset_investigators": investigators,
                "constituent_database": payload["database"],
                "source_dataset_notes": payload["datasetnotes"],
                "provider_publication_status": status,
                "provider_publications": links,
                "provider_response_sha256": _sha(response),
                "direct_pollen_role": "used_in_selected_study",
                "lra_admission": "unresolved_source_requirements",
            }
        )
    counts = Counter(row["provider_publication_status"] for row in decisions)
    doi_counts = Counter(row["dataset_doi_status"] for row in decisions)
    country = {
        code: {
            "used_datasets": sum(row["country_code"] == code for row in decisions),
            "one_source_primary_publication": sum(
                row["country_code"] == code
                and row["provider_publication_status"]
                == "one_source_primary_publication"
                for row in decisions
            ),
            "primary_link_review_required": sum(
                row["country_code"] == code
                and row["provider_publication_status"]
                != "one_source_primary_publication"
                for row in decisions
            ),
            "distinct_source_dois": sum(
                row["country_code"] == code
                and row["dataset_doi_status"] == "distinct_source_dois"
                for row in decisions
            ),
            "either_citation_review": sum(
                row["country_code"] == code
                and (
                    row["provider_publication_status"]
                    != "one_source_primary_publication"
                    or row["dataset_doi_status"] == "distinct_source_dois"
                )
                for row in decisions
            ),
        }
        for code in ("SE", "DK", "NO", "FI")
    }
    if {code: row["used_datasets"] for code, row in country.items()} != {
        "SE": 3,
        "DK": 2,
        "NO": 52,
        "FI": 28,
    }:
        raise ValueError("The selected country dataset denominator changed")
    return {
        "schema_version": "nordic-neotoma-publication-readiness.v1",
        "entity_ledger_sha256": _sha(entity_bytes),
        "dataset_part_sha256": _sha(dataset_bytes),
        "provider_capture_manifest_sha256": _sha(capture_bytes),
        "provider_policy": {
            "url": "https://www.neotomadb.org/data/data-use-and-embargo-policy",
            "captured_policy_sha256": POLICY_CAPTURE_SHA256,
            "governed_review_sha256": _sha(policy_review_bytes),
            "version": "2025",
            "posture": "CC BY 4.0 with three-level attribution; source-specific review remains separate",
        },
        "used_dataset_count": len(decisions),
        "provider_publication_status_counts": dict(sorted(counts.items())),
        "dataset_doi_status_counts": dict(sorted(doi_counts.items())),
        "doi_equivalence_rule": {
            "url": "https://www.doi.org/doi-handbook/html/",
            "section": "3.3.4 Case Insensitivity of the DOI Name",
            "application": "ASCII case equivalence only; preserve source DOI strings",
        },
        "country_denominators": country,
        "provider_primary_gap_dataset_ids": [
            row["dataset_id"]
            for row in decisions
            if row["provider_publication_status"] != "one_source_primary_publication"
        ],
        "distinct_doi_dataset_ids": [
            row["dataset_id"]
            for row in decisions
            if row["dataset_doi_status"] == "distinct_source_dois"
        ],
        "citation_review_dataset_ids": [
            row["dataset_id"]
            for row in decisions
            if row["provider_publication_status"] != "one_source_primary_publication"
            or row["dataset_doi_status"] == "distinct_source_dois"
        ],
        "decisions": decisions,
        "publication_ready": False,
        "lra_accepted_samples": 0,
    }


def main() -> None:
    """Run the CLI to attribute the Neotoma datasets used in Nordic direct-pollen development."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.repository, args.capture_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
