"""Governed payload assembly for classification-audit publication."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import cast

from .constants import (
    ACCEPTED_STATUSES,
    COUNTRY_PARTITION,
    MAPPING_STATUSES,
    REVIEW_STATUSES,
    ZERO_ACCEPTED_REASON_CODES,
)
from .partitions import country_partitions, observation_country_counts
from .queues import queue_payload, queue_row
from .values import refuse


def build_payloads(
    *,
    accounting: Mapping[str, object],
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
    classification_contract_version: str,
    classification_contract_digest: str,
    classification_producer_id: str,
    classification_producer_version: str,
    classification_producer_digest: str,
) -> tuple[dict[str, dict[str, object]], str]:
    status_concepts = Counter(str(row["mapping_status"]) for row in concepts)
    status_observations = Counter(str(row["mapping_status"]) for row in memberships)
    queue_rows = tuple(queue_row(row) for row in concepts)
    accepted_rows = tuple(
        row for row in queue_rows if row["mapping_status"] in ACCEPTED_STATUSES
    )
    unmapped_rows = tuple(
        row for row in queue_rows if row["mapping_status"] == "unmapped"
    )
    not_applicable_rows = tuple(
        row for row in queue_rows if row["mapping_status"] == "not_applicable"
    )
    review_rows = tuple(
        row
        for row in queue_rows
        if row["mapping_status"] in REVIEW_STATUSES
        or (row["mapping_status"] in ACCEPTED_STATUSES and not row["review_complete"])
    )
    reviewed_accepted_count = sum(bool(row["review_complete"]) for row in accepted_rows)
    release_eligible_count = sum(bool(row["release_eligible"]) for row in accepted_rows)
    source_review = accounting.get("review")
    if not isinstance(source_review, Mapping):
        refuse(
            "invalid_accounting_schema",
            "classification accounting requires review metadata",
        )
    source_review = cast(Mapping[str, object], source_review)
    release_reason_codes: tuple[str, ...]
    if not accepted_rows:
        release_status = "refused"
        release_reason_codes = ZERO_ACCEPTED_REASON_CODES
    elif reviewed_accepted_count != len(accepted_rows):
        release_status = "refused"
        release_reason_codes = ("accepted_mapping_review_incomplete",)
    else:
        release_status = "review_required"
        release_reason_codes = ("independent_scientific_review_required",)
    common = {
        "source_family": accounting["source_family"],
        "source_snapshot_id": accounting["source_snapshot_id"],
        "build_id": accounting["build_id"],
        "classification_contract_version": classification_contract_version,
        "classification_contract_digest": classification_contract_digest,
        "classification_producer_id": classification_producer_id,
        "classification_producer_version": classification_producer_version,
        "classification_producer_digest": classification_producer_digest,
    }
    partitions = country_partitions(memberships)
    return (
        {
            "concept_denominators.json": {
                "schema_version": "classification-concept-denominators.v1",
                **common,
                "record_count": len(concepts),
                "total_concept_count": len(concepts),
                "mapping_status_counts": {
                    status: status_concepts[status] for status in MAPPING_STATUSES
                },
                "accepted_queue_count": len(accepted_rows),
                "unmapped_queue_count": len(unmapped_rows),
                "not_applicable_queue_count": len(not_applicable_rows),
                "review_queue_count": len(review_rows),
            },
            "observation_denominators.json": {
                "schema_version": "classification-observation-denominators.v1",
                **common,
                "record_count": len(memberships),
                "total_observation_count": len(memberships),
                "mapping_status_counts": {
                    status: status_observations[status] for status in MAPPING_STATUSES
                },
                "source_country_counts": observation_country_counts(
                    memberships, "source_country_code"
                ),
                "governed_country_counts": observation_country_counts(
                    memberships, "governed_country_code"
                ),
            },
            "observation_memberships.json": {
                "schema_version": "classification-observation-memberships.v1",
                **common,
                "record_count": len(memberships),
                "records": tuple(dict(row) for row in memberships),
            },
            "country_partitions.json": {
                "schema_version": "classification-country-partitions.v1",
                **common,
                "record_count": len(COUNTRY_PARTITION) * 2
                + len(COUNTRY_PARTITION) ** 2,
                **partitions,
            },
            "accepted_mapping_queue.json": queue_payload(
                "classification-accepted-mapping-queue.v1",
                common,
                accepted_rows,
                queue_semantics="accepted and accepted-qualified source concepts",
            ),
            "unmapped_mapping_queue.json": queue_payload(
                "classification-unmapped-mapping-queue.v1",
                common,
                unmapped_rows,
                queue_semantics="source concepts without an accepted mapping",
            ),
            "not_applicable_mapping_queue.json": queue_payload(
                "classification-not-applicable-mapping-queue.v1",
                common,
                not_applicable_rows,
                queue_semantics="explicit non-biological source concepts",
            ),
            "review_queue.json": {
                **queue_payload(
                    "classification-review-queue.v1",
                    common,
                    review_rows,
                    queue_semantics=(
                        "unmapped, contested, refused, or incompletely reviewed "
                        "accepted source concepts"
                    ),
                ),
                "unresolved_concept_ids": source_review.get(
                    "unresolved_concept_ids", ()
                ),
                "country_release_blockers": source_review.get(
                    "country_release_blockers", ()
                ),
                "integrity_blockers": source_review.get("integrity_blockers", ()),
            },
            "release_metadata.json": {
                "schema_version": "classification-release-metadata.v1",
                **common,
                "status_namespace": "classification_release",
                "release_status": release_status,
                "public_release_allowed": False,
                "release_reason_codes": release_reason_codes,
                "accepted_mapping_count": len(accepted_rows),
                "reviewed_accepted_mapping_count": reviewed_accepted_count,
                "release_eligible_mapping_count": release_eligible_count,
                "unmapped_mapping_count": len(unmapped_rows),
                "not_applicable_mapping_count": len(not_applicable_rows),
                "human_approval_synthesized": False,
                "record_count": 1,
            },
        },
        release_status,
    )
