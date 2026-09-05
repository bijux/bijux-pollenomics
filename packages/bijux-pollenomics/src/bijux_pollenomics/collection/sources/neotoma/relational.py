from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
import copy
from dataclasses import dataclass, replace
import hashlib
import json
import math
from typing import TypeAlias

from ....core.text import clean_optional_text
from ...spatial import CountryAttributionDecision

__all__ = ["build_neotoma_relational_snapshot"]

_COUNTRY_CODES = {
    "Denmark": "DK",
    "Finland": "FI",
    "Norway": "NO",
    "Sweden": "SE",
}
_TABLE_NAMES = (
    "sites",
    "collection_units",
    "datasets",
    "chronologies",
    "chronology_controls",
    "samples",
    "age_claims",
    "variables",
    "observations",
)
_TABLE_ID_FIELDS = {
    "sites": "site_id",
    "collection_units": "collection_unit_id",
    "datasets": "dataset_id",
    "chronologies": "chronology_id",
    "chronology_controls": "chronology_control_id",
    "samples": "sample_id",
    "age_claims": "chronology_claim_id",
    "variables": "variable_id",
    "observations": "observation_id",
}
_COUNTRY_COUNT_FIELDS = (
    "site_rows",
    "sites",
    "collection_unit_rows",
    "collection_units",
    "dataset_rows",
    "datasets",
    "chronologies",
    "chronology_controls",
    "sample_rows",
    "samples",
    "age_claim_rows",
    "age_comparable",
    "age_context_only",
    "age_refused",
    "age_unresolved",
    "observation_rows",
    "variables",
    "assigned_sites",
    "review_sites",
    "unassigned_sites",
    "refused_sites",
    "propagation_eligible_sites",
)

CountryAttributionInput: TypeAlias = CountryAttributionDecision | str


@dataclass(frozen=True)
class _NeotomaCountryAttribution:
    raw_country: str | None
    derived_country: str | None
    final_country_code: str
    decision_status: str
    decision_method: str
    candidate_countries: tuple[str, ...]
    ambiguity_reason: str | None
    refusal_reason: str | None
    boundary_artifact_digest: str | None
    boundary_version: str | None
    source_vs_derived_comparison: str
    propagation_eligible: bool


def build_neotoma_relational_snapshot(
    download_rows: Iterable[Mapping[str, object]],
    *,
    source_snapshot_id: str,
    build_id: str,
    country_by_site_id: Mapping[object, CountryAttributionInput] | None = None,
) -> dict[str, object]:
    """Preserve joined detail with governed country decisions on every site.

    String country values remain accepted only as review-blocked legacy evidence.
    """
    if not source_snapshot_id.strip():
        raise ValueError("source_snapshot_id must not be empty")
    if not build_id.strip():
        raise ValueError("build_id must not be empty")

    country_attribution = {
        str(site_id): _country_attribution(value)
        for site_id, value in (country_by_site_id or {}).items()
    }
    tables: dict[str, dict[str, dict[str, object]]] = {
        table_name: {} for table_name in _TABLE_NAMES
    }
    conflicts: list[dict[str, object]] = []
    orphans: list[dict[str, object]] = []
    source_counts: Counter[str] = Counter()
    age_postures: Counter[str] = Counter()
    age_reasons: Counter[str] = Counter()
    unit_counts: Counter[str] = Counter()
    country_counts: dict[str, Counter[str]] = {
        code: Counter() for code in ("SE", "DK", "NO", "FI", "UNASSIGNED")
    }

    for download_row in download_rows:
        source_counts["download_rows"] += 1
        site = download_row.get("site")
        if not isinstance(site, Mapping):
            _add_orphan(orphans, "download_row", None, "missing_site")
            continue
        site_source_id = _required_source_id(
            site.get("siteid"), "site", orphans, parent_id=None
        )
        if site_source_id is None:
            continue
        site_id = f"neotoma:site:{site_source_id}"
        attribution = country_attribution.get(site_source_id)
        if attribution is None:
            attribution = _missing_country_attribution(site)
        else:
            attribution = _with_source_country(attribution, site)
        country_code = attribution.final_country_code
        source_counts["site_rows"] += 1
        country_counts[country_code]["site_rows"] += 1
        _register(
            tables["sites"],
            {
                "site_id": site_id,
                "source_site_id": site.get("siteid"),
                "raw_country": attribution.raw_country,
                "derived_country": attribution.derived_country,
                "country_code": country_code,
                "country_decision_status": attribution.decision_status,
                "country_decision_method": attribution.decision_method,
                "country_candidates": list(attribution.candidate_countries),
                "country_ambiguity_reason": attribution.ambiguity_reason,
                "country_refusal_reason": attribution.refusal_reason,
                "boundary_artifact_digest": attribution.boundary_artifact_digest,
                "boundary_version": attribution.boundary_version,
                "source_vs_derived_comparison": (
                    attribution.source_vs_derived_comparison
                ),
                "country_propagation_eligible": attribution.propagation_eligible,
                "source_geopolitical": copy.deepcopy(site.get("geopolitical")),
                "source_payload": _without(site, "collectionunit", "dataset"),
                "source_snapshot_id": source_snapshot_id,
                "build_id": build_id,
            },
            id_field="site_id",
            conflicts=conflicts,
            conflict_kind="site_payload_conflict",
        )

        unit = site.get("collectionunit")
        if not isinstance(unit, Mapping):
            _add_orphan(orphans, "site", site_id, "missing_collection_unit")
            continue
        unit_source_id = _required_source_id(
            unit.get("collectionunitid"),
            "collection_unit",
            orphans,
            parent_id=site_id,
        )
        if unit_source_id is None:
            continue
        unit_id = f"neotoma:collection-unit:{unit_source_id}"
        source_counts["collection_unit_rows"] += 1
        country_counts[country_code]["collection_unit_rows"] += 1
        _register(
            tables["collection_units"],
            {
                "collection_unit_id": unit_id,
                "source_collection_unit_id": unit.get("collectionunitid"),
                "site_id": site_id,
                "country_code": country_code,
                "source_payload": _without(
                    unit, "dataset", "chronologies", "defaultchronology"
                ),
                "source_snapshot_id": source_snapshot_id,
                "build_id": build_id,
            },
            id_field="collection_unit_id",
            conflicts=conflicts,
            conflict_kind="collection_unit_payload_conflict",
        )

        dataset = unit.get("dataset")
        if not isinstance(dataset, Mapping):
            _add_orphan(orphans, "collection_unit", unit_id, "missing_dataset")
            continue
        dataset_source_id = _required_source_id(
            dataset.get("datasetid"), "dataset", orphans, parent_id=unit_id
        )
        if dataset_source_id is None:
            continue
        dataset_id = f"neotoma:dataset:{dataset_source_id}"
        source_counts["dataset_rows"] += 1
        country_counts[country_code]["dataset_rows"] += 1
        site_dataset = site.get("dataset")
        _register(
            tables["datasets"],
            {
                "dataset_id": dataset_id,
                "source_dataset_id": dataset.get("datasetid"),
                "site_id": site_id,
                "collection_unit_id": unit_id,
                "country_code": country_code,
                "source_payload": _without(dataset, "samples"),
                "source_site_dataset_payload": copy.deepcopy(site_dataset)
                if isinstance(site_dataset, Mapping)
                else None,
                "source_snapshot_id": source_snapshot_id,
                "build_id": build_id,
            },
            id_field="dataset_id",
            conflicts=conflicts,
            conflict_kind="dataset_payload_conflict",
        )

        default_source_id = _optional_source_id(unit.get("defaultchronology"))
        chronology_ids_by_source: dict[str, str] = {}
        flagged_default_ids: list[str] = []
        chronologies = unit.get("chronologies")
        if not isinstance(chronologies, list):
            chronologies = []
        source_counts["chronology_rows"] += len(chronologies)
        for wrapper in chronologies:
            if not isinstance(wrapper, Mapping):
                _add_orphan(
                    orphans, "collection_unit", unit_id, "invalid_chronology_row"
                )
                continue
            chronology = wrapper.get("chronology")
            if not isinstance(chronology, Mapping):
                _add_orphan(
                    orphans, "collection_unit", unit_id, "missing_chronology_payload"
                )
                continue
            chronology_source_id = _optional_source_id(chronology.get("chronologyid"))
            if chronology_source_id is None:
                _add_orphan(
                    orphans,
                    "chronology",
                    unit_id,
                    "missing_source_identifier",
                    source_value=chronology.get("chronologyid"),
                )
                chronology_key = f"unidentified:{_digest(dict(chronology))[:20]}"
            else:
                chronology_key = chronology_source_id
            chronology_id = f"neotoma:chronology:{unit_source_id}:{chronology_key}"
            if chronology_source_id is not None:
                chronology_ids_by_source[chronology_source_id] = chronology_id
            chronology_metadata = chronology.get("chronology")
            if not isinstance(chronology_metadata, Mapping):
                chronology_metadata = {}
            source_is_default = chronology_metadata.get("isdefault") is True
            if source_is_default and chronology_source_id is not None:
                flagged_default_ids.append(chronology_source_id)
            _register(
                tables["chronologies"],
                {
                    "chronology_id": chronology_id,
                    "source_chronology_id": chronology.get("chronologyid"),
                    "collection_unit_id": unit_id,
                    "site_id": site_id,
                    "country_code": country_code,
                    "selected_by_collection_unit_reference": (
                        chronology_source_id == default_source_id
                    ),
                    "source_is_default_assertion": source_is_default,
                    "source_payload": _without(chronology, "chroncontrols"),
                    "source_snapshot_id": source_snapshot_id,
                    "build_id": build_id,
                },
                id_field="chronology_id",
                conflicts=conflicts,
                conflict_kind="chronology_payload_conflict",
            )
            controls = chronology.get("chroncontrols")
            if not isinstance(controls, list):
                controls = []
            source_counts["chronology_control_rows"] += len(controls)
            for control in controls:
                if not isinstance(control, Mapping):
                    _add_orphan(
                        orphans,
                        "chronology",
                        chronology_id,
                        "invalid_chronology_control_row",
                    )
                    continue
                control_source_id = _optional_source_id(control.get("chroncontrolid"))
                if control_source_id is None:
                    _add_orphan(
                        orphans,
                        "chronology_control",
                        chronology_id,
                        "missing_source_identifier",
                        source_value=control.get("chroncontrolid"),
                    )
                    control_key = f"unidentified:{_digest(dict(control))[:20]}"
                else:
                    control_key = control_source_id
                control_id = f"{chronology_id}:control:{control_key}"
                _register(
                    tables["chronology_controls"],
                    {
                        "chronology_control_id": control_id,
                        "source_chronology_control_id": control.get("chroncontrolid"),
                        "chronology_id": chronology_id,
                        "collection_unit_id": unit_id,
                        "site_id": site_id,
                        "country_code": country_code,
                        "source_payload": copy.deepcopy(dict(control)),
                        "source_snapshot_id": source_snapshot_id,
                        "build_id": build_id,
                    },
                    id_field="chronology_control_id",
                    conflicts=conflicts,
                    conflict_kind="chronology_control_payload_conflict",
                )

        expected_flags = [default_source_id] if default_source_id is not None else []
        if sorted(flagged_default_ids) != expected_flags:
            conflicts.append(
                _conflict_record(
                    "default_chronology_assertions_conflict",
                    dataset_id,
                    {
                        "collection_unit_id": unit_id,
                        "explicit_default_chronology_id": (
                            f"neotoma:chronology:{unit_source_id}:{default_source_id}"
                            if default_source_id is not None
                            else None
                        ),
                        "source_flagged_default_chronology_ids": [
                            f"neotoma:chronology:{unit_source_id}:{source_id}"
                            for source_id in sorted(flagged_default_ids)
                        ],
                        "governing_selection": "collection_unit.defaultchronology",
                    },
                )
            )
        if (
            default_source_id is not None
            and default_source_id not in chronology_ids_by_source
        ):
            _add_orphan(
                orphans,
                "collection_unit",
                unit_id,
                "default_chronology_not_found",
                source_value=unit.get("defaultchronology"),
            )

        samples = dataset.get("samples")
        if not isinstance(samples, list):
            samples = []
        source_counts["sample_rows"] += len(samples)
        country_counts[country_code]["sample_rows"] += len(samples)
        for sample in samples:
            if not isinstance(sample, Mapping):
                _add_orphan(orphans, "dataset", dataset_id, "invalid_sample_row")
                continue
            sample_source_id = _required_source_id(
                sample.get("sampleid"), "sample", orphans, parent_id=dataset_id
            )
            if sample_source_id is None:
                continue
            sample_id = f"neotoma:sample:{sample_source_id}"
            _register(
                tables["samples"],
                {
                    "sample_id": sample_id,
                    "source_sample_id": sample.get("sampleid"),
                    "source_analysis_unit_id": copy.deepcopy(
                        sample.get("analysisunitid")
                    ),
                    "dataset_id": dataset_id,
                    "collection_unit_id": unit_id,
                    "site_id": site_id,
                    "country_code": country_code,
                    "source_payload": _without(sample, "ages", "datum"),
                    "source_snapshot_id": source_snapshot_id,
                    "build_id": build_id,
                },
                id_field="sample_id",
                conflicts=conflicts,
                conflict_kind="sample_payload_conflict",
            )
            ages = sample.get("ages")
            if not isinstance(ages, list):
                ages = []
            source_counts["age_claim_rows"] += len(ages)
            country_counts[country_code]["age_claim_rows"] += len(ages)
            age_occurrence_counts: Counter[str] = Counter()
            for age in ages:
                if not isinstance(age, Mapping):
                    _add_orphan(orphans, "sample", sample_id, "invalid_age_row")
                    continue
                age_digest = _digest(dict(age))
                age_occurrence_counts[age_digest] += 1
                age_record = _build_age_claim(
                    age,
                    occurrence=age_occurrence_counts[age_digest],
                    sample_id=sample_id,
                    dataset_id=dataset_id,
                    collection_unit_id=unit_id,
                    site_id=site_id,
                    country_code=country_code,
                    default_source_id=default_source_id,
                    chronology_ids_by_source=chronology_ids_by_source,
                    source_snapshot_id=source_snapshot_id,
                    build_id=build_id,
                    orphans=orphans,
                )
                age_postures[str(age_record["comparability_status"])] += 1
                country_counts[country_code][
                    f"age_{age_record['comparability_status']}"
                ] += 1
                admission_reason = age_record.get("admission_reason")
                if admission_reason is not None:
                    age_reasons[str(admission_reason)] += 1
                _register(
                    tables["age_claims"],
                    age_record,
                    id_field="chronology_claim_id",
                    conflicts=conflicts,
                    conflict_kind="age_claim_identity_conflict",
                )

            datum_rows = sample.get("datum")
            if not isinstance(datum_rows, list):
                datum_rows = []
            source_counts["observation_rows"] += len(datum_rows)
            country_counts[country_code]["observation_rows"] += len(datum_rows)
            occurrence_counts: Counter[str] = Counter()
            for datum in datum_rows:
                if not isinstance(datum, Mapping):
                    _add_orphan(orphans, "sample", sample_id, "invalid_observation_row")
                    continue
                datum_payload = copy.deepcopy(dict(datum))
                datum_digest = _digest(datum_payload)
                occurrence_counts[datum_digest] += 1
                observation_id = (
                    f"neotoma:observation:{sample_source_id}:"
                    f"{datum_digest[:20]}:{occurrence_counts[datum_digest]}"
                )
                variable_id = _variable_id(datum)
                _register_variable(
                    tables["variables"],
                    variable_id=variable_id,
                    datum=datum,
                    source_snapshot_id=source_snapshot_id,
                    build_id=build_id,
                    conflicts=conflicts,
                )
                source_unit = clean_optional_text(datum.get("units"))
                unit_counts[source_unit or "<missing>"] += 1
                _register(
                    tables["observations"],
                    {
                        "observation_id": observation_id,
                        "sample_id": sample_id,
                        "dataset_id": dataset_id,
                        "collection_unit_id": unit_id,
                        "site_id": site_id,
                        "country_code": country_code,
                        "variable_id": variable_id,
                        "source_taxon_id": copy.deepcopy(datum.get("taxonid")),
                        "source_reported_name": copy.deepcopy(
                            datum.get("variablename")
                        ),
                        "source_element": copy.deepcopy(datum.get("element")),
                        "source_element_type": copy.deepcopy(datum.get("elementtype")),
                        "source_ecological_group": copy.deepcopy(
                            datum.get("ecologicalgroup")
                        ),
                        "source_taxon_group": copy.deepcopy(datum.get("taxongroup")),
                        "source_unit": copy.deepcopy(datum.get("units")),
                        "unit_family": _unit_family(source_unit),
                        "aggregation_key": f"neotoma:exact-unit:{source_unit}"
                        if source_unit
                        else None,
                        "source_value": copy.deepcopy(datum.get("value")),
                        "detection_status": "reported_value",
                        "source_denominator": None,
                        "denominator_status": "not_provided_by_source",
                        "source_context": copy.deepcopy(datum.get("context")),
                        "source_payload": datum_payload,
                        "source_snapshot_id": source_snapshot_id,
                        "build_id": build_id,
                    },
                    id_field="observation_id",
                    conflicts=conflicts,
                    conflict_kind="observation_identity_conflict",
                )

    normalized_tables = {
        name: sorted(
            records.values(),
            key=lambda item: str(item[_TABLE_ID_FIELDS[name]]),
        )
        for name, records in tables.items()
    }
    _finalize_variables(normalized_tables["variables"])
    normalized_counts = {name: len(rows) for name, rows in normalized_tables.items()}
    for country_code, counts in country_counts.items():
        counts["sites"] = sum(
            1
            for site in normalized_tables["sites"]
            if site.get("country_code") == country_code
        )
        counts["collection_units"] = sum(
            1
            for unit in normalized_tables["collection_units"]
            if _parent_country(unit, normalized_tables["sites"]) == country_code
        )
        counts["datasets"] = sum(
            1
            for dataset_record in normalized_tables["datasets"]
            if _parent_country(dataset_record, normalized_tables["sites"])
            == country_code
        )
        counts["samples"] = sum(
            1
            for sample_record in normalized_tables["samples"]
            if sample_record.get("country_code") == country_code
        )
        counts["chronologies"] = sum(
            1
            for chronology_record in normalized_tables["chronologies"]
            if chronology_record.get("country_code") == country_code
        )
        counts["chronology_controls"] = sum(
            1
            for control_record in normalized_tables["chronology_controls"]
            if control_record.get("country_code") == country_code
        )
        counts["variables"] = len(
            {
                observation["variable_id"]
                for observation in normalized_tables["observations"]
                if observation.get("country_code") == country_code
            }
        )
        for status in ("assigned", "review", "unassigned", "refused"):
            counts[f"{status}_sites"] = sum(
                1
                for site in normalized_tables["sites"]
                if site.get("country_code") == country_code
                and site.get("country_decision_status") == status
            )
        counts["propagation_eligible_sites"] = sum(
            1
            for site in normalized_tables["sites"]
            if site.get("country_code") == country_code
            and site.get("country_propagation_eligible") is True
        )
        for field in _COUNTRY_COUNT_FIELDS:
            counts[field] += 0

    unit_family_counts = Counter(
        str(observation["unit_family"])
        for observation in normalized_tables["observations"]
    )
    variable_semantic_variant_count = 0
    for variable in normalized_tables["variables"]:
        source_semantics = variable.get("source_semantics")
        if isinstance(source_semantics, list):
            variable_semantic_variant_count += len(source_semantics)

    conflicts.sort(key=lambda item: str(item["conflict_id"]))
    orphans.sort(key=lambda item: str(item["orphan_id"]))
    return {
        "schema_version": "neotoma-relational-snapshot.v2",
        "source_family": "neotoma",
        "source_snapshot_id": source_snapshot_id,
        "build_id": build_id,
        **normalized_tables,
        "reconciliation": {
            "source_row_counts": dict(sorted(source_counts.items())),
            "normalized_row_counts": normalized_counts,
            "age_comparability_counts": dict(sorted(age_postures.items())),
            "age_reason_counts": dict(sorted(age_reasons.items())),
            "source_unit_counts": dict(sorted(unit_counts.items())),
            "unit_family_counts": dict(sorted(unit_family_counts.items())),
            "variable_semantic_variant_count": variable_semantic_variant_count,
            "country_counts": {
                code: dict(sorted(counts.items()))
                for code, counts in country_counts.items()
            },
            "country_attribution_counts": _country_attribution_counts(
                normalized_tables["sites"]
            ),
            "conflict_count": len(conflicts),
            "orphan_count": len(orphans),
        },
        "conflicts": conflicts,
        "orphans": orphans,
    }


def _build_age_claim(
    age: Mapping[str, object],
    *,
    occurrence: int,
    sample_id: str,
    dataset_id: str,
    collection_unit_id: str,
    site_id: str,
    country_code: str,
    default_source_id: str | None,
    chronology_ids_by_source: Mapping[str, str],
    source_snapshot_id: str,
    build_id: str,
    orphans: list[dict[str, object]],
) -> dict[str, object]:
    chronology_source_id = _optional_source_id(age.get("chronologyid"))
    chronology_id = (
        chronology_ids_by_source.get(chronology_source_id)
        if chronology_source_id is not None
        else None
    )
    if (
        chronology_source_id is not None
        and chronology_source_id not in chronology_ids_by_source
    ):
        _add_orphan(
            orphans,
            "age_claim",
            sample_id,
            "chronology_not_found",
            source_value=age.get("chronologyid"),
        )
    temporal = _age_temporal_posture(age)
    claim_digest = _digest(
        {
            "sample_id": sample_id,
            "dataset_id": dataset_id,
            "source_payload": dict(age),
        }
    )
    return {
        "chronology_claim_id": (f"neotoma:age-claim:{claim_digest[:24]}:{occurrence}"),
        "source_family": "neotoma",
        "source_record_id": sample_id,
        "subject_type": "sample",
        "subject_id": sample_id,
        "site_id": site_id,
        "collection_unit_id": collection_unit_id,
        "dataset_id": dataset_id,
        "country_code": country_code,
        "chronology_id": chronology_id,
        "chronology_name": copy.deepcopy(age.get("chronologyname")),
        "is_default_chronology": chronology_source_id == default_source_id
        if chronology_source_id is not None
        else False,
        "source_age_type": copy.deepcopy(age.get("agetype")),
        "source_age_value": copy.deepcopy(age.get("age")),
        "source_age_younger": copy.deepcopy(age.get("ageyounger")),
        "source_age_older": copy.deepcopy(age.get("ageolder")),
        "source_age_unit": "year"
        if "year" in clean_optional_text(age.get("agetype")).casefold()
        else None,
        "calibration_status": temporal["calibration_status"],
        "comparability_status": temporal["comparability_status"],
        "younger_bp": temporal["younger_bp"],
        "older_bp": temporal["older_bp"],
        "admission_reason": temporal["reason_code"],
        "refusal_reason": temporal["reason_code"]
        if temporal["comparability_status"] == "refused"
        else None,
        "source_payload": copy.deepcopy(dict(age)),
        "source_relation_path": (
            f"{dataset_id}/{sample_id}/ages/{claim_digest[:24]}:{occurrence}"
        ),
        "provenance_record_id": source_snapshot_id,
        "source_snapshot_id": source_snapshot_id,
        "build_id": build_id,
    }


def _age_temporal_posture(age: Mapping[str, object]) -> dict[str, object]:
    age_type = clean_optional_text(age.get("agetype"))
    if not age_type:
        return _temporal_result(
            "unresolved", "unresolved", None, None, "missing_age_type"
        )
    if age_type == "Radiocarbon years BP":
        return _temporal_result(
            "uncalibrated", "context_only", None, None, "uncalibrated_radiocarbon"
        )
    if age_type == "Varve years BP":
        return _temporal_result(
            "not_calibrated", "context_only", None, None, "ungoverned_varve_basis"
        )
    if age_type not in {
        "Calibrated radiocarbon years BP",
        "Calendar years BP",
    }:
        return _temporal_result(
            "unresolved", "unresolved", None, None, "unknown_age_type"
        )

    calibration_status = (
        "calibrated"
        if age_type == "Calibrated radiocarbon years BP"
        else "not_applicable"
    )
    younger = _finite_number(age.get("ageyounger"))
    older = _finite_number(age.get("ageolder"))
    if (younger is None) != (older is None):
        return _temporal_result(
            calibration_status, "refused", None, None, "partial_interval"
        )
    if younger is None and older is None:
        point = _finite_number(age.get("age"))
        if point is None:
            return _temporal_result(
                calibration_status, "refused", None, None, "missing_numeric_age"
            )
        younger = older = point
    if younger is None or older is None:
        return _temporal_result(
            calibration_status, "refused", None, None, "partial_interval"
        )
    if younger < 0 or older < 0:
        return _temporal_result(
            calibration_status, "refused", None, None, "negative_bp"
        )
    if younger > older:
        return _temporal_result(
            calibration_status, "refused", None, None, "reversed_interval"
        )
    return _temporal_result(calibration_status, "comparable", younger, older, None)


def _temporal_result(
    calibration_status: str,
    comparability_status: str,
    younger_bp: int | float | None,
    older_bp: int | float | None,
    reason_code: str | None,
) -> dict[str, object]:
    return {
        "calibration_status": calibration_status,
        "comparability_status": comparability_status,
        "younger_bp": younger_bp,
        "older_bp": older_bp,
        "reason_code": reason_code,
    }


def _register_variable(
    variables: dict[str, dict[str, object]],
    *,
    variable_id: str,
    datum: Mapping[str, object],
    source_snapshot_id: str,
    build_id: str,
    conflicts: list[dict[str, object]],
) -> None:
    semantics = {
        "source_taxon_group": copy.deepcopy(datum.get("taxongroup")),
        "source_ecological_group": copy.deepcopy(datum.get("ecologicalgroup")),
        "source_element": copy.deepcopy(datum.get("element")),
        "source_element_type": copy.deepcopy(datum.get("elementtype")),
    }
    unit = clean_optional_text(datum.get("units"))
    record = variables.get(variable_id)
    if record is None:
        variables[variable_id] = {
            "variable_id": variable_id,
            "source_taxon_id": copy.deepcopy(datum.get("taxonid")),
            "source_reported_name": copy.deepcopy(datum.get("variablename")),
            "source_semantics_by_digest": {_digest(semantics): semantics},
            "source_units": {unit} if unit else set(),
            "source_snapshot_id": source_snapshot_id,
            "build_id": build_id,
        }
        return
    if record.get("source_taxon_id") != datum.get("taxonid") or record.get(
        "source_reported_name"
    ) != datum.get("variablename"):
        conflicts.append(
            _conflict_record(
                "variable_identity_conflict",
                variable_id,
                {
                    "existing_taxon_id": record.get("source_taxon_id"),
                    "incoming_taxon_id": datum.get("taxonid"),
                    "existing_name": record.get("source_reported_name"),
                    "incoming_name": datum.get("variablename"),
                },
            )
        )
    semantics_by_digest = record["source_semantics_by_digest"]
    if isinstance(semantics_by_digest, dict):
        semantics_by_digest.setdefault(_digest(semantics), semantics)
    source_units = record["source_units"]
    if isinstance(source_units, set) and unit:
        source_units.add(unit)


def _finalize_variables(variables: list[dict[str, object]]) -> None:
    for variable in variables:
        semantics = variable.pop("source_semantics_by_digest", {})
        if isinstance(semantics, dict):
            variable["source_semantics"] = [semantics[key] for key in sorted(semantics)]
        units = variable.get("source_units")
        if isinstance(units, set):
            variable["source_units"] = sorted(units)


def _variable_id(datum: Mapping[str, object]) -> str:
    taxon_id = _optional_source_id(datum.get("taxonid"))
    name = clean_optional_text(datum.get("variablename"))
    if taxon_id is not None:
        return f"neotoma:variable:{taxon_id}"
    return f"neotoma:variable:unidentified:{_digest({'name': name})[:20]}"


def _unit_family(unit: str) -> str:
    return {
        "NISP": "count",
        "NISP digitized": "count",
        "number": "count",
        "NISP/tablet": "count_per_tablet",
        "grains/tablet": "count_per_tablet",
        "number/tablet": "count_per_tablet",
        "cm3": "volume",
        "cm^3": "volume",
        "ml": "volume",
        "g": "mass",
        "mg": "mass",
        "grains/cm3": "concentration_per_volume",
        "grains/ml": "concentration_per_volume",
        "grains/g": "concentration_per_mass",
        "grains/g sample": "concentration_per_mass",
        "grains/mg": "concentration_per_mass",
        "grains/cm²/yr": "influx_per_area_time",
        "particles/cm²/yr": "influx_per_area_time",
        "yr/cm": "sedimentation_time_per_depth",
    }.get(unit, "unresolved")


def _register(
    table: dict[str, dict[str, object]],
    record: dict[str, object],
    *,
    id_field: str,
    conflicts: list[dict[str, object]],
    conflict_kind: str,
) -> None:
    record_id = str(record[id_field])
    existing = table.get(record_id)
    if existing is None:
        table[record_id] = record
        return
    if existing != record:
        conflicts.append(
            _conflict_record(
                conflict_kind,
                record_id,
                {"existing": existing, "incoming": record},
            )
        )


def _required_source_id(
    value: object,
    entity_type: str,
    orphans: list[dict[str, object]],
    *,
    parent_id: str | None,
) -> str | None:
    source_id = _optional_source_id(value)
    if source_id is None:
        _add_orphan(
            orphans,
            entity_type,
            parent_id,
            "missing_source_identifier",
            source_value=value,
        )
    return source_id


def _optional_source_id(value: object) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return str(int(value))
    text = clean_optional_text(value)
    return text or None


def _finite_number(value: object) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value


def _country_code(value: str) -> str:
    cleaned = clean_optional_text(value)
    if cleaned in {"SE", "DK", "NO", "FI"}:
        return cleaned
    return _COUNTRY_CODES.get(cleaned, "UNASSIGNED")


def _country_attribution(
    value: CountryAttributionInput,
) -> _NeotomaCountryAttribution:
    if isinstance(value, str):
        legacy_country = clean_optional_text(value)
        return _NeotomaCountryAttribution(
            raw_country=None,
            derived_country=legacy_country or None,
            final_country_code="UNASSIGNED",
            decision_status="review",
            decision_method="legacy_unproven_country_string",
            candidate_countries=(legacy_country,) if legacy_country else (),
            ambiguity_reason="legacy_country_string_without_boundary_provenance",
            refusal_reason=None if legacy_country else "empty_legacy_country_string",
            boundary_artifact_digest=None,
            boundary_version=None,
            source_vs_derived_comparison="unresolved",
            propagation_eligible=False,
        )
    if not isinstance(value, CountryAttributionDecision):
        raise TypeError(
            "country_by_site_id values must be CountryAttributionDecision or str"
        )
    derived_code = _country_code(value.derived_country or "")
    propagation_eligible = (
        value.decision_status == "assigned"
        and value.decision_method == "strict_boundary_containment"
        and value.raw_country_comparison != "conflicts"
        and derived_code != "UNASSIGNED"
    )
    return _NeotomaCountryAttribution(
        raw_country=value.raw_country,
        derived_country=value.derived_country,
        final_country_code=derived_code if propagation_eligible else "UNASSIGNED",
        decision_status=value.decision_status,
        decision_method=value.decision_method,
        candidate_countries=value.candidate_countries,
        ambiguity_reason=value.ambiguity_reason,
        refusal_reason=value.refusal_reason,
        boundary_artifact_digest=value.boundary_artifact_digest,
        boundary_version=value.boundary_version,
        source_vs_derived_comparison=value.raw_country_comparison,
        propagation_eligible=propagation_eligible,
    )


def _missing_country_attribution(
    site: Mapping[str, object],
) -> _NeotomaCountryAttribution:
    return _NeotomaCountryAttribution(
        raw_country=_source_country(site),
        derived_country=None,
        final_country_code="UNASSIGNED",
        decision_status="unassigned",
        decision_method="missing_country_decision",
        candidate_countries=(),
        ambiguity_reason=None,
        refusal_reason="missing_country_decision",
        boundary_artifact_digest=None,
        boundary_version=None,
        source_vs_derived_comparison="unresolved",
        propagation_eligible=False,
    )


def _with_source_country(
    attribution: _NeotomaCountryAttribution,
    site: Mapping[str, object],
) -> _NeotomaCountryAttribution:
    source_country = _source_country(site)
    if source_country is None:
        return attribution
    if attribution.raw_country is not None and _country_code(
        attribution.raw_country
    ) != _country_code(source_country):
        raise ValueError("Country decision raw country conflicts with Neotoma source")
    return replace(attribution, raw_country=source_country)


def _source_country(site: Mapping[str, object]) -> str | None:
    geopolitical = site.get("geopolitical")
    if not isinstance(geopolitical, list):
        return None
    candidates: set[str] = set()
    for value in geopolitical:
        if isinstance(value, Mapping):
            candidate = clean_optional_text(value.get("country"))
        else:
            candidate = clean_optional_text(value)
        if _country_code(candidate) != "UNASSIGNED":
            candidates.add(candidate)
    if len(candidates) != 1:
        return None
    return candidates.pop()


def _country_attribution_counts(
    sites: list[dict[str, object]],
) -> dict[str, dict[str, int]]:
    raw_country_values: Counter[str] = Counter()
    derived_country_values: Counter[str] = Counter()
    raw_countries: Counter[str] = Counter()
    derived_countries: Counter[str] = Counter()
    final_countries: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    methods: Counter[str] = Counter()
    comparisons: Counter[str] = Counter()
    eligibility: Counter[str] = Counter()
    for site in sites:
        raw_country_values[str(site.get("raw_country") or "UNASSIGNED")] += 1
        derived_country_values[str(site.get("derived_country") or "UNASSIGNED")] += 1
        raw_countries[_country_code(str(site.get("raw_country") or ""))] += 1
        derived_countries[_country_code(str(site.get("derived_country") or ""))] += 1
        final_countries[str(site.get("country_code", "UNASSIGNED"))] += 1
        statuses[str(site.get("country_decision_status", "unassigned"))] += 1
        methods[str(site.get("country_decision_method", "unknown"))] += 1
        comparisons[str(site.get("source_vs_derived_comparison", "unresolved"))] += 1
        eligibility[
            "eligible"
            if site.get("country_propagation_eligible") is True
            else "blocked"
        ] += 1
    return {
        "raw_country_values": dict(sorted(raw_country_values.items())),
        "derived_country_values": dict(sorted(derived_country_values.items())),
        "raw_country_codes": dict(sorted(raw_countries.items())),
        "derived_country_codes": dict(sorted(derived_countries.items())),
        "final_country_codes": dict(sorted(final_countries.items())),
        "decision_statuses": dict(sorted(statuses.items())),
        "decision_methods": dict(sorted(methods.items())),
        "source_vs_derived_comparisons": dict(sorted(comparisons.items())),
        "propagation_eligibility": dict(sorted(eligibility.items())),
    }


def _parent_country(
    record: Mapping[str, object], sites: list[dict[str, object]]
) -> str:
    site_id = record.get("site_id")
    for site in sites:
        if site.get("site_id") == site_id:
            return str(site.get("country_code", "UNASSIGNED"))
    return "UNASSIGNED"


def _without(payload: Mapping[str, object], *keys: str) -> dict[str, object]:
    return {
        key: copy.deepcopy(value) for key, value in payload.items() if key not in keys
    }


def _digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _conflict_record(
    conflict_kind: str, subject_id: str, detail: Mapping[str, object]
) -> dict[str, object]:
    body = {
        "conflict_kind": conflict_kind,
        "subject_id": subject_id,
        "detail": copy.deepcopy(dict(detail)),
    }
    return {"conflict_id": f"neotoma:conflict:{_digest(body)[:24]}", **body}


def _add_orphan(
    orphans: list[dict[str, object]],
    entity_type: str,
    parent_id: str | None,
    reason: str,
    *,
    source_value: object = None,
) -> None:
    body = {
        "entity_type": entity_type,
        "parent_id": parent_id,
        "reason": reason,
        "source_value": copy.deepcopy(source_value),
    }
    orphans.append({"orphan_id": f"neotoma:orphan:{_digest(body)[:24]}", **body})
