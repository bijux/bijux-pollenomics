"""Retain literal Neotoma pollen-name leads for published LandClim parameters."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

PARAMETERS = Path("data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv")
PRIORITY = Path("docs/report/source-relations/neotoma/taxon-priority/priority.json")


def _identity(path: Path, repository: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(repository).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def derive(
    parameters: list[dict[str, str]], priority: dict[str, Any]
) -> dict[str, object]:
    """Join exact labels while retaining every source concept and count unit."""
    if len(parameters) != 31 or priority.get("candidate_review_row_count") != 1006:
        raise ValueError("Published parameter or current pollen priority scope changed")
    if priority.get("lra_accepted_samples") != 0:
        raise ValueError("Pollen priority admission status changed")
    concepts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    for concept in priority["rows"]:
        identity = concept["review_row_id"]
        if identity in seen_ids or concept["review_state"] != "needs_discussion":
            raise ValueError("Pollen concept identity or review state changed")
        seen_ids.add(identity)
        concepts[concept["source_reported_name"]].append(concept)
    if len(seen_ids) != 1006:
        raise ValueError("Pollen concept inventory is incomplete")
    rows: list[dict[str, Any]] = []
    parameter_names: set[str] = set()
    for parameter in parameters:
        name = parameter["Plant taxa/Pollen-morphological types"]
        if not name or name in parameter_names:
            raise ValueError("Published parameter name is blank or duplicated")
        parameter_names.add(name)
        matched = sorted(concepts.get(name, []), key=lambda item: item["review_row_id"])
        rows.append(
            {
                "parameter_source_name": name,
                "parameter_pft_code": parameter["PFT"],
                "parameter_fsp_source_text": parameter["FSP (m/s)"],
                "parameter_ppe_source_text": parameter["PPE (SD)"],
                "literal_name_match_status": (
                    "exact_unreviewed_candidate" if matched else "no_exact_source_name"
                ),
                "source_concepts": [
                    {
                        "review_row_id": concept["review_row_id"],
                        "source_identity_sha256": concept["source_identity_sha256"],
                        "source_unit": concept["source_unit"],
                        "candidate_observation_count": concept[
                            "candidate_observation_count"
                        ],
                        "candidate_exact_count_sum": concept[
                            "candidate_exact_count_sum"
                        ],
                        "review_state": concept["review_state"],
                    }
                    for concept in matched
                ],
            }
        )
    return {
        "schema_version": "neotoma-landclim-parameter-candidates.v1",
        "source_snapshot_id": priority["source_snapshot_id"],
        "source_concept_review_bundle_sha256": priority["review_bundle_sha256"],
        "parameter_row_count": len(rows),
        "exact_name_parameter_count": sum(bool(row["source_concepts"]) for row in rows),
        "unmatched_parameter_count": sum(
            row["literal_name_match_status"] == "no_exact_source_name" for row in rows
        ),
        "exact_name_concept_count": sum(len(row["source_concepts"]) for row in rows),
        "lra_accepted_samples": 0,
        "scientific_admission_allowed": False,
        "interpretation": (
            "Literal source-name correspondence only. Distinct source concepts and "
            "NISP units remain separate. Name equality does not establish taxon "
            "identity, count denominator, PPE/FSP applicability or LRA admission."
        ),
        "rows": rows,
    }


def publish(repository: Path, output: Path) -> dict[str, object]:
    """Write a reproducible candidate ledger with the exact consumed file IDs."""
    parameter_path = repository / PARAMETERS
    priority_path = repository / PRIORITY
    with parameter_path.open(encoding="utf-8-sig", newline="") as handle:
        parameters = list(csv.DictReader(handle))
    priority = json.loads(priority_path.read_text(encoding="utf-8"))
    report = derive(parameters, priority)
    report["inputs"] = [
        _identity(parameter_path, repository),
        _identity(priority_path, repository),
    ]
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = publish(args.repository.resolve(), args.output)
    print(
        f"{report['exact_name_parameter_count']}/{report['parameter_row_count']} "
        "parameter names have unreviewed exact source leads"
    )


if __name__ == "__main__":
    main()
