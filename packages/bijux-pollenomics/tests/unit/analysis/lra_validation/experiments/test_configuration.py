"""The first profile cannot silently admit final data or implicit assumptions."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments import ExperimentSpec
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    BLOCK_BASELINE_METHOD,
    BLOCK_METHODS,
    FITTED_METHOD,
    FITTED_METHODS,
    TRAINING_MEAN_METHOD,
    InputReference,
    SpatialBlockLocalPollenSpec,
)

from .test_inputs import fixture_inputs


def test_spatial_block_methods_have_one_ordered_fitted_baseline_pair() -> None:
    assert TRAINING_MEAN_METHOD == "training_mean"
    assert BLOCK_BASELINE_METHOD == TRAINING_MEAN_METHOD
    assert BLOCK_METHODS == (FITTED_METHOD, BLOCK_BASELINE_METHOD)
    assert FITTED_METHODS == (FITTED_METHOD, TRAINING_MEAN_METHOD)


@pytest.mark.parametrize(
    "field,value",
    [("purpose", "final"), ("data_kind", "observed"), ("operation", "love")],
)
def test_unsupported_request_posture(tmp_path: Path, field: str, value: str) -> None:
    payload = fixture_inputs(tmp_path)
    payload["request_template"][field] = value
    with pytest.raises(ValidationRefusal):
        ExperimentSpec(payload)


@pytest.mark.parametrize("path", ["../outside", "/outside", "a\\b", ""])
def test_reference_paths_cannot_escape(path: str) -> None:
    with pytest.raises(ValidationRefusal):
        InputReference.parse({"path": path, "sha256": "a" * 64}, "raw")


def test_template_and_sites_are_immutable_snapshots(tmp_path: Path) -> None:
    payload = fixture_inputs(tmp_path)
    spec = ExperimentSpec(payload)
    payload["request_template"]["taxa"] = ["mutated"]
    assert spec.template()["taxa"] == ["Alnus", "Betula"]
    assert spec.template() is not spec.template()


@pytest.mark.parametrize(
    "field,value",
    [
        ("local_ring_count", True),
        ("local_support_radius_m", 0),
        ("baselines", ["training_mean", "training_mean"]),
        ("regional_priority", ["missing"]),
        ("support_profile", "implicit"),
    ],
)
def test_invalid_declared_scope(tmp_path: Path, field: str, value: object) -> None:
    payload = fixture_inputs(tmp_path)
    payload[field] = value
    with pytest.raises(ValidationRefusal):
        ExperimentSpec(payload)


def test_block_local_profile_is_analytical_and_round_trips(tmp_path: Path) -> None:
    from .fitted.test_admission import block_local_payload

    payload = block_local_payload(tmp_path)
    spec = SpatialBlockLocalPollenSpec(payload)
    assert spec.request() == payload
    payload["method"] = "training_mean"
    with pytest.raises(ValidationRefusal, match="analytical"):
        SpatialBlockLocalPollenSpec(payload)
