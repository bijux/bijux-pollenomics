"""Sample chronology claims and temporal admission posture."""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping

from .....core.text import clean_optional_text
from .diagnostics import add_orphan
from .identifiers import digest, optional_source_id


def build_age_claim(
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
    chronology_source_id = optional_source_id(age.get("chronologyid"))
    chronology_id = (
        chronology_ids_by_source.get(chronology_source_id)
        if chronology_source_id is not None
        else None
    )
    if (
        chronology_source_id is not None
        and chronology_source_id not in chronology_ids_by_source
    ):
        add_orphan(
            orphans,
            "age_claim",
            sample_id,
            "chronology_not_found",
            source_value=age.get("chronologyid"),
        )
    temporal = age_temporal_posture(age)
    claim_digest = digest(
        {
            "sample_id": sample_id,
            "dataset_id": dataset_id,
            "source_payload": dict(age),
        }
    )
    return {
        "chronology_claim_id": f"neotoma:age-claim:{claim_digest[:24]}:{occurrence}",
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


def age_temporal_posture(age: Mapping[str, object]) -> dict[str, object]:
    age_type = clean_optional_text(age.get("agetype"))
    if not age_type:
        return temporal_result(
            "unresolved", "unresolved", None, None, "missing_age_type"
        )
    if age_type == "Radiocarbon years BP":
        return temporal_result(
            "uncalibrated", "context_only", None, None, "uncalibrated_radiocarbon"
        )
    if age_type == "Varve years BP":
        return temporal_result(
            "not_calibrated", "context_only", None, None, "ungoverned_varve_basis"
        )
    if age_type not in {
        "Calibrated radiocarbon years BP",
        "Calendar years BP",
    }:
        return temporal_result(
            "unresolved", "unresolved", None, None, "unknown_age_type"
        )

    calibration_status = (
        "calibrated"
        if age_type == "Calibrated radiocarbon years BP"
        else "not_applicable"
    )
    younger = finite_number(age.get("ageyounger"))
    older = finite_number(age.get("ageolder"))
    if (younger is None) != (older is None):
        return temporal_result(
            calibration_status, "refused", None, None, "partial_interval"
        )
    if younger is None and older is None:
        point = finite_number(age.get("age"))
        if point is None:
            return temporal_result(
                calibration_status, "refused", None, None, "missing_numeric_age"
            )
        younger = older = point
    if younger is None or older is None:
        return temporal_result(
            calibration_status, "refused", None, None, "partial_interval"
        )
    if younger < 0 or older < 0:
        return temporal_result(calibration_status, "refused", None, None, "negative_bp")
    if younger > older:
        return temporal_result(
            calibration_status, "refused", None, None, "reversed_interval"
        )
    return temporal_result(calibration_status, "comparable", younger, older, None)


def temporal_result(
    calibration_status: str,
    comparability_status: str,
    younger_bp: float | None,
    older_bp: float | None,
    reason_code: str | None,
) -> dict[str, object]:
    return {
        "calibration_status": calibration_status,
        "comparability_status": comparability_status,
        "younger_bp": younger_bp,
        "older_bp": older_bp,
        "reason_code": reason_code,
    }


def finite_number(value: object) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value
