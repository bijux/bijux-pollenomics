"""Country identity, partitions, relations, and release blockers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def _source_country_code(site: Mapping[str, object] | None) -> str:
    from . import Mapping as RuntimeMapping
    from . import Sequence as RuntimeSequence
    from . import _COUNTRY_CODES

    if site is None:
        return "UNASSIGNED"
    geopolitical = site.get("source_geopolitical")
    if not isinstance(geopolitical, RuntimeSequence) or isinstance(
        geopolitical, (str, bytes)
    ):
        return "UNASSIGNED"
    first = geopolitical[0] if geopolitical else None
    if isinstance(first, RuntimeMapping):
        first = first.get("country")
    return _COUNTRY_CODES.get(str(first), "UNASSIGNED")


def _governed_country_code(value: object) -> str:
    from . import _COUNTRY_CODES, _COUNTRY_PARTITION

    text = "" if value is None else str(value).strip()
    if text in _COUNTRY_PARTITION:
        return text
    return _COUNTRY_CODES.get(text, "UNASSIGNED")


def _country_partition_rows(
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
    dimension: str,
) -> list[dict[str, object]]:
    from . import Counter, Sequence as RuntimeSequence
    from . import _COUNTRY_PARTITION, defaultdict

    membership_field = f"{dimension}_code"
    concept_field = f"{dimension}_codes"
    observation_counts = Counter(str(row[membership_field]) for row in memberships)
    concept_memberships: dict[str, set[str]] = defaultdict(set)
    for concept in concepts:
        concept_id = str(concept["classification_concept_id"])
        country_codes = concept.get(concept_field, [])
        if isinstance(country_codes, RuntimeSequence) and not isinstance(
            country_codes, (str, bytes)
        ):
            for country_code in country_codes:
                concept_memberships[str(country_code)].add(concept_id)
    return [
        {
            "country_code": country_code,
            "concept_membership_count": len(concept_memberships[country_code]),
            "observation_count": observation_counts[country_code],
        }
        for country_code in _COUNTRY_PARTITION
    ]


def _country_relation_rows(
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    from . import Counter, _COUNTRY_PARTITION, defaultdict

    observation_counts = Counter(
        (str(row["source_country_code"]), str(row["governed_country_code"]))
        for row in memberships
    )
    concept_memberships: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in memberships:
        pair = (str(row["source_country_code"]), str(row["governed_country_code"]))
        concept_memberships[pair].add(str(row["classification_concept_id"]))
    return [
        {
            "source_country_code": source_country,
            "governed_country_code": governed_country,
            "concept_membership_count": len(
                concept_memberships[(source_country, governed_country)]
            ),
            "observation_count": observation_counts[(source_country, governed_country)],
        }
        for source_country in _COUNTRY_PARTITION
        for governed_country in _COUNTRY_PARTITION
    ]


def _country_release_blockers(
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    from . import _RELEASE_REASON_CODES, _country_partition_rows

    rows: list[dict[str, object]] = []
    for dimension in ("source_country", "governed_country"):
        country_rows = _country_partition_rows(concepts, memberships, dimension)
        for country_row in country_rows:
            country_code = str(country_row["country_code"])
            unresolved_ids = {
                str(row["classification_concept_id"])
                for row in memberships
                if row[f"{dimension}_code"] == country_code
                and row["mapping_status"] == "unmapped"
            }
            unresolved_observations = sum(
                row[f"{dimension}_code"] == country_code
                and row["mapping_status"] == "unmapped"
                for row in memberships
            )
            rows.append(
                {
                    "country_dimension": dimension,
                    "country_code": country_code,
                    "release_status": "refused",
                    "reason_codes": list(_RELEASE_REASON_CODES),
                    "unresolved_concept_membership_count": len(unresolved_ids),
                    "unresolved_observation_count": unresolved_observations,
                }
            )
    return rows


def _country_sort_key(value: str) -> tuple[int, str]:
    from . import _COUNTRY_PARTITION

    try:
        return _COUNTRY_PARTITION.index(value), value
    except ValueError:
        return len(_COUNTRY_PARTITION), value
