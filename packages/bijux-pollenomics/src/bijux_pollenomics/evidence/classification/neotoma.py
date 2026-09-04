from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import copy
import hashlib
import json
import re

__all__ = ["build_neotoma_classification_accounting"]

_COUNTRY_CODES = {
    "Denmark": "DK",
    "Finland": "FI",
    "Norway": "NO",
    "Sweden": "SE",
}
_COUNTRY_PARTITION = ("SE", "DK", "NO", "FI", "UNASSIGNED")
_MAPPING_STATUSES = (
    "accepted",
    "accepted_qualified",
    "unmapped",
    "contested",
    "not_applicable",
    "refused",
)
_LABORATORY_ECOLOGICAL_GROUPS = frozenset({"LABO"})
_LABORATORY_TAXON_GROUPS = frozenset({"Laboratory", "Laboratory analyses"})
_ADMINISTRATIVE_ECOLOGICAL_GROUPS = frozenset({"ADMN"})
_ADMINISTRATIVE_TAXON_GROUPS = frozenset({"Administrative", "Administrative variables"})
_QUALIFIER_PATTERNS = (
    ("cf", re.compile(r"(?:^|\s)cf\.\s", re.IGNORECASE)),
    ("type", re.compile(r"(?:-|\.|\s)type(?:\b|\))", re.IGNORECASE)),
    ("undifferentiated", re.compile(r"\bundiff\.?\b", re.IGNORECASE)),
    ("combined_taxa", re.compile(r"/")),
    ("group", re.compile(r"\bgroup\b", re.IGNORECASE)),
    ("sensu_lato", re.compile(r"\bsensu\s+lato\b", re.IGNORECASE)),
    ("subgenus", re.compile(r"\bsubg\.\s", re.IGNORECASE)),
)
_RELEASE_REASON_CODES = (
    "accepted_mapping_not_available",
    "mapping_evidence_not_available",
    "human_review_not_available",
)


def build_neotoma_classification_accounting(
    relational_snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Build a lossless, non-interpretive classification accounting surface."""
    if relational_snapshot.get("source_family") != "neotoma":
        raise ValueError("classification accounting requires a Neotoma snapshot")

    observations = _mapping_rows(relational_snapshot.get("observations"))
    variables = _index_rows(
        _mapping_rows(relational_snapshot.get("variables")), "variable_id"
    )
    sites = _index_rows(_mapping_rows(relational_snapshot.get("sites")), "site_id")
    unique_observations, duplicate_blockers = _deduplicate_observations(observations)

    concept_accumulators: dict[str, dict[str, object]] = {}
    observation_memberships: list[dict[str, object]] = []
    integrity_blockers: list[dict[str, object]] = list(duplicate_blockers)
    for observation in unique_observations:
        observation_id = _required_text(observation, "observation_id")
        variable_id = _required_text(observation, "variable_id")
        site_id = _required_text(observation, "site_id")
        variable = variables.get(variable_id)
        site = sites.get(site_id)
        if variable is None:
            integrity_blockers.append(
                _blocker("orphan_variable_reference", observation_id, variable_id)
            )
        elif not _variable_identity_matches(variable, observation):
            integrity_blockers.append(
                _blocker("variable_identity_conflict", observation_id, variable_id)
            )
        if site is None:
            integrity_blockers.append(
                _blocker("orphan_site_reference", observation_id, site_id)
            )

        source_country = _source_country_code(site)
        governed_country = _governed_country_code(observation.get("country_code"))
        identity = _source_concept_identity(observation)
        concept_id = _concept_id(identity)
        mapping_status, mapping_reason = _mapping_posture(identity)
        accumulator = concept_accumulators.get(concept_id)
        if accumulator is None:
            accumulator = {
                "classification_concept_id": concept_id,
                **copy.deepcopy(identity),
                "source_element_type_partition": _partition_value(
                    identity["source_element_type"]
                ),
                "source_label_qualifier_markers": _qualifier_markers(
                    identity["source_reported_name"]
                ),
                "mapping_status": mapping_status,
                "mapping_reason_code": mapping_reason,
                "source_evidence_universe": _source_evidence_universe(
                    identity, mapping_status
                ),
                "aggregation_posture": "exact_source_unit_only",
                "cross_unit_aggregation_allowed": False,
                "accepted_taxon_concept_id": None,
                "accepted_taxon_name": None,
                "primary_group_id": None,
                "primary_subgroup_id": None,
                "role_ids": [],
                "evidence_reference_ids": [],
                "reviewer_id": None,
                "decision_date": None,
                "crosswalk_version": None,
                "release_eligible": False,
                "release_blocker_reason_codes": list(_RELEASE_REASON_CODES)
                if mapping_status == "unmapped"
                else [],
                "source_country_codes": set(),
                "governed_country_codes": set(),
                "observation_ids": set(),
            }
            concept_accumulators[concept_id] = accumulator
        _set_member(accumulator, "source_country_codes", source_country)
        _set_member(accumulator, "governed_country_codes", governed_country)
        _set_member(accumulator, "observation_ids", observation_id)
        observation_memberships.append(
            {
                "observation_id": observation_id,
                "classification_concept_id": concept_id,
                "mapping_status": mapping_status,
                "source_country_code": source_country,
                "governed_country_code": governed_country,
            }
        )

    concepts = [_finalize_concept(row) for row in concept_accumulators.values()]
    concepts.sort(key=lambda row: str(row["classification_concept_id"]))
    observation_memberships.sort(key=lambda row: str(row["observation_id"]))
    integrity_blockers.sort(
        key=lambda row: (
            str(row["reason_code"]),
            str(row["subject_id"]),
            str(row.get("detail", "")),
        )
    )
    partitions = _build_partitions(concepts, observation_memberships)
    unresolved_concept_ids = [
        str(row["classification_concept_id"])
        for row in concepts
        if row["mapping_status"] == "unmapped"
    ]
    country_release_blockers = _country_release_blockers(
        concepts, observation_memberships
    )
    observation_count = len(observation_memberships)
    return {
        "schema_version": "neotoma-classification-accounting.v1",
        "source_family": "neotoma",
        "source_snapshot_id": copy.deepcopy(
            relational_snapshot.get("source_snapshot_id")
        ),
        "build_id": copy.deepcopy(relational_snapshot.get("build_id")),
        "classification_posture": "source_accounting_only",
        "release_status": "refused",
        "release_reason_codes": list(_RELEASE_REASON_CODES),
        "concepts": concepts,
        "observation_memberships": observation_memberships,
        "partitions": partitions,
        "review": {
            "unresolved_concept_ids": unresolved_concept_ids,
            "country_release_blockers": country_release_blockers,
            "integrity_blockers": integrity_blockers,
        },
        "reconciliation": {
            "input_observation_row_count": len(observations),
            "unique_observation_count": observation_count,
            "duplicate_observation_row_count": len(observations) - observation_count,
            "observation_membership_count": observation_count,
            "concept_count": len(concepts),
            "concept_observation_count_sum": sum(
                _integer_count(row, "observation_count") for row in concepts
            ),
            "mapping_status_concept_count_sum": sum(
                _integer_count(row, "concept_count")
                for row in partitions["mapping_status"]
            ),
            "mapping_status_observation_count_sum": sum(
                _integer_count(row, "observation_count")
                for row in partitions["mapping_status"]
            ),
            "accepted_concept_count": 0,
            "release_eligible_concept_count": 0,
            "integrity_blocker_count": len(integrity_blockers),
        },
    }


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _index_rows(
    rows: Sequence[Mapping[str, object]], id_field: str
) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for row in rows:
        value = row.get(id_field)
        if value is None:
            continue
        row_id = str(value)
        existing = indexed.get(row_id)
        if existing is not None and _canonical_json(existing) != _canonical_json(row):
            raise ValueError(f"conflicting duplicate {id_field}: {row_id}")
        indexed[row_id] = row
    return indexed


def _deduplicate_observations(
    rows: Sequence[Mapping[str, object]],
) -> tuple[list[Mapping[str, object]], list[dict[str, object]]]:
    unique: dict[str, Mapping[str, object]] = {}
    duplicate_counts: Counter[str] = Counter()
    for row in rows:
        observation_id = _required_text(row, "observation_id")
        existing = unique.get(observation_id)
        if existing is None:
            unique[observation_id] = row
            continue
        if _canonical_json(existing) != _canonical_json(row):
            raise ValueError(f"conflicting duplicate observation_id: {observation_id}")
        duplicate_counts[observation_id] += 1
    blockers: list[dict[str, object]] = [
        {
            "reason_code": "duplicate_observation_id",
            "subject_id": observation_id,
            "detail": str(count),
        }
        for observation_id, count in sorted(duplicate_counts.items())
    ]
    return list(unique.values()), blockers


def _integer_count(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    return value


def _required_text(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    text = "" if value is None else str(value).strip()
    if not text:
        raise ValueError(f"observation requires {field}")
    return text


def _source_concept_identity(
    observation: Mapping[str, object],
) -> dict[str, object]:
    return {
        "source_family": "neotoma",
        "source_variable_id": _required_text(observation, "variable_id"),
        "source_taxon_id": copy.deepcopy(observation.get("source_taxon_id")),
        "source_reported_name": copy.deepcopy(observation.get("source_reported_name")),
        "source_taxon_group": copy.deepcopy(observation.get("source_taxon_group")),
        "source_ecological_group": copy.deepcopy(
            observation.get("source_ecological_group")
        ),
        "source_element": copy.deepcopy(observation.get("source_element")),
        "source_element_type": copy.deepcopy(observation.get("source_element_type")),
        "source_unit": copy.deepcopy(observation.get("source_unit")),
        "unit_family": copy.deepcopy(observation.get("unit_family")),
    }


def _concept_id(identity: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json(identity).encode()).hexdigest()[:24]
    return f"neotoma:classification-concept:{digest}"


def _mapping_posture(identity: Mapping[str, object]) -> tuple[str, str]:
    ecological_group = identity.get("source_ecological_group")
    taxon_group = identity.get("source_taxon_group")
    if (
        ecological_group in _LABORATORY_ECOLOGICAL_GROUPS
        or taxon_group in _LABORATORY_TAXON_GROUPS
    ):
        return "not_applicable", "source_declares_laboratory_analysis"
    if (
        ecological_group in _ADMINISTRATIVE_ECOLOGICAL_GROUPS
        or taxon_group in _ADMINISTRATIVE_TAXON_GROUPS
    ):
        return "not_applicable", "source_declares_administrative_variable"
    return "unmapped", "mapping_evidence_and_human_review_required"


def _source_evidence_universe(
    identity: Mapping[str, object], mapping_status: str
) -> str:
    if mapping_status == "not_applicable":
        return "explicit_non_biological"
    if identity.get("source_element_type") == "pollen":
        return "source_pollen"
    return "other_or_unresolved_source_element"


def _variable_identity_matches(
    variable: Mapping[str, object], observation: Mapping[str, object]
) -> bool:
    return variable.get("source_taxon_id") == observation.get(
        "source_taxon_id"
    ) and variable.get("source_reported_name") == observation.get(
        "source_reported_name"
    )


def _source_country_code(site: Mapping[str, object] | None) -> str:
    if site is None:
        return "UNASSIGNED"
    geopolitical = site.get("source_geopolitical")
    if not isinstance(geopolitical, Sequence) or isinstance(geopolitical, (str, bytes)):
        return "UNASSIGNED"
    first = geopolitical[0] if geopolitical else None
    if isinstance(first, Mapping):
        first = first.get("country")
    return _COUNTRY_CODES.get(str(first), "UNASSIGNED")


def _governed_country_code(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if text in _COUNTRY_PARTITION:
        return text
    return _COUNTRY_CODES.get(text, "UNASSIGNED")


def _qualifier_markers(value: object) -> list[str]:
    label = "" if value is None else str(value)
    return [name for name, pattern in _QUALIFIER_PATTERNS if pattern.search(label)]


def _partition_value(value: object) -> str:
    if value is None or value == "":
        return "not_provided_by_source"
    return str(value)


def _set_member(row: dict[str, object], field: str, value: str) -> None:
    values = row[field]
    if not isinstance(values, set):
        raise TypeError(f"{field} accumulator must be a set")
    values.add(value)


def _finalize_concept(row: dict[str, object]) -> dict[str, object]:
    result = copy.deepcopy(row)
    observation_ids = result.pop("observation_ids")
    if not isinstance(observation_ids, set):
        raise TypeError("observation_ids accumulator must be a set")
    result["observation_count"] = len(observation_ids)
    for field in ("source_country_codes", "governed_country_codes"):
        values = result[field]
        if not isinstance(values, set):
            raise TypeError(f"{field} accumulator must be a set")
        result[field] = sorted(values, key=_country_sort_key)
    return result


def _build_partitions(
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
) -> dict[str, list[dict[str, object]]]:
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


def _country_partition_rows(
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
    dimension: str,
) -> list[dict[str, object]]:
    membership_field = f"{dimension}_code"
    concept_field = f"{dimension}_codes"
    observation_counts = Counter(str(row[membership_field]) for row in memberships)
    concept_memberships: dict[str, set[str]] = defaultdict(set)
    for concept in concepts:
        concept_id = str(concept["classification_concept_id"])
        country_codes = concept.get(concept_field, [])
        if isinstance(country_codes, Sequence) and not isinstance(
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


def _concept_field_partition_rows(
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
    field: str,
) -> list[dict[str, object]]:
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


def _country_release_blockers(
    concepts: Sequence[Mapping[str, object]],
    memberships: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
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


def _blocker(reason_code: str, subject_id: str, detail: str) -> dict[str, object]:
    return {
        "reason_code": reason_code,
        "subject_id": subject_id,
        "detail": detail,
    }


def _country_sort_key(value: str) -> tuple[int, str]:
    try:
        return _COUNTRY_PARTITION.index(value), value
    except ValueError:
        return len(_COUNTRY_PARTITION), value


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
