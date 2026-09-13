"""Temporal retained intake refuses incompatible phase before model or outcome access."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
)
from bijux_pollenomics.analysis.lra_validation.temporal.persistence import reading


@pytest.mark.parametrize(
    "profile,phase",
    [
        ("synthetic-withheld-site-baselines-v1", "predictions"),
        ("synthetic-forward-time-persistence-v1", "scores"),
    ],
)
def test_wrong_profile_or_phase_stops_before_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, profile: str, phase: str
) -> None:
    product = ExperimentProduct(tmp_path, "a" * 64, "b" * 64)
    monkeypatch.setattr(
        reading,
        "read_experiment_product",
        lambda *args, **kwargs: (product, {"profile": profile, "phase": phase}),
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Wrong profile must not read retained scientific members")

    monkeypatch.setattr(reading, "read_member", forbidden)
    with pytest.raises(ValidationRefusal):
        reading.read_temporal_persistence_predictions(
            tmp_path, expected_manifest_sha256=product.manifest_sha256
        )


def test_actual_all_refused_product_remains_readable(tmp_path: Path) -> None:
    from .support import refused_product

    product, spec = refused_product(tmp_path)
    assert isinstance(product, ExperimentProduct)
    _, restored, science = reading.read_temporal_persistence_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    assert restored.sha256 == spec.sha256
    assert science["requested_predictions"] == 1
    assert science["generated_predictions"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("requested_predictions", 0),
        ("interrupted", True),
        ("uncertainty_status", "joint_validated"),
        ("temporal_decision", {}),
        ("consumed_pollen_record_ids", ["p04"]),
        ("consumed_geometry_record_ids", ["p04"]),
        ("older_regional_vegetation_fraction", [0.5, 0.5]),
    ],
)
def test_fully_rehashed_refusal_cannot_change_scope(
    tmp_path: Path, field: str, value: object
) -> None:
    import json

    from .support import refused_product, rehash_product

    product, _ = refused_product(tmp_path)
    assert isinstance(product, ExperimentProduct)
    scientific = json.loads((product.directory / "manifest.json").read_text())[
        "scientific_payload"
    ]
    scientific[field] = value
    digest = rehash_product(product.directory, scientific)
    with pytest.raises(ValidationRefusal):
        reading.read_temporal_persistence_predictions(
            product.directory, expected_manifest_sha256=digest
        )
