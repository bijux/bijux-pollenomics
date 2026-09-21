"""Source-bound publication leads for screened Neotoma LRA candidates."""

from __future__ import annotations

from collections import Counter
import hashlib
from typing import Any, cast

from bijux_pollenomics.evidence.sources.neotoma.contract import COUNTRY_CODES

from .models import canonical_bytes
from .reading import json_object


def parse_dataset_publications(dataset_id: int, content: bytes) -> list[dict[str, Any]]:
    """Preserve provider publication fields and nullable primary flags."""
    if (
        isinstance(dataset_id, bool)
        or not isinstance(dataset_id, int)
        or dataset_id <= 0
    ):
        raise ValueError("Invalid source dataset ID")
    response = json_object(content)
    if response.get("status") != "success" or not isinstance(
        response.get("data"), list
    ):
        raise ValueError("Provider publication response is not successful")
    publications: dict[int, dict[str, Any]] = {}
    for item in response["data"]:
        if not isinstance(item, dict) or not isinstance(item.get("publication"), dict):
            raise ValueError("Provider publication row is malformed")
        publication = cast(dict[str, Any], item["publication"])
        publication_id = publication.get("publicationid")
        if (
            isinstance(publication_id, bool)
            or not isinstance(publication_id, int)
            or publication_id <= 0
            or publication_id in publications
        ):
            raise ValueError("Provider publication identity is invalid or duplicate")
        links = publication.get("datasets")
        if not isinstance(links, list):
            raise ValueError("Provider publication dataset links are missing")
        matching = [
            link
            for link in links
            if isinstance(link, dict) and link.get("datasetid") == dataset_id
        ]
        if len(matching) != 1:
            raise ValueError("Provider publication does not uniquely link dataset")
        primary = matching[0].get("primary")
        if primary is not None and not isinstance(primary, bool):
            raise ValueError("Provider primary-publication flag is not typed")
        publications[publication_id] = {
            "publication_id": publication_id,
            "source_primary_flag": primary,
            "source_citation": publication.get("citation"),
            "source_doi": publication.get("doi"),
            "source_year": publication.get("year"),
            "source_publication_type": publication.get("pubtype"),
            "source_authors": publication.get("author"),
            "source_payload_sha256": hashlib.sha256(
                canonical_bytes(publication)
            ).hexdigest(),
        }
    return [publications[key] for key in sorted(publications)]


def build_candidate_publication_report(
    attribution: dict[str, Any], responses: dict[int, bytes]
) -> dict[str, Any]:
    """Reconcile every candidate dataset to a captured provider response.

    Publication links are source attribution leads, not reuse permission,
    qualified taxon review, compatible pollen counts, or LRA admission.
    """
    dataset_rows = attribution.get("dataset_rows")
    if (
        attribution.get("schema_version") != "neotoma-candidate-taxon-attribution.v1"
        or attribution.get("publication_allowed") is not False
        or attribution.get("lra_accepted_samples") != 0
        or not isinstance(dataset_rows, list)
        or len(dataset_rows) != attribution.get("candidate_dataset_count")
    ):
        raise ValueError("Candidate attribution is not a refused source projection")
    expected_ids: set[int] = set()
    for row in dataset_rows:
        if (
            not isinstance(row, dict)
            or row.get("dataset_id")
            != f"neotoma:dataset:{row.get('source_dataset_id')}"
        ):
            raise ValueError("Candidate source dataset identity differs")
        source_id = row["source_dataset_id"]
        if (
            isinstance(source_id, bool)
            or not isinstance(source_id, int)
            or source_id <= 0
        ):
            raise ValueError("Candidate source dataset ID is invalid")
        if source_id in expected_ids:
            raise ValueError("Duplicate candidate source dataset")
        expected_ids.add(source_id)
    if set(responses) != expected_ids:
        raise ValueError("Publication response closure differs from candidate datasets")

    rows = []
    country_counts: dict[str, Counter[str]] = {
        country: Counter() for country in COUNTRY_CODES
    }
    for source in sorted(dataset_rows, key=lambda row: row["source_dataset_id"]):
        dataset_id = cast(int, source["source_dataset_id"])
        publications = parse_dataset_publications(dataset_id, responses[dataset_id])
        primary_count = sum(
            item["source_primary_flag"] is True for item in publications
        )
        status = (
            "no_publication_link"
            if not publications
            else "one_source_primary_publication"
            if primary_count == 1
            else "multiple_source_primary_publications"
            if primary_count > 1
            else "no_source_primary_flag"
        )
        country = str(source["source_country_code"])
        if country not in country_counts:
            raise ValueError("Candidate dataset has an unknown country partition")
        country_counts[country]["datasets"] += 1
        country_counts[country][status] += 1
        rows.append(
            {
                "dataset_id": source["dataset_id"],
                "source_dataset_id": dataset_id,
                "country_code": country,
                "source_constituent_database": source["source_constituent_database"],
                "source_dataset_doi_values": source["source_doi_values"],
                "source_dataset_pi": source["source_dataset_pi"],
                "candidate_sample_count": source["candidate_sample_count"],
                "candidate_pollen_observation_count": source[
                    "candidate_pollen_observation_count"
                ],
                "source_response_sha256": hashlib.sha256(
                    responses[dataset_id]
                ).hexdigest(),
                "publication_link_status": status,
                "source_publications": publications,
                "rights_review_status": "not_evaluated",
            }
        )
    return {
        "schema_version": "neotoma-candidate-publication-attribution.v1",
        "source_snapshot_id": attribution["source_snapshot_id"],
        "candidate_attribution_sha256": hashlib.sha256(
            canonical_bytes(attribution)
        ).hexdigest(),
        "candidate_dataset_count": len(rows),
        "candidate_sample_count": attribution["candidate_sample_count"],
        "candidate_pollen_observation_count": attribution[
            "candidate_pollen_observation_count"
        ],
        "publication_record_count": sum(
            len(row["source_publications"]) for row in rows
        ),
        "publication_link_status_counts": dict(
            sorted(Counter(row["publication_link_status"] for row in rows).items())
        ),
        "country_dataset_denominators": {
            country: {"datasets": counts["datasets"], **dict(sorted(counts.items()))}
            for country, counts in sorted(country_counts.items())
        },
        "rows": rows,
        "rights_review_status": "not_evaluated",
        "lra_accepted_samples": 0,
        "publication_allowed": False,
    }
