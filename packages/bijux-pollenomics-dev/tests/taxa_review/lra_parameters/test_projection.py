"""The LRA parameter projection closes source rows without choosing parameters."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.evidence import digest
from bijux_pollenomics_dev.taxa_review.lra_parameters import (
    build_lra_parameter_review,
)
from bijux_pollenomics_dev.taxa_review.rows import review_row
from bijux_pollenomics_dev.taxa_review.workflow import assemble


def _sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _artifact_sha256(value: object) -> str:
    return hashlib.sha256(
        (
            json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n"
        ).encode()
    ).hexdigest()


def _review_artifact_sha256(value: object) -> str:
    return hashlib.sha256(
        (
            json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        ).encode()
    ).hexdigest()


def provenance_sha256(value: object) -> str:
    return _artifact_sha256(value)


def build(
    priority: dict[str, Any],
    provenance: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    return build_lra_parameter_review(
        priority,
        provenance,
        review,
        provenance_file_sha256=provenance_sha256(provenance),
    )


def authorities() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = {
        "hierarchy": {
            "groups": [
                {
                    "group_id": "woodland",
                    "subgroups": [{"subgroup_id": "deciduous_tree"}],
                }
            ]
        },
        "role_vocabulary": {
            "ecological_roles": ["tree"],
            "crop_evidence_roles": [],
        },
    }
    concepts = []
    for index, name in enumerate(("Betula", "Alnus"), 1):
        row = review_row(
            row_id=f"neotoma:concept:{index}",
            source="neotoma",
            native_id=index,
            label=name,
            domain="source_pollen",
            evidence={"source_unit": "NISP", "native_id": index},
        )
        concepts.append(row)
    ppe = review_row(
        row_id="parameter:ppe",
        source="lra_reference_resources",
        native_id=None,
        label="Betula",
        domain="reference_parameter_taxon",
        evidence={"path": "ppe.json", "ppe": 4.0},
    )
    ppe["parameter_candidates"] = [
        {
            "approval": "not_established",
            "source_values": {"ppe": 4.0, "ppe.error": 0.4},
        }
    ]
    fall = review_row(
        row_id="parameter:fall",
        source="landclim",
        native_id=None,
        label="Betula",
        domain="published_modeled_taxon_parameter",
        evidence={"path": "fall.csv", "source_fall_speed": "0.024"},
    )
    fall["parameter_candidates"] = [
        {
            "approval": "not_established",
            "fall_speed_source_text": "0.024",
            "fall_speed_units": "m/s",
        }
    ]
    review = assemble(
        [*concepts, ppe, fall],
        inputs=[{"path": "fixture", "sha256": "fixture"}],
        contract=contract,
        summaries={},
    )
    priority_rows = [
        {
            "review_row_id": concept["review_row_id"],
            "source_identity_sha256": concept["source_identity_sha256"],
            "source_reported_name": concept["source_reported_name"],
            "source_unit": "NISP",
            "review_state": "needs_discussion",
            "candidate_observation_count": index,
            "candidate_exact_count_sum": 10 * index,
            "candidate_observed_zero_count": 0,
            "candidate_sample_count": index,
            "candidate_country_observation_counts": {"SE": index},
            "candidate_country_exact_count_sums": {"SE": 10 * index},
        }
        for index, concept in enumerate(concepts, 1)
    ]
    common = {
        "source_snapshot_id": "sha256:" + "1" * 64,
        "raw_manifest_sha256": "2" * 64,
        "normalized_manifest_sha256": "3" * 64,
        "screen_candidate_ids_sha256": "4" * 64,
        "review_bundle_sha256": review["bundle_sha256"],
        "candidate_sample_count": 2,
        "candidate_pollen_observation_count": 3,
        "candidate_review_row_count": 2,
        "lra_accepted_samples": 0,
        "publication_allowed": False,
    }
    priority = {
        "schema_version": "neotoma-candidate-taxon-review-priority.v2",
        **common,
        "full_review_row_count": 4,
        "selected_review_state_counts": {"needs_discussion": 2},
        "rows": priority_rows,
        "input_file_sha256": {
            "full_review": _review_artifact_sha256(review),
            "raw_manifest": "2" * 64,
            "normalized_manifest": "3" * 64,
            "screen_report": "5" * 64,
        },
    }
    provenance_rows = [
        {
            "review_row_id": row["review_row_id"],
            "source_identity_sha256": row["source_identity_sha256"],
            "source_reported_name": row["source_reported_name"],
            "source_unit": row["source_unit"],
            "review_state": row["review_state"],
            "candidate_observation_count": row["candidate_observation_count"],
            "candidate_dataset_count": 1,
            "source_datasets": [
                {
                    "dataset_id": f"dataset:{index}",
                    "observation_count": row["candidate_observation_count"],
                    "sample_count": row["candidate_sample_count"],
                }
            ],
            "candidate_sample_count": row["candidate_sample_count"],
        }
        for index, row in enumerate(priority_rows, 1)
    ]
    provenance = {
        "schema_version": "neotoma-candidate-taxon-attribution.v1",
        **common,
        "candidate_dataset_count": 2,
        "dataset_doi_status_counts": {},
        "dataset_rows": [],
        "source_attribution_scope": "fixture",
        "rows": provenance_rows,
        "input_file_sha256": {
            "full_review": _review_artifact_sha256(review),
            "priority": _artifact_sha256(priority),
            "raw_manifest": "2" * 64,
            "normalized_manifest": "3" * 64,
            "screen_report": "5" * 64,
        },
    }
    assert (
        digest({key: value for key, value in review.items() if key != "bundle_sha256"})
        == review["bundle_sha256"]
    )
    return priority, provenance, review


def test_projection_is_complete_deterministic_and_non_admitting() -> None:
    priority, provenance, review = authorities()
    first = build(priority, provenance, review)
    second = build(priority, provenance, review)
    assert first == second
    assert first["denominators"] == {
        "candidate_pollen_observations": 3,
        "candidate_samples": 2,
        "candidate_taxon_concepts": 2,
        "full_review_rows": 4,
        "parameter_authority_capability_counts": {"fall_speed": 1, "ppe": 1},
        "parameter_authority_rows": 2,
        "projected_review_rows": 4,
    }
    assert first["parameter_candidate_extraction"] == "source_specific"
    assert first["taxon_parameter_matching"] == "not_performed"
    assert first["reviewer_authority"] == "declared_not_authenticated"
    assert first["lra_accepted_samples"] == 0
    assert first["executable_request"] is None
    assert first["scientific_acceptance"] == "not_evaluated"
    assert first["release_acceptance"] == "not_evaluated"
    content = {key: value for key, value in first.items() if key != "projection_sha256"}
    assert _sha256(content) == first["projection_sha256"]
    records = {
        row["parameter_record_id"]: row for row in first["parameter_authority_rows"]
    }
    ppe = records["parameter:ppe"]["parameter_candidates"][0]
    assert ppe["parameter_candidate_id"] == "parameter:ppe:candidate:1:ppe"
    assert ppe["source_value_text"] == "4.0"
    assert ppe["source_value"] == 4.0
    assert ppe["source_units"] == "relative_to_reference_taxon"
    assert ppe["parsing_status"] == "usable_finite_positive"


def _rebind_review(
    priority: dict[str, Any],
    provenance: dict[str, Any],
    review: dict[str, Any],
) -> None:
    review["bundle_sha256"] = digest(
        {key: value for key, value in review.items() if key != "bundle_sha256"}
    )
    priority["review_bundle_sha256"] = review["bundle_sha256"]
    provenance["review_bundle_sha256"] = review["bundle_sha256"]
    full = _review_artifact_sha256(review)
    priority["input_file_sha256"]["full_review"] = full
    provenance["input_file_sha256"]["full_review"] = full
    provenance["input_file_sha256"]["priority"] = _artifact_sha256(priority)


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("stale_priority", "another priority"),
        ("missing_concept", "denominator"),
        ("promoted_parameter", "promoted"),
        ("changed_source_identity", "source row"),
        ("dataset_sample_mismatch", "does not reconcile"),
    ],
)
def test_projection_refuses_incomplete_or_promoted_evidence(
    mutation: str, match: str
) -> None:
    priority, provenance, review = authorities()
    if mutation == "stale_priority":
        provenance["input_file_sha256"]["priority"] = "0" * 64
    elif mutation == "missing_concept":
        provenance["rows"].pop()
    elif mutation == "promoted_parameter":
        review["rows"][-1]["parameter_candidates"][0]["approval"] = "accepted"
        _rebind_review(priority, provenance, review)
    elif mutation == "changed_source_identity":
        priority["rows"][0]["source_identity_sha256"] = "changed"
        provenance["rows"][0]["source_identity_sha256"] = "changed"
        provenance["input_file_sha256"]["priority"] = _artifact_sha256(priority)
    else:
        provenance["rows"][0]["source_datasets"][0]["sample_count"] = 0
    with pytest.raises(ValueError, match=match):
        build(priority, provenance, review)


@pytest.mark.parametrize(
    "value,units,status",
    [
        (None, "m/s", "missing_source_value"),
        ("", "m/s", "empty_source_value"),
        ("not-a-number", "m/s", "nonnumeric_source_value"),
        ("0.024", "cm/s", "incompatible_source_units"),
    ],
)
def test_unusable_source_values_never_create_capabilities(
    value: object, units: str, status: str
) -> None:
    priority, provenance, review = authorities()
    source = next(
        row for row in review["rows"] if row["review_row_id"] == "parameter:fall"
    )
    candidate = source["parameter_candidates"][0]
    candidate["fall_speed_source_text"] = value
    candidate["fall_speed_units"] = units
    _rebind_review(priority, provenance, review)
    result = build(priority, provenance, review)
    record = next(
        row
        for row in result["parameter_authority_rows"]
        if row["parameter_record_id"] == "parameter:fall"
    )
    assert "fall_speed" not in record["capabilities"]
    extracted = [
        row
        for row in record["parameter_candidates"]
        if row["parameter_kind"] == "fall_speed"
    ]
    assert extracted[0]["parsing_status"] == status


def test_ambiguous_or_malformed_parameter_candidates_refuse() -> None:
    priority, provenance, review = authorities()
    review["rows"][-1]["parameter_candidates"].append(
        dict(review["rows"][-1]["parameter_candidates"][0])
    )
    _rebind_review(priority, provenance, review)
    with pytest.raises(ValueError, match="ambiguous"):
        build(priority, provenance, review)

    priority, provenance, review = authorities()
    review["rows"][-1]["parameter_candidates"] = [None]
    _rebind_review(priority, provenance, review)
    with pytest.raises(ValueError, match="malformed"):
        build(priority, provenance, review)


def test_zero_source_uncertainty_is_usable_not_a_zero_parameter() -> None:
    priority, provenance, review = authorities()
    source = next(
        row for row in review["rows"] if row["review_row_id"] == "parameter:ppe"
    )
    source["parameter_candidates"][0]["source_values"]["ppe.error"] = 0.0
    _rebind_review(priority, provenance, review)
    result = build(priority, provenance, review)
    record = next(
        row
        for row in result["parameter_authority_rows"]
        if row["parameter_record_id"] == "parameter:ppe"
    )
    candidate = next(
        row for row in record["parameter_candidates"] if row["parameter_kind"] == "ppe"
    )
    assert "ppe" in record["capabilities"]
    assert candidate["source_uncertainty_value"] == 0.0
    assert candidate["parsing_status"] == "usable_finite_positive"


def test_full_review_denominator_must_reconcile() -> None:
    priority, provenance, review = authorities()
    priority["full_review_row_count"] += 1
    provenance["input_file_sha256"]["priority"] = _artifact_sha256(priority)
    with pytest.raises(ValueError, match="denominator"):
        build(priority, provenance, review)


def test_full_review_and_provenance_pins_must_match_content() -> None:
    priority, provenance, review = authorities()
    priority["input_file_sha256"]["full_review"] = "a" * 64
    provenance["input_file_sha256"]["full_review"] = "a" * 64
    with pytest.raises(ValueError, match="another taxa review"):
        build(priority, provenance, review)

    priority, provenance, review = authorities()
    with pytest.raises(ValueError, match="pinned provenance identity"):
        build_lra_parameter_review(
            priority,
            provenance,
            review,
            provenance_file_sha256="b" * 64,
        )
