"""Strict validation for returned Neotoma prerequisite review decisions."""

from __future__ import annotations

from datetime import date
import hashlib
import math
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
from bijux_pollenomics.analysis.lra.materialization.reading import NeotomaEvidence

from .projection import (
    NeotomaPrerequisiteProjection,
    build_neotoma_prerequisite_projection,
)

_RETURNED_FIELDS = {
    "schema_version",
    "projection_sha256",
    "chronology_decisions",
    "basin_decisions",
}
_COMMON_FIELDS = {
    "reviewer_id",
    "decision_date",
    "rationale",
    "evidence_reference_ids",
    "source_row_sha256",
}
_CHRONOLOGY_FIELDS = _COMMON_FIELDS | {
    "sample_id",
    "disposition",
    "selected_age_claim_id",
    "selected_age_claim_sha256",
}
_BASIN_FIELDS = _COMMON_FIELDS | {
    "site_id",
    "disposition",
    "selected_basin_evidence_sha256",
    "selected_source_field",
    "selected_source_value",
    "selected_source_unit",
    "selected_source_domain",
    "support_disposition",
    "selected_support_evidence_sha256",
}


def _common(row: dict[str, Any]) -> None:
    for field in ("reviewer_id", "rationale"):
        value = row[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a nonempty string")
    value = row["decision_date"]
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("decision_date must be an exact ISO calendar date")
    references = row["evidence_reference_ids"]
    if (
        not isinstance(references, list)
        or references != sorted(set(references))
        or any(not isinstance(item, str) or not item.strip() for item in references)
        or not references
    ):
        raise ValueError("Evidence references must be nonempty canonical strings")


def _rows(value: object, name: str, fields: set[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise TypeError(f"{name} must be a list")
    result = []
    for row in value:
        if not isinstance(row, dict) or set(row) != fields:
            raise ValueError(f"{name} fields differ from the exact schema")
        _common(row)
        result.append(row)
    return result


def validate_returned_prerequisite_decisions(
    projection: NeotomaPrerequisiteProjection,
    returned: dict[str, Any],
    *,
    evidence: NeotomaEvidence,
    lakeparameter_capture_root: Path,
    expected_lakeparameter_capture_sha256: str,
) -> dict[str, Any]:
    """Validate complete review intent while keeping all scientific gates closed."""
    try:
        returned_bytes = canonical_bytes(returned)
    except (TypeError, ValueError) as error:
        raise ValueError("Returned decisions are not canonical finite JSON") from error
    returned_digest = hashlib.sha256(returned_bytes).hexdigest()
    projection.assert_authenticated()
    rebuilt = build_neotoma_prerequisite_projection(
        evidence,
        lakeparameter_capture_root=lakeparameter_capture_root,
        expected_lakeparameter_capture_sha256=expected_lakeparameter_capture_sha256,
    )
    if (
        projection.canonical_json != rebuilt.canonical_json
        or projection.result_digest != rebuilt.result_digest
    ):
        raise ValueError("Projection differs from rebuilt original authorities")
    source = projection.as_dict()
    if set(returned) != _RETURNED_FIELDS:
        raise ValueError("Returned decision document fields differ")
    if (
        returned["schema_version"] != "neotoma-lra-prerequisite-returned-decisions.v1"
        or returned["projection_sha256"] != projection.result_digest
    ):
        raise ValueError("Returned decisions target a stale projection")

    expected_chronology = {row["sample_id"]: row for row in source["chronology_rows"]}
    chronology = _rows(
        returned["chronology_decisions"],
        "chronology_decisions",
        _CHRONOLOGY_FIELDS,
    )
    chronology_ids = [row["sample_id"] for row in chronology]
    if chronology_ids != sorted(expected_chronology) or len(set(chronology_ids)) != len(
        chronology_ids
    ):
        raise ValueError(
            "Chronology decisions do not canonically close the denominator"
        )
    for row in chronology:
        expected = expected_chronology[row["sample_id"]]
        if row["source_row_sha256"] != expected["source_row_sha256"]:
            raise ValueError("Chronology decision source row is stale")
        disposition = row["disposition"]
        if disposition not in {"selected_candidate", "insufficient_evidence"}:
            raise ValueError("Unknown chronology disposition")
        if (
            expected["country_code"] == "UNASSIGNED"
            and disposition != "insufficient_evidence"
        ):
            raise ValueError("Unassigned-country chronology must remain insufficient")
        selected = (row["selected_age_claim_id"], row["selected_age_claim_sha256"])
        candidates = {
            (item["chronology_claim_id"], item["source_row_sha256"])
            for item in expected["candidate_age_claims"]
        }
        if disposition == "selected_candidate" and selected not in candidates:
            raise ValueError("Selected chronology is not an exact observed candidate")
        if disposition == "insufficient_evidence" and selected != (None, None):
            raise ValueError("Unresolved chronology cannot select a candidate")

    expected_basins = {row["site_id"]: row for row in source["basin_rows"]}
    basins = _rows(returned["basin_decisions"], "basin_decisions", _BASIN_FIELDS)
    basin_ids = [row["site_id"] for row in basins]
    if basin_ids != sorted(expected_basins) or len(set(basin_ids)) != len(basin_ids):
        raise ValueError("Basin decisions do not canonically close the denominator")
    for row in basins:
        expected = expected_basins[row["site_id"]]
        if row["source_row_sha256"] != expected["source_row_sha256"]:
            raise ValueError("Basin decision source row is stale")
        if (
            row["support_disposition"] != "not_observed"
            or row["selected_support_evidence_sha256"] is not None
        ):
            raise ValueError("Returned support must not invent unobserved evidence")
        if (
            expected["country_code"] == "UNASSIGNED"
            and row["disposition"] != "insufficient_evidence"
        ):
            raise ValueError("Unassigned-country basin must remain insufficient")
        selection = (
            row["selected_basin_evidence_sha256"],
            row["selected_source_field"],
            row["selected_source_value"],
            row["selected_source_unit"],
            row["selected_source_domain"],
        )
        if row["disposition"] == "insufficient_evidence":
            if selection != (None, None, None, None, None):
                raise ValueError("Unresolved basin decision cannot select evidence")
            continue
        if row["disposition"] != "selected_candidate":
            raise ValueError("Unknown basin disposition")
        value = row["selected_source_value"]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
        ):
            raise ValueError(
                "Selected basin evidence is not positive observed area with units"
            )
        basin_candidates = {
            (
                item["source_row_sha256"],
                item["source_field"],
                item["source_value"],
                item["source_unit"],
                item["source_domain"],
            ): item
            for item in expected["candidate_basin_evidence"]
        }
        candidate = basin_candidates.get(selection)
        if (
            candidate is None
            or candidate["source_domain"] != "area"
            or candidate["value_status"] != "positive"
            or candidate["unit_status"] == "not_observed"
        ):
            raise ValueError(
                "Selected basin evidence is not positive observed area with units"
            )

    if canonical_bytes(returned) != returned_bytes:
        raise ValueError("Returned decisions changed during validation")
    result = {
        "schema_version": "neotoma-lra-prerequisite-validation.v1",
        "projection_sha256": projection.result_digest,
        "returned_decisions_sha256": returned_digest,
        "chronology_decision_count": len(chronology),
        "basin_decision_count": len(basins),
        "reviewer_authority": "declared_not_authenticated",
        "accepted_samples": 0,
        "executable_request": None,
        "scientific_acceptance": "not_evaluated",
        "release_status": "not_evaluated",
    }
    return {
        **result,
        "validation_sha256": hashlib.sha256(canonical_bytes(result)).hexdigest(),
    }


__all__ = ["validate_returned_prerequisite_decisions"]
