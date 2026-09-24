"""Prioritize existing taxon review rows using source-screened Neotoma samples."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from typing import Any, cast

from ..models import canonical_bytes
from ..reading import NeotomaEvidence
from .accounting import source_accounting
from .series import source_element_status

_IDENTITY_FIELDS = (
    "source_family",
    "source_variable_id",
    "source_taxon_id",
    "source_reported_name",
    "source_taxon_group",
    "source_ecological_group",
    "source_element",
    "source_element_type",
    "source_unit",
    "unit_family",
)


def _identity(value: dict[str, Any]) -> str:
    return json.dumps(
        {field: value.get(field) for field in _IDENTITY_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _review_digest(value: object) -> str:
    """Match the existing review bundle digest without importing dev tooling."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def prioritize_neotoma_candidate_taxa(
    evidence: NeotomaEvidence,
    screen: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    """Join necessary pollen counts to the full unresolved review inventory.

    Counts are review workload indicators. They do not establish taxa, PPE,
    compatible pollen sums, chronology selection, or scientific admission.
    """
    evidence.assert_unchanged()
    manifest = evidence.manifest()
    if (
        screen.get("schema_version") != "neotoma-pollen-prerequisite-screen.v1"
        or screen.get("source_snapshot_id") != manifest["source_snapshot_id"]
        or screen.get("normalized_build_id") != manifest["build_id"]
        or screen.get("normalized_manifest_sha256")
        != hashlib.sha256(evidence.manifest_bytes).hexdigest()
        or screen.get("raw_manifest_sha256")
        != dict(evidence.raw_files)["manifest.json"]
        or screen.get("lra_accepted_samples") != 0
        or screen.get("executable_request") is not None
    ):
        raise ValueError("Screen is not bound to this refused Neotoma source")
    expected_digest = review.get("bundle_sha256")
    if (
        not isinstance(expected_digest, str)
        or _review_digest(
            {key: value for key, value in review.items() if key != "bundle_sha256"}
        )
        != expected_digest
    ):
        raise ValueError("Taxa review bundle digest differs")
    if (
        review.get("authority_role") != "review_projection_not_canonical_classification"
        or review.get("scientific_admission_allowed") is not False
        or review.get("source_summaries", {})
        .get("neotoma", {})
        .get("source_snapshot_id")
        != manifest["source_snapshot_id"]
    ):
        raise ValueError("Taxa review does not match refused source scope")
    review_rows = cast(list[dict[str, Any]], review["rows"])
    if review.get("row_count") != len(review_rows):
        raise ValueError("Taxa review row count differs")
    concepts: dict[str, dict[str, Any]] = {}
    concept_ids: set[str] = set()
    for review_row in review_rows:
        if review_row.get("source_family") != "neotoma" or not review_row.get(
            "observation_count"
        ):
            continue
        concept_source = cast(dict[str, Any], review_row["supporting_evidence"])
        if review_row["review_row_id"] != concept_source["classification_concept_id"]:
            raise ValueError("Review identity differs from source concept")
        key = _identity(concept_source)
        concept_id = str(review_row["review_row_id"])
        if key in concepts or concept_id in concept_ids:
            raise ValueError("Duplicate source concept in taxa review")
        concepts[key] = review_row
        concept_ids.add(concept_id)

    candidate_ids = cast(list[str], screen["candidate_sample_ids"])
    if (
        screen.get("candidate_sample_ids_sha256")
        != hashlib.sha256(canonical_bytes(candidate_ids)).hexdigest()
    ):
        raise ValueError("Screen candidate identity digest differs")
    decisions = cast(list[dict[str, Any]], screen["sample_decisions"])
    by_sample = {row["sample_id"]: row for row in decisions}
    if (
        len(candidate_ids) != len(set(candidate_ids))
        or len(decisions) != len(by_sample)
        or len(candidate_ids)
        != screen["screen_denominators"]["necessary_candidate_samples"]
        or any(
            by_sample[sample_id]["screen_status"] != "necessary_candidate"
            for sample_id in candidate_ids
        )
    ):
        raise ValueError("Screen candidate sample identities do not reconcile")
    accounting = source_accounting(evidence, candidate_ids)
    occurrences: Counter[str] = Counter()
    exact_sums: Counter[str] = Counter()
    observed_zeros: Counter[str] = Counter()
    samples: dict[str, set[str]] = defaultdict(set)
    countries: dict[str, Counter[str]] = defaultdict(Counter)
    country_exact_sums: dict[str, Counter[str]] = defaultdict(Counter)
    screened_samples: Counter[str] = Counter()
    for source in evidence.rows("observations"):
        observation = source.payload()
        sample_id = observation["sample_id"]
        if sample_id not in accounting.selected_samples:
            continue
        record = accounting.observation(source)
        if (
            record["count_status"] != "count_candidate"
            or source_element_status(
                observation.get("source_element"),
                observation.get("source_element_type"),
            )
            != "source_label_pollen"
        ):
            continue
        identity = {
            "source_family": "neotoma",
            "source_variable_id": observation["variable_id"],
            **{field: observation.get(field) for field in _IDENTITY_FIELDS[2:]},
        }
        matched_concept = concepts.get(_identity(identity))
        if matched_concept is None:
            raise ValueError("Screened source pollen has no full-review concept")
        concept_id = str(matched_concept["review_row_id"])
        country = str(observation["country_code"])
        if country != by_sample[sample_id]["country_code"]:
            raise ValueError("Candidate observation country differs from sample")
        count = record.get("typed_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("Candidate pollen has no exact nonnegative count")
        occurrences[concept_id] += 1
        exact_sums[concept_id] += count
        if count == 0:
            observed_zeros[concept_id] += 1
        samples[concept_id].add(sample_id)
        countries[concept_id][country] += 1
        country_exact_sums[concept_id][country] += count
        screened_samples[sample_id] += 1
    if any(
        screened_samples[sample_id] != by_sample[sample_id]["pollen_count_observations"]
        for sample_id in candidate_ids
    ) or sum(occurrences.values()) != sum(
        by_sample[sample_id]["pollen_count_observations"] for sample_id in candidate_ids
    ):
        raise ValueError("Candidate pollen observations differ from source screen")
    concepts_by_id = {
        str(concept_row["review_row_id"]): concept_row
        for concept_row in concepts.values()
    }
    rows = [
        {
            "review_row_id": concept_id,
            "source_identity_sha256": concepts_by_id[concept_id][
                "source_identity_sha256"
            ],
            "source_reported_name": concepts_by_id[concept_id]["source_reported_name"],
            "source_unit": concepts_by_id[concept_id]["supporting_evidence"][
                "source_unit"
            ],
            "review_state": concepts_by_id[concept_id]["review_state"],
            "candidate_observation_count": count,
            "candidate_exact_count_sum": exact_sums[concept_id],
            "candidate_observed_zero_count": observed_zeros[concept_id],
            "candidate_sample_count": len(samples[concept_id]),
            "candidate_country_observation_counts": dict(
                sorted(countries[concept_id].items())
            ),
            "candidate_country_exact_count_sums": dict(
                sorted(country_exact_sums[concept_id].items())
            ),
        }
        for concept_id, count in sorted(
            occurrences.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    evidence.assert_unchanged()
    return {
        "schema_version": "neotoma-candidate-taxon-review-priority.v2",
        "source_snapshot_id": manifest["source_snapshot_id"],
        "raw_manifest_sha256": dict(evidence.raw_files)["manifest.json"],
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "screen_candidate_ids_sha256": screen["candidate_sample_ids_sha256"],
        "review_bundle_sha256": expected_digest,
        "full_review_row_count": review["row_count"],
        "candidate_sample_count": len(candidate_ids),
        "candidate_pollen_observation_count": sum(occurrences.values()),
        "candidate_review_row_count": len(rows),
        "selected_review_state_counts": dict(
            sorted(Counter(row["review_state"] for row in rows).items())
        ),
        "rows": rows,
        "lra_accepted_samples": 0,
        "publication_allowed": False,
    }
