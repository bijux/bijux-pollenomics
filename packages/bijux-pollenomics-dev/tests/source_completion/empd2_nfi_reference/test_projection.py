"""Source projection stays exact, deterministic, and refusal-first."""

from __future__ import annotations

import json
from hashlib import sha256

import pytest
from bijux_pollenomics_dev.source_completion.empd2_nfi_reference import (
    build_empd2_nfi_decision_projection,
    review_empd2_nfi_decisions,
)

from .factories import json_bytes, nfi_schema, parameter_manifest, projection, sources


def test_absent_return_is_deterministic_zero_admission_projection() -> None:
    first = review_empd2_nfi_decisions(**sources())
    second = review_empd2_nfi_decisions(**sources())
    assert first == second
    assert first.cohort is None
    assert first.projection["candidate_count"] == 16
    assert first.projection["admitted_pair_count"] == 0
    assert first.validation["awaiting_review_count"] == 16
    assert first.validation["outcome_access_status"] == "not_started"
    assert first.validation["scientific_acceptance"] == "not_evaluated"


def test_projection_binds_source_identities_and_country() -> None:
    inputs = sources()
    result = build_empd2_nfi_decision_projection(**inputs)
    assert result["source_identities"] == {
        "dossier": inputs["dossier_sha256"],
        "spatial": inputs["spatial_sha256"],
        "guide": inputs["guide_sha256"],
        "nfi_workbook": inputs["workbook_sha256"],
        "empd2_source": "5" * 64,
        "empd2_screen": "6" * 64,
        "nfi_eligibility": "a" * 64,
        "nfi_schema": nfi_schema()[1],
    }
    assert [row["record_id"] for row in result["candidate_rows"]] == sorted(
        row["record_id"] for row in result["candidate_rows"]
    )
    assert {row["source_country"] for row in result["candidate_rows"]} == {"Sweden"}
    assert {row["country_code"] for row in result["candidate_rows"]} == {"SE"}
    assert (
        len(
            {
                (row["nfi_tract"], row["nfi_plot"], row["nfi_year"])
                for row in result["candidate_rows"]
            }
        )
        == 14
    )


def test_pending_projection_rejects_unused_review_baggage() -> None:
    parameter_bytes, parameter_sha, _ = parameter_manifest(projection())
    with pytest.raises(ValueError, match="review baggage"):
        review_empd2_nfi_decisions(
            **sources(),
            taxon_parameter_manifest_bytes=parameter_bytes,
            taxon_parameter_manifest_sha256=parameter_sha,
        )
    schema_bytes, schema_sha = nfi_schema()
    with pytest.raises(ValueError, match="review baggage"):
        review_empd2_nfi_decisions(
            **sources(),
            nfi_schema_bytes=schema_bytes,
            nfi_schema_sha256=schema_sha,
        )


def test_stale_or_rebound_source_changes_projection_identity() -> None:
    inputs = sources()
    original = build_empd2_nfi_decision_projection(**inputs)
    dossier = json.loads(inputs["dossier_bytes"])
    dossier["rows"][0]["source_metadata_excluding_vegdescription"]["latitude"] += 0.01
    changed = json_bytes(dossier)
    with pytest.raises(ValueError, match="pinned identity"):
        build_empd2_nfi_decision_projection(**{**inputs, "dossier_bytes": changed})
    rebound = build_empd2_nfi_decision_projection(
        **{
            **inputs,
            "dossier_bytes": changed,
            "dossier_sha256": sha256(changed).hexdigest(),
        }
    )
    assert rebound["projection_sha256"] != original["projection_sha256"]


@pytest.mark.parametrize("target", ["dossier", "spatial"])
@pytest.mark.parametrize(
    "field", ["BaPine", "VolPine", "MeanHeight", "StandAge", "NoStemsPine"]
)
def test_rebound_source_cannot_inject_outcome_fields(target: str, field: str) -> None:
    inputs = sources()
    key = f"{target}_bytes"
    sha_key = f"{target}_sha256"
    value = json.loads(inputs[key])
    value[field] = 12.5
    changed = json_bytes(value)
    with pytest.raises(ValueError, match="exact governed schemas"):
        build_empd2_nfi_decision_projection(
            **{**inputs, key: changed, sha_key: sha256(changed).hexdigest()}
        )


@pytest.mark.parametrize("target", ["dossier", "spatial"])
def test_source_reports_reject_duplicate_json_keys(target: str) -> None:
    inputs = sources()
    key = f"{target}_bytes"
    sha_key = f"{target}_sha256"
    content = inputs[key]
    duplicate = content.replace(b'{"', b'{"schema_version":"duplicate","', 1)
    with pytest.raises(ValueError, match="duplicate JSON key"):
        build_empd2_nfi_decision_projection(
            **{**inputs, key: duplicate, sha_key: sha256(duplicate).hexdigest()}
        )


def test_duplicate_spatial_lead_is_refused() -> None:
    inputs = sources()
    spatial = json.loads(inputs["spatial_bytes"])
    spatial["nearest_nfi_row_by_pollen_sample"][1]["pollen_sample"] = "sample-00"
    spatial_bytes = json_bytes(spatial)
    dossier = json.loads(inputs["dossier_bytes"])
    dossier["spatial_report_sha256"] = sha256(spatial_bytes).hexdigest()
    dossier_bytes = json_bytes(dossier)
    with pytest.raises(ValueError, match="16-lead denominator"):
        build_empd2_nfi_decision_projection(
            **{
                **inputs,
                "spatial_bytes": spatial_bytes,
                "spatial_sha256": sha256(spatial_bytes).hexdigest(),
                "dossier_bytes": dossier_bytes,
                "dossier_sha256": sha256(dossier_bytes).hexdigest(),
            }
        )


def test_promoted_spatial_lead_is_refused() -> None:
    inputs = sources()
    dossier = json.loads(inputs["dossier_bytes"])
    dossier["rows"][0]["independent_vegetation_pair_admission"] = True
    dossier_bytes = json_bytes(dossier)
    with pytest.raises(ValueError, match="lead identities differ"):
        build_empd2_nfi_decision_projection(
            **{
                **inputs,
                "dossier_bytes": dossier_bytes,
                "dossier_sha256": sha256(dossier_bytes).hexdigest(),
            }
        )


def test_nonmechanical_count_candidate_is_refused() -> None:
    inputs = sources()
    spatial = json.loads(inputs["spatial_bytes"])
    spatial["nearest_nfi_row_by_pollen_sample"][0]["mechanical_count_candidate"] = False
    spatial_bytes = json_bytes(spatial)
    dossier = json.loads(inputs["dossier_bytes"])
    dossier["rows"][-1]["spatial_lead"]["mechanical_count_candidate"] = False
    dossier["spatial_report_sha256"] = sha256(spatial_bytes).hexdigest()
    dossier_bytes = json_bytes(dossier)
    with pytest.raises(ValueError, match="lead identities differ"):
        build_empd2_nfi_decision_projection(
            **{
                **inputs,
                "spatial_bytes": spatial_bytes,
                "spatial_sha256": sha256(spatial_bytes).hexdigest(),
                "dossier_bytes": dossier_bytes,
                "dossier_sha256": sha256(dossier_bytes).hexdigest(),
            }
        )


@pytest.mark.parametrize("country", ["Norway", "SE", " Sweden "])
def test_source_country_must_be_exact_supported_sweden(country: str) -> None:
    inputs = sources()
    dossier = json.loads(inputs["dossier_bytes"])
    dossier["rows"][0]["source_metadata_excluding_vegdescription"]["country"] = country
    dossier_bytes = json_bytes(dossier)
    with pytest.raises(ValueError, match="country"):
        build_empd2_nfi_decision_projection(
            **{
                **inputs,
                "dossier_bytes": dossier_bytes,
                "dossier_sha256": sha256(dossier_bytes).hexdigest(),
            }
        )
