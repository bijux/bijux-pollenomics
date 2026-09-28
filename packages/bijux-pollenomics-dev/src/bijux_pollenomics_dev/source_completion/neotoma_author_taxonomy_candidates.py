"""Join Neotoma review concepts to literal LandClim author taxonomy names."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from .landclim_taxonomy_mass import EXCLUDED_TARGETS, LOOKUP, _lookup

PRIORITY = Path("docs/report/source-relations/neotoma/taxon-priority/priority.json")
CONCEPTS = Path("data/neotoma/review/source_taxon_concepts.json")


def _identity(path: Path, repository: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(repository).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def derive(
    priority: dict[str, Any], concepts: dict[str, Any], lookup: dict[str, str]
) -> dict[str, object]:
    """Retain all screened source concepts without promoting name equality."""
    if (
        priority.get("candidate_review_row_count") != 1006
        or priority.get("lra_accepted_samples") != 0
        or concepts.get("row_count") != 1351
        or concepts.get("scientific_admission_allowed") is not False
        or priority.get("review_bundle_sha256") != concepts.get("bundle_sha256")
    ):
        raise ValueError("Neotoma source review or priority scope changed")
    concept_by_id = {row["review_row_id"]: row for row in concepts["rows"]}
    if len(concept_by_id) != 1351:
        raise ValueError("Duplicate Neotoma review concept")

    rows: list[dict[str, object]] = []
    concept_counts: Counter[str] = Counter()
    observation_counts: Counter[str] = Counter()
    count_sums: Counter[tuple[str, str]] = Counter()
    seen: set[str] = set()
    for source in priority["rows"]:
        identity = source["review_row_id"]
        concept = concept_by_id.get(identity)
        if identity in seen or concept is None:
            raise ValueError("Missing or repeated priority concept")
        seen.add(identity)
        if (
            source["review_state"] != "needs_discussion"
            or concept["review_state"] != "needs_discussion"
            or concept["current_mapping_status"] != "unmapped"
            or source["source_identity_sha256"] != concept["source_identity_sha256"]
            or source["source_reported_name"] != concept["source_reported_name"]
            or concept["source_domain"] != "source_pollen"
        ):
            raise ValueError("Priority concept changed or acquired a review decision")
        name = source["source_reported_name"]
        target = lookup.get(name)
        status = (
            "unmatched"
            if target is None
            else "author_excluded"
            if target in EXCLUDED_TARGETS
            else "author_target"
        )
        unit = source["source_unit"]
        observations = source["candidate_observation_count"]
        exact_count = source["candidate_exact_count_sum"]
        if (
            unit not in {"NISP", "NISP digitized"}
            or observations <= 0
            or exact_count < 0
            or sum(source["candidate_country_observation_counts"].values())
            != observations
            or sum(source["candidate_country_exact_count_sums"].values()) != exact_count
        ):
            raise ValueError("Neotoma source unit or country accounting changed")
        concept_counts[status] += 1
        observation_counts[status] += observations
        count_sums[(status, unit)] += exact_count
        rows.append(
            {
                "review_row_id": identity,
                "source_identity_sha256": source["source_identity_sha256"],
                "source_native_id": concept["source_native_id"],
                "source_reported_name": name,
                "source_unit": unit,
                "source_groups": concept["source_groups"],
                "qualifier_markers": concept["qualifier_markers"],
                "candidate_observation_count": observations,
                "candidate_exact_count_sum": exact_count,
                "candidate_country_observation_counts": source[
                    "candidate_country_observation_counts"
                ],
                "candidate_country_exact_count_sums": source[
                    "candidate_country_exact_count_sums"
                ],
                "literal_name_status": status,
                "author_lookup_target": target,
                "review_state": "needs_discussion",
                "scientific_admission_allowed": False,
            }
        )
    if (
        len(rows) != 1006
        or sum(observation_counts.values())
        != priority["candidate_pollen_observation_count"]
    ):
        raise ValueError("Neotoma priority denominator does not close")
    return {
        "schema_version": "neotoma-author-taxonomy-candidates.v1",
        "source_snapshot_id": priority["source_snapshot_id"],
        "review_bundle_sha256": concepts["bundle_sha256"],
        "priority_concept_count": len(rows),
        "concept_counts_by_literal_status": dict(sorted(concept_counts.items())),
        "observation_counts_by_literal_status": dict(
            sorted(observation_counts.items())
        ),
        "exact_count_sums_by_literal_status_and_unit": [
            {
                "literal_name_status": status,
                "source_unit": unit,
                "exact_count_sum": total,
            }
            for (status, unit), total in sorted(count_sums.items())
        ],
        "lra_accepted_samples": 0,
        "scientific_admission_allowed": False,
        "interpretation": (
            "Literal author lookup leads for qualified concept review only. "
            "Source NISP and NISP digitized are separate units. Name equality "
            "does not approve taxon identity, ecological role, PPE, fall speed, "
            "pollen denominator, publication rights or LRA admission."
        ),
        "rows": rows,
    }


def publish(
    repository: Path, author_source_root: Path, output: Path
) -> dict[str, object]:
    """Retain the exact source-backed review candidates and consumed identities."""
    repository = repository.resolve()
    lookup_path = author_source_root.resolve() / LOOKUP
    lookup, _ = _lookup(lookup_path)
    priority_path = repository / PRIORITY
    concept_path = repository / CONCEPTS
    report = derive(
        json.loads(priority_path.read_text(encoding="utf-8")),
        json.loads(concept_path.read_text(encoding="utf-8")),
        lookup,
    )
    report["inputs"] = [
        _identity(priority_path, repository),
        _identity(concept_path, repository),
        {
            "source_root_role": "external_landclim_author_reference",
            "path": LOOKUP.as_posix(),
            "bytes": lookup_path.stat().st_size,
            "sha256": hashlib.sha256(lookup_path.read_bytes()).hexdigest(),
        },
    ]
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--author-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = publish(args.repository, args.author_source_root, args.output)
    print(report["concept_counts_by_literal_status"])


if __name__ == "__main__":
    main()
