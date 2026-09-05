"""Deterministic concept and observation denominator partitions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def _build_partitions(
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
) -> dict[str, list[dict[str, object]]]:
    from . import (
        Counter,
        _MAPPING_STATUSES,
        _concept_field_partition_rows,
        _country_partition_rows,
        _country_relation_rows,
    )

    status_concepts = Counter(str(row["mapping_status"]) for row in concepts)
    status_observations = Counter(str(row["mapping_status"]) for row in memberships)
    partitions: dict[str, list[dict[str, object]]] = {
        "mapping_status": [
            {
                "value": status,
                "concept_count": status_concepts[status],
                "observation_count": status_observations[status],
            }
            for status in _MAPPING_STATUSES
        ],
        "source_country": _country_partition_rows(
            concepts, memberships, "source_country"
        ),
        "governed_country": _country_partition_rows(
            concepts, memberships, "governed_country"
        ),
        "country_relation": _country_relation_rows(concepts, memberships),
    }
    for field in (
        "source_element",
        "source_element_type_partition",
        "source_taxon_group",
        "source_ecological_group",
        "source_unit",
        "unit_family",
        "source_evidence_universe",
    ):
        partitions[field] = _concept_field_partition_rows(concepts, memberships, field)
    return partitions


def _concept_field_partition_rows(
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
    field: str,
) -> list[dict[str, object]]:
    from . import Counter, _partition_value

    concept_by_id = {str(row["classification_concept_id"]): row for row in concepts}
    concept_counts = Counter(_partition_value(row.get(field)) for row in concepts)
    observation_counts: Counter[str] = Counter()
    for membership in memberships:
        concept = concept_by_id[str(membership["classification_concept_id"])]
        observation_counts[_partition_value(concept.get(field))] += 1
    values = sorted(set(concept_counts) | set(observation_counts))
    return [
        {
            "value": value,
            "concept_count": concept_counts[value],
            "observation_count": observation_counts[value],
        }
        for value in values
    ]
