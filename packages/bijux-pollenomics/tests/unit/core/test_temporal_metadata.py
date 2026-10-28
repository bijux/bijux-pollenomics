"""Source chronology assertions survive shared temporal payload transport."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from bijux_pollenomics.core.temporal_semantics import (
    TemporalSemantics,
    build_temporal_semantics,
    normalize_temporal_semantics_payload,
    temporal_semantics_has_numeric_interval,
)


def _semantics() -> TemporalSemantics:
    return build_temporal_semantics(
        source_family="source",
        evidence_class="direct",
        precision_posture="source_interval",
        comparability_posture="numeric_interval",
        time_start_bp=0,
        time_end_bp=10,
    )


def test_absent_metadata_preserves_existing_payload_keys_and_bytes() -> None:
    payload = _semantics().as_dict()
    assert len(payload) == 20
    assert (
        not {"reference_epoch", "age_type", "calibration_status", "model", "method"}
        & payload.keys()
    )
    assert normalize_temporal_semantics_payload(payload) == payload


def test_explicit_metadata_unknowns_and_source_extensions_roundtrip_without_aliasing() -> (
    None
):
    metadata: dict[str, object] = {
        "reference_epoch": None,
        "age_type": "radiocarbon_bp",
        "calibration_status": "uncalibrated",
        "model": {"name": "source model", "version": None},
        "method": ["source method", None],
        "source_record_ids": ["Native:01", "Native:02"],
        "source_record_count": 2,
        "claim_bundle_path": "evidence/source.json",
        "chronology_claim_ids": ["claim-01"],
    }
    semantics = replace(_semantics(), source_metadata=metadata)
    payload = semantics.as_dict()
    assert {key: payload[key] for key in metadata} == metadata
    normalized = normalize_temporal_semantics_payload(payload)
    assert normalized == payload
    cast(list[str], normalized["source_record_ids"]).append("mutation")
    assert metadata["source_record_ids"] == ["Native:01", "Native:02"]
    cast(dict[str, object], payload["model"])["version"] = "mutation"
    assert metadata["model"] == {"name": "source model", "version": None}


def test_builder_accepts_explicit_source_metadata_without_inferring_unknowns() -> None:
    payload = build_temporal_semantics(
        source_family="source",
        evidence_class="contextual",
        precision_posture="period_label",
        comparability_posture="contextual_label_only",
        time_start_bp=None,
        time_end_bp=None,
        source_metadata={"reference_epoch": None, "method": "source-defined period"},
    ).as_dict()
    assert payload["reference_epoch"] is None
    assert payload["method"] == "source-defined period"
    assert "calibration_status" not in payload
    assert not temporal_semantics_has_numeric_interval(payload)


@pytest.mark.parametrize(
    "metadata",
    [
        {"time_start_bp": 0},
        {"schema_version": "other"},
        {"comparability_posture": "numeric_interval"},
        {"model": float("nan")},
        {"model": float("inf")},
        {"method": object()},
        {"model": {1: "invalid key"}},
    ],
)
def test_metadata_cannot_override_core_or_introduce_non_json_values(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="Source metadata"):
        replace(_semantics(), source_metadata=metadata).as_dict()


def test_cyclic_source_metadata_is_rejected_explicitly() -> None:
    cycle: list[object] = []
    cycle.append(cycle)
    with pytest.raises(ValueError, match="cycles"):
        replace(_semantics(), source_metadata={"model": cycle}).as_dict()


@pytest.mark.parametrize("version", ["temporal-semantics.v9", None, 3, False])
def test_unsupported_schema_is_retained_and_refused(version: object) -> None:
    payload = _semantics().as_dict()
    payload.update(
        schema_version=version, reference_epoch=None, source_record_ids=["Native:01"]
    )
    result = normalize_temporal_semantics_payload(payload)
    assert result["schema_version"] == version
    assert result["refusal_reason_code"] == "unsupported_temporal_semantics_schema"
    assert result["comparability_posture"] == "refused"
    assert result["time_start_bp"] is None and result["time_mean_bp"] is None
    assert result["reference_epoch"] is None
    assert result["source_record_ids"] == ["Native:01"]
    assert not temporal_semantics_has_numeric_interval(result)


def test_schema_less_legacy_input_remains_supported() -> None:
    source = _semantics().as_dict()
    del source["schema_version"]
    assert normalize_temporal_semantics_payload(source) == _semantics().as_dict()


@pytest.mark.parametrize(
    "change",
    [
        {"refusal_reason_code": "source_refusal"},
        {"comparability_posture": "contextual_label_only"},
        {"time_start_bp": "0"},
        {"time_start_bp": 0.25},
        {"time_start_bp": True},
        {"schema_version": "other"},
    ],
)
def test_raw_numeric_presence_does_not_override_refusal_or_invalid_projection(
    change: dict[str, object],
) -> None:
    payload = _semantics().as_dict()
    payload.update(change)
    assert not temporal_semantics_has_numeric_interval(payload)


@pytest.mark.parametrize(
    "mean", [0.25, 2**53, 10**1000, float("inf"), float("nan"), True, "0"]
)
def test_invalid_explicit_mean_cannot_bypass_the_shared_numeric_predicate(
    mean: object,
) -> None:
    payload = _semantics().as_dict()
    payload["time_mean_bp"] = mean
    assert not temporal_semantics_has_numeric_interval(payload)
    assert not temporal_semantics_has_numeric_interval(
        normalize_temporal_semantics_payload(payload)
    )


def test_outside_mean_is_discarded_without_erasing_valid_source_interval() -> None:
    payload = _semantics().as_dict()
    payload["time_mean_bp"] = 100
    normalized = normalize_temporal_semantics_payload(payload)
    assert normalized["time_mean_bp"] is None
    assert temporal_semantics_has_numeric_interval(payload)
    assert temporal_semantics_has_numeric_interval(normalized)
