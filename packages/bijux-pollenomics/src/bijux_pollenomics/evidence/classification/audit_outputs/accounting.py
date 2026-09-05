"""Scientific input validation and reconciliation for classification audits."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import cast

from .constants import ACCEPTED_STATUSES, COUNTRY_PARTITION, MAPPING_STATUSES
from .manifest import canonical_json_bytes
from .partitions import country_partitions
from .values import mapping_sequence, refuse, required_text


def validated_accounting_rows(
    accounting: Mapping[str, object],
) -> tuple[tuple[Mapping[str, object], ...], tuple[Mapping[str, object], ...]]:
    if accounting.get("schema_version") != "neotoma-classification-accounting.v1":
        refuse(
            "unsupported_accounting_schema",
            "classification audit requires neotoma-classification-accounting.v1",
        )
    if accounting.get("source_family") != "neotoma":
        refuse(
            "unsupported_source_family",
            "classification audit requires source-native Neotoma accounting",
        )
    required_text(accounting.get("source_snapshot_id"), field_name="source_snapshot_id")
    required_text(accounting.get("build_id"), field_name="build_id")
    concepts = mapping_sequence(accounting.get("concepts"), field_name="concepts")
    memberships = mapping_sequence(
        accounting.get("observation_memberships"),
        field_name="observation_memberships",
    )
    concept_ids: set[str] = set()
    concept_statuses: dict[str, str] = {}
    for concept in concepts:
        concept_id = required_text(
            concept.get("classification_concept_id"),
            field_name="classification_concept_id",
        )
        if concept_id in concept_ids:
            refuse("duplicate_concept_id", f"duplicate concept: {concept_id}")
        concept_ids.add(concept_id)
        status = str(concept.get("mapping_status", ""))
        if status not in MAPPING_STATUSES:
            refuse("invalid_mapping_status", f"unsupported status: {status}")
        concept_statuses[concept_id] = status
        observation_count = concept.get("observation_count")
        if (
            isinstance(observation_count, bool)
            or not isinstance(observation_count, int)
            or observation_count < 0
        ):
            refuse(
                "invalid_accounting_reconciliation",
                f"concept {concept_id} has invalid observation_count",
            )
    observation_ids: set[str] = set()
    for membership in memberships:
        observation_id = required_text(
            membership.get("observation_id"), field_name="observation_id"
        )
        concept_id = required_text(
            membership.get("classification_concept_id"),
            field_name="classification_concept_id",
        )
        if observation_id in observation_ids:
            refuse(
                "duplicate_observation_membership",
                f"duplicate observation membership: {observation_id}",
            )
        observation_ids.add(observation_id)
        if concept_id not in concept_ids:
            refuse(
                "orphan_concept_membership",
                f"observation references unknown concept: {concept_id}",
            )
        status = str(membership.get("mapping_status", ""))
        if status not in MAPPING_STATUSES:
            refuse("invalid_mapping_status", f"unsupported status: {status}")
        if status != concept_statuses[concept_id]:
            refuse(
                "invalid_accounting_reconciliation",
                f"membership status conflicts with concept: {observation_id}",
            )
        for field_name in ("source_country_code", "governed_country_code"):
            country_code = str(membership.get(field_name, ""))
            if country_code not in COUNTRY_PARTITION:
                refuse(
                    "invalid_country_partition",
                    f"{field_name} is outside the governed partition: {country_code}",
                )
    return (
        tuple(sorted(concepts, key=lambda row: str(row["classification_concept_id"]))),
        tuple(sorted(memberships, key=lambda row: str(row["observation_id"]))),
    )


def validate_accounting_reconciliation(
    accounting: Mapping[str, object],
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
) -> None:
    reconciliation = accounting.get("reconciliation")
    if not isinstance(reconciliation, Mapping):
        refuse(
            "invalid_accounting_reconciliation",
            "accounting requires a reconciliation object",
        )
    reconciliation = cast(Mapping[str, object], reconciliation)
    expected_counts = {
        "unique_observation_count": len(memberships),
        "observation_membership_count": len(memberships),
        "concept_count": len(concepts),
        "concept_observation_count_sum": len(memberships),
        "mapping_status_concept_count_sum": len(concepts),
        "mapping_status_observation_count_sum": len(memberships),
        "accepted_concept_count": sum(
            str(row["mapping_status"]) in ACCEPTED_STATUSES for row in concepts
        ),
        "release_eligible_concept_count": sum(
            bool(row.get("release_eligible", False)) for row in concepts
        ),
    }
    for field_name, expected_count in expected_counts.items():
        if reconciliation.get(field_name) != expected_count:
            refuse(
                "invalid_accounting_reconciliation",
                f"{field_name} does not reconcile to {expected_count}",
            )
    membership_counts = Counter(
        str(row["classification_concept_id"]) for row in memberships
    )
    for concept in concepts:
        concept_id = str(concept["classification_concept_id"])
        if concept.get("observation_count") != membership_counts[concept_id]:
            refuse(
                "invalid_accounting_reconciliation",
                f"concept observation count does not reconcile: {concept_id}",
            )
    expected_country_partitions = country_partitions(memberships)
    partitions = accounting.get("partitions")
    if not isinstance(partitions, Mapping):
        refuse(
            "invalid_accounting_reconciliation",
            "accounting requires partition tables",
        )
    partitions = cast(Mapping[str, object], partitions)
    concept_status_counts = Counter(str(row["mapping_status"]) for row in concepts)
    observation_status_counts = Counter(
        str(row["mapping_status"]) for row in memberships
    )
    expected_status_partition = tuple(
        {
            "value": status,
            "concept_count": concept_status_counts[status],
            "observation_count": observation_status_counts[status],
        }
        for status in MAPPING_STATUSES
    )
    if canonical_json_bytes(partitions.get("mapping_status")) != canonical_json_bytes(
        expected_status_partition
    ):
        refuse(
            "invalid_accounting_reconciliation",
            "source accounting mapping-status partition does not reconcile",
        )
    for key, expected_partition in expected_country_partitions.items():
        if canonical_json_bytes(partitions.get(key)) != canonical_json_bytes(
            expected_partition
        ):
            refuse(
                "invalid_accounting_reconciliation",
                f"source accounting partition does not reconcile: {key}",
            )
