"""Country partitions and denominators for classification evidence."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence

from .constants import COUNTRY_PARTITION


def country_partitions(
    memberships: Sequence[Mapping[str, object]],
) -> dict[str, tuple[dict[str, object], ...]]:
    concept_memberships: dict[tuple[str, str], set[str]] = defaultdict(set)
    observation_counts: Counter[tuple[str, str]] = Counter()
    for row in memberships:
        concept_id = str(row["classification_concept_id"])
        for dimension in ("source_country", "governed_country"):
            code = str(row[f"{dimension}_code"])
            concept_memberships[(dimension, code)].add(concept_id)
            observation_counts[(dimension, code)] += 1
    source_rows = tuple(
        {
            "country_code": code,
            "concept_membership_count": len(
                concept_memberships[("source_country", code)]
            ),
            "observation_count": observation_counts[("source_country", code)],
        }
        for code in COUNTRY_PARTITION
    )
    governed_rows = tuple(
        {
            "country_code": code,
            "concept_membership_count": len(
                concept_memberships[("governed_country", code)]
            ),
            "observation_count": observation_counts[("governed_country", code)],
        }
        for code in COUNTRY_PARTITION
    )
    relation_observations = Counter(
        (
            str(row["source_country_code"]),
            str(row["governed_country_code"]),
        )
        for row in memberships
    )
    relation_concepts: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in memberships:
        pair = (
            str(row["source_country_code"]),
            str(row["governed_country_code"]),
        )
        relation_concepts[pair].add(str(row["classification_concept_id"]))
    relation_rows = tuple(
        {
            "source_country_code": source,
            "governed_country_code": governed,
            "concept_membership_count": len(relation_concepts[(source, governed)]),
            "observation_count": relation_observations[(source, governed)],
        }
        for source in COUNTRY_PARTITION
        for governed in COUNTRY_PARTITION
    )
    return {
        "source_country": source_rows,
        "governed_country": governed_rows,
        "country_relation": relation_rows,
    }


def observation_country_counts(
    memberships: Sequence[Mapping[str, object]], field_name: str
) -> dict[str, int]:
    counts = Counter(str(row[field_name]) for row in memberships)
    return {code: counts[code] for code in COUNTRY_PARTITION}
