"""Source-native concept identity and conservative mapping posture."""

from __future__ import annotations

from collections.abc import Mapping


def _source_concept_identity(
    observation: Mapping[str, object],
) -> dict[str, object]:
    from . import _required_text, copy

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
    from . import _canonical_json, hashlib

    digest = hashlib.sha256(_canonical_json(identity).encode()).hexdigest()[:24]
    return f"neotoma:classification-concept:{digest}"


def _mapping_posture(identity: Mapping[str, object]) -> tuple[str, str]:
    from . import (
        _ADMINISTRATIVE_ECOLOGICAL_GROUPS,
        _ADMINISTRATIVE_TAXON_GROUPS,
        _LABORATORY_ECOLOGICAL_GROUPS,
        _LABORATORY_TAXON_GROUPS,
    )

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


def _qualifier_markers(value: object) -> list[str]:
    from . import _QUALIFIER_PATTERNS

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
    from . import _country_sort_key, copy

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


def _blocker(reason_code: str, subject_id: str, detail: str) -> dict[str, object]:
    return {
        "reason_code": reason_code,
        "subject_id": subject_id,
        "detail": detail,
    }
