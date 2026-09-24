"""Returned parameter intent is complete, source-bound and never admission."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

import pytest

from bijux_pollenomics_dev.taxa_review.lra_parameters import (
    validate_lra_parameter_decisions,
)
from tests.taxa_review.lra_parameters.test_projection import (
    authorities,
    build,
    provenance_sha256,
)


def projection() -> tuple[
    dict[str, Any], tuple[dict[str, Any], dict[str, Any], dict[str, Any]]
]:
    source = authorities()
    return build(*source), source


def validate(
    payload: dict[str, Any],
    decisions: dict[str, Any],
    source: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
) -> dict[str, Any]:
    return validate_lra_parameter_decisions(
        payload,
        decisions,
        priority=source[0],
        provenance=source[1],
        review=source[2],
        provenance_file_sha256=provenance_sha256(source[1]),
    )


def binding(payload: dict[str, Any], record_id: str, *, kind: str) -> dict[str, Any]:
    records = {
        row["parameter_record_id"]: row for row in payload["parameter_authority_rows"]
    }
    candidates = [
        candidate
        for candidate in records[record_id]["parameter_candidates"]
        if candidate["parameter_kind"] == kind
        and candidate["parsing_status"] == "usable_finite_positive"
    ]
    assert len(candidates) == 1
    candidate = candidates[0]
    return {
        "parameter_record_id": record_id,
        "parameter_record_sha256": records[record_id]["parameter_record_sha256"],
        "parameter_candidate_id": candidate["parameter_candidate_id"],
        "parameter_candidate_sha256": candidate["parameter_candidate_sha256"],
        "source_value_text": candidate["source_value_text"],
        "source_value": candidate["source_value"],
        "source_units": candidate["source_units"],
        "normalized_value": candidate["source_value"],
        "normalized_units": candidate["source_units"],
        "reference_taxon": "Poaceae" if kind == "ppe" else None,
        "source_uncertainty_text": candidate["source_uncertainty_text"],
        "source_uncertainty_value": candidate["source_uncertainty_value"],
        "applicability_domain": "fixture Nordic pollen model review only",
        "normalization_rationale": "Identity normalization from selected source value",
    }


def returned(payload: dict[str, Any]) -> dict[str, Any]:
    decisions = []
    for index, row in enumerate(payload["candidate_taxon_rows"]):
        retained = index == 0
        decisions.append(
            {
                "review_row_id": row["review_row_id"],
                "source_identity_sha256": row["source_identity_sha256"],
                "disposition": "retained_intent" if retained else "unresolved",
                "accepted_taxon_name": "Betula" if retained else None,
                "accepted_taxon_rank": "genus" if retained else None,
                "lra_model_taxon_id": "model-taxon:betula" if retained else None,
                "primary_group_id": "woodland" if retained else None,
                "primary_subgroup_id": "deciduous_tree" if retained else None,
                "role_ids": ["tree"] if retained else [],
                "ppe_binding": (
                    binding(payload, "parameter:ppe", kind="ppe") if retained else None
                ),
                "fall_speed_binding": (
                    binding(payload, "parameter:fall", kind="fall_speed")
                    if retained
                    else None
                ),
                "reviewer_id": "fixture-reviewer",
                "decision_date": "2026-09-24",
                "rationale": "Fixture decision shape; not scientific acceptance",
                "evidence_reference_ids": ["fixture:evidence"],
            }
        )
    return {
        "schema_version": "neotoma-lra-parameter-decisions.v1",
        "projection_sha256": payload["projection_sha256"],
        "reviewer_authority": "declared_not_authenticated",
        "decisions": decisions,
    }


def test_complete_return_remains_non_admitting_intent() -> None:
    payload, source = projection()
    result = validate(payload, returned(payload), source)
    assert result["decision_count"] == 2
    assert result["disposition_counts"] == {
        "retained_intent": 1,
        "unresolved": 1,
    }
    assert result["reviewer_authority"] == "declared_not_authenticated"
    assert result["qualified_scientific_review_verified"] is False
    assert result["canonical_import_allowed"] is False
    assert result["lra_accepted_samples"] == 0
    assert result["executable_request"] is None
    assert result["scientific_acceptance"] == "not_evaluated"
    assert result["release_acceptance"] == "not_evaluated"


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("missing", "close"),
        ("duplicate", "duplicated"),
        ("stale_source", "stale source"),
        ("stale_parameter", "stale parameter"),
        ("stale_candidate", "stale parameter candidate"),
        ("wrong_capability", "unsupported parameter"),
        ("nonfinite", "finite JSON"),
        ("wrong_units", "normalized units"),
        ("source_value_mismatch", "selected source evidence"),
        ("arbitrary_normalized", "lacks selected source evidence"),
        ("unknown_group", "do not belong"),
        ("mapping_on_unresolved", "must not carry"),
    ],
)
def test_invalid_or_incomplete_returns_refuse(mutation: str, match: str) -> None:
    payload, source = projection()
    decisions = returned(payload)
    first = decisions["decisions"][0]
    if mutation == "missing":
        decisions["decisions"].pop()
    elif mutation == "duplicate":
        decisions["decisions"][1] = deepcopy(first)
    elif mutation == "stale_source":
        first["source_identity_sha256"] = "0" * 64
    elif mutation == "stale_parameter":
        first["ppe_binding"]["parameter_record_sha256"] = "0" * 64
    elif mutation == "stale_candidate":
        first["ppe_binding"]["parameter_candidate_sha256"] = "0" * 64
    elif mutation == "wrong_capability":
        records = {
            row["parameter_record_id"]: row
            for row in payload["parameter_authority_rows"]
        }
        first["ppe_binding"]["parameter_record_id"] = "parameter:fall"
        first["ppe_binding"]["parameter_record_sha256"] = records["parameter:fall"][
            "parameter_record_sha256"
        ]
    elif mutation == "nonfinite":
        first["ppe_binding"]["normalized_value"] = float("nan")
    elif mutation == "wrong_units":
        first["fall_speed_binding"]["normalized_units"] = "cm/s"
    elif mutation == "source_value_mismatch":
        first["ppe_binding"]["source_value"] = 99.0
    elif mutation == "arbitrary_normalized":
        first["ppe_binding"]["normalized_value"] = 99.0
    elif mutation == "unknown_group":
        first["primary_group_id"] = "invented"
    else:
        decisions["decisions"][1]["accepted_taxon_name"] = "Alnus"
    with pytest.raises(ValueError, match=match):
        validate(payload, decisions, source)


def test_parameter_uncertainty_and_evidence_are_explicit() -> None:
    payload, source = projection()
    decisions = returned(payload)
    ppe = decisions["decisions"][0]["ppe_binding"]
    assert ppe["source_uncertainty_text"] == "0.4"
    assert ppe["source_uncertainty_value"] == 0.4
    ppe["source_uncertainty_value"] = None
    with pytest.raises(ValueError, match="selected source evidence"):
        validate(payload, decisions, source)


@pytest.mark.parametrize("malformed", [False, True])
def test_self_rehashed_or_malformed_projection_refuses(malformed: bool) -> None:
    payload, source = projection()
    decisions = returned(payload)
    forged = deepcopy(payload)
    if malformed:
        forged["parameter_authority_rows"][0]["parameter_candidates"] = [None]
    else:
        forged["candidate_taxon_rows"][0]["candidate_observation_count"] += 1
    content = {
        key: value for key, value in forged.items() if key != "projection_sha256"
    }
    forged["projection_sha256"] = hashlib.sha256(
        json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    decisions["projection_sha256"] = forged["projection_sha256"]
    with pytest.raises(ValueError, match="pinned source rebuild"):
        validate(forged, decisions, source)
