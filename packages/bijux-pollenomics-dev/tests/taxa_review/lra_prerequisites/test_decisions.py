"""Returned chronology and basin decisions remain complete and non-admitting."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import math
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
from bijux_pollenomics_dev.taxa_review.lra_prerequisites import (
    projection as projection_module,
)
from bijux_pollenomics_dev.taxa_review.lra_prerequisites.decisions import (
    validate_returned_prerequisite_decisions,
)
from bijux_pollenomics_dev.taxa_review.lra_prerequisites.projection import (
    NeotomaPrerequisiteProjection,
)


def _projection(*, unassigned: bool = False) -> NeotomaPrerequisiteProjection:
    chronology: list[dict[str, Any]] = []
    for index in (1, 2):
        claim = {
            "chronology_claim_id": f"claim:{index}",
            "source_locator": {"surface": "age_claims", "row_index": index},
            "source_claim": {"subject_id": f"sample:{index}", "younger_bp": 10},
        }
        claim = {**claim, "source_row_sha256": projection_module._digest(claim)}
        alternate = {
            "chronology_claim_id": f"claim:{index}:alternate",
            "source_locator": {"surface": "age_claims", "row_index": index + 10},
            "source_claim": {
                "subject_id": f"sample:{index}",
                "younger_bp": 20,
            },
        }
        alternate = {
            **alternate,
            "source_row_sha256": projection_module._digest(alternate),
        }
        row: dict[str, Any] = {
            "sample_id": f"sample:{index}",
            "site_id": f"site:{index}",
            "country_code": "UNASSIGNED" if unassigned and index == 2 else "SE",
            "source_screen_row_sha256": str(index) * 64,
            "candidate_age_claims": [claim, alternate],
            "chronology_disposition": "not_evaluated",
        }
        chronology.append({**row, "source_row_sha256": projection_module._digest(row)})
    basins: list[dict[str, Any]] = []
    for index in (1, 2):
        evidence: dict[str, Any] = {
            "source_field": "lakeparameters.value:3",
            "source_value": float(index),
            "source_unit": "Surface area (ha)",
            "source_domain": "area",
            "source_row_locator": {"page": "page.json", "row_index": index},
            "source_parameter_code": "Area",
            "value_status": "positive",
            "unit_status": "source_parameter_label",
        }
        evidence = {
            **evidence,
            "source_row_sha256": projection_module._digest(evidence),
        }
        row = {
            "site_id": f"site:{index}",
            "country_code": "UNASSIGNED" if unassigned and index == 2 else "SE",
            "candidate_sample_count": 1,
            "source_site_row_sha256": str(index) * 64,
            "candidate_basin_evidence": [evidence],
            "support_evidence": [],
            "basin_disposition": "not_evaluated",
        }
        basins.append({**row, "source_row_sha256": projection_module._digest(row)})
    payload = {
        "schema_version": "neotoma-lra-prerequisite-review-projection.v1",
        "source_family": "neotoma",
        "source_identities": {},
        "denominators": {
            "necessary_samples": 2,
            "source_sites": 2,
            "chronology_decisions_required": 2,
            "basin_decisions_required": 2,
            "accepted_samples": 0,
        },
        "chronology_rows": chronology,
        "basin_rows": basins,
        "reviewer_authority": "declared_not_authenticated",
        "scientific_acceptance": "not_evaluated",
        "release_status": "not_evaluated",
        "executable_request": None,
    }
    return NeotomaPrerequisiteProjection(
        canonical_bytes(payload), projection_module._AUTHORITY
    )


def _review(
    projection: NeotomaPrerequisiteProjection | None = None,
) -> tuple[NeotomaPrerequisiteProjection, dict[str, Any]]:
    projection = projection or _projection()
    source = projection.as_dict()
    chronology = []
    for row in source["chronology_rows"]:
        claim = row["candidate_age_claims"][0]
        chronology.append(
            {
                "sample_id": row["sample_id"],
                "source_row_sha256": row["source_row_sha256"],
                "disposition": "selected_candidate",
                "selected_age_claim_id": claim["chronology_claim_id"],
                "selected_age_claim_sha256": claim["source_row_sha256"],
                "reviewer_id": "reviewer-1",
                "decision_date": "2026-09-24",
                "rationale": "The source claim is retained for later scientific review.",
                "evidence_reference_ids": ["evidence:chronology"],
            }
        )
    basins = []
    for row in source["basin_rows"]:
        evidence = row["candidate_basin_evidence"][0]
        basins.append(
            {
                "site_id": row["site_id"],
                "source_row_sha256": row["source_row_sha256"],
                "disposition": "selected_candidate",
                "selected_basin_evidence_sha256": evidence["source_row_sha256"],
                "selected_source_field": evidence["source_field"],
                "selected_source_value": evidence["source_value"],
                "selected_source_unit": evidence["source_unit"],
                "selected_source_domain": evidence["source_domain"],
                "support_disposition": "not_observed",
                "selected_support_evidence_sha256": None,
                "reviewer_id": "reviewer-1",
                "decision_date": "2026-09-24",
                "rationale": "The observed area is retained without conversion.",
                "evidence_reference_ids": ["evidence:basin"],
            }
        )
    return projection, {
        "schema_version": "neotoma-lra-prerequisite-returned-decisions.v1",
        "projection_sha256": projection.result_digest,
        "chronology_decisions": chronology,
        "basin_decisions": basins,
    }


def _validate(
    monkeypatch: pytest.MonkeyPatch,
    projection: NeotomaPrerequisiteProjection,
    returned: dict[str, Any],
) -> dict[str, Any]:
    observed: dict[str, object] = {}

    def rebuild(
        evidence: object,
        *,
        lakeparameter_capture_root: Path,
        expected_lakeparameter_capture_sha256: str,
    ) -> NeotomaPrerequisiteProjection:
        observed.update(
            evidence=evidence,
            root=lakeparameter_capture_root,
            sha=expected_lakeparameter_capture_sha256,
        )
        return projection

    monkeypatch.setattr(
        "bijux_pollenomics_dev.taxa_review.lra_prerequisites.decisions."
        "build_neotoma_prerequisite_projection",
        rebuild,
    )
    result = validate_returned_prerequisite_decisions(
        projection,
        returned,
        evidence=object(),  # type: ignore[arg-type]
        lakeparameter_capture_root=Path("capture"),
        expected_lakeparameter_capture_sha256="a" * 64,
    )
    assert observed == {
        "evidence": observed["evidence"],
        "root": Path("capture"),
        "sha": "a" * 64,
    }
    return result


def test_complete_return_stays_outcome_free_and_non_executable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection, returned = _review()
    result = _validate(monkeypatch, projection, returned)
    assert result == {
        "schema_version": "neotoma-lra-prerequisite-validation.v1",
        "projection_sha256": projection.result_digest,
        "returned_decisions_sha256": result["returned_decisions_sha256"],
        "validation_sha256": result["validation_sha256"],
        "chronology_decision_count": 2,
        "basin_decision_count": 2,
        "reviewer_authority": "declared_not_authenticated",
        "accepted_samples": 0,
        "executable_request": None,
        "scientific_acceptance": "not_evaluated",
        "release_status": "not_evaluated",
    }
    validation_body = {
        key: value for key, value in result.items() if key != "validation_sha256"
    }
    assert (
        result["returned_decisions_sha256"]
        == hashlib.sha256(canonical_bytes(returned)).hexdigest()
    )
    assert (
        result["validation_sha256"]
        == hashlib.sha256(canonical_bytes(validation_body)).hexdigest()
    )


def test_different_valid_candidate_rebinds_validation_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection, returned = _review()
    first = _validate(monkeypatch, projection, returned)
    alternate = projection.as_dict()["chronology_rows"][0]["candidate_age_claims"][1]
    changed = deepcopy(returned)
    changed["chronology_decisions"][0]["selected_age_claim_id"] = alternate[
        "chronology_claim_id"
    ]
    changed["chronology_decisions"][0]["selected_age_claim_sha256"] = alternate[
        "source_row_sha256"
    ]
    second = _validate(monkeypatch, projection, changed)
    assert first["returned_decisions_sha256"] != second["returned_decisions_sha256"]
    assert first["validation_sha256"] != second["validation_sha256"]


@pytest.mark.parametrize("kind", ["missing", "duplicate", "reordered"])
def test_partial_duplicate_or_noncanonical_closure_is_refused(
    monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    projection, returned = _review()
    rows = returned["chronology_decisions"]
    if kind == "missing":
        rows.pop()
    elif kind == "duplicate":
        rows[1] = deepcopy(rows[0])
    else:
        rows.reverse()
    with pytest.raises(ValueError, match="canonically close"):
        _validate(monkeypatch, projection, returned)


def test_stale_rows_and_rehashed_projection_shapes_are_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection, returned = _review()
    returned["chronology_decisions"][0]["source_row_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source row is stale"):
        _validate(monkeypatch, projection, returned)
    with pytest.raises(ValueError, match="original authorities"):
        NeotomaPrerequisiteProjection(projection.canonical_json, object())


def test_projection_is_rebuilt_from_original_authorities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection, returned = _review()
    forged_payload = projection.as_dict()
    forged_payload["source_identities"] = {"forged": "rehash"}
    forged = NeotomaPrerequisiteProjection(
        canonical_bytes(forged_payload), projection_module._AUTHORITY
    )
    monkeypatch.setattr(
        "bijux_pollenomics_dev.taxa_review.lra_prerequisites.decisions."
        "build_neotoma_prerequisite_projection",
        lambda *_args, **_kwargs: projection,
    )
    with pytest.raises(ValueError, match="rebuilt original authorities"):
        validate_returned_prerequisite_decisions(
            forged,
            returned,
            evidence=object(),  # type: ignore[arg-type]
            lakeparameter_capture_root=Path("capture"),
            expected_lakeparameter_capture_sha256="a" * 64,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("selected_source_value", 9.0, "positive observed area"),
        ("selected_source_value", 0.0, "positive observed area"),
        ("selected_source_value", math.inf, "canonical finite JSON"),
        ("selected_source_unit", "m2", "positive observed area"),
        (
            "selected_source_field",
            "sites.source_payload.radius",
            "positive observed area",
        ),
        ("selected_source_domain", "radius", "positive observed area"),
    ],
)
def test_basin_selection_must_exactly_match_positive_observed_area(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object, message: str
) -> None:
    projection, returned = _review()
    returned["basin_decisions"][0][field] = value
    with pytest.raises(ValueError, match=message):
        _validate(monkeypatch, projection, returned)


def test_support_and_unresolved_rows_cannot_invent_selections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection, returned = _review()
    returned["basin_decisions"][0]["selected_support_evidence_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="invent unobserved"):
        _validate(monkeypatch, projection, returned)
    projection, returned = _review()
    row = returned["chronology_decisions"][0]
    row["disposition"] = "insufficient_evidence"
    with pytest.raises(ValueError, match="cannot select"):
        _validate(monkeypatch, projection, returned)


def test_unassigned_country_cannot_select_chronology_or_basin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projection, returned = _review(_projection(unassigned=True))
    with pytest.raises(ValueError, match="Unassigned-country chronology"):
        _validate(monkeypatch, projection, returned)
    chronology = returned["chronology_decisions"][1]
    chronology.update(
        disposition="insufficient_evidence",
        selected_age_claim_id=None,
        selected_age_claim_sha256=None,
    )
    with pytest.raises(ValueError, match="Unassigned-country basin"):
        _validate(monkeypatch, projection, returned)
    basin = returned["basin_decisions"][1]
    basin.update(
        disposition="insufficient_evidence",
        selected_basin_evidence_sha256=None,
        selected_source_field=None,
        selected_source_value=None,
        selected_source_unit=None,
        selected_source_domain=None,
    )
    result = _validate(monkeypatch, projection, returned)
    assert result["accepted_samples"] == 0
