"""Outcome phases require a pinned prior prediction and the exact younger support."""

import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.temporal.persistence import scoring

from .support import fixture_payload, spec_from_payload


def test_final_scoring_refuses_before_prediction_or_outcome_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Final mode must refuse before inputs")

    monkeypatch.setattr(scoring, "read_temporal_persistence_predictions", forbidden)
    with pytest.raises(ValidationRefusal):
        scoring.score_temporal_persistence_predictions(
            tmp_path / "absent",
            expected_manifest_sha256="a" * 64,
            outcome_root=tmp_path / "labels",
            outcome_inventory={},
            destination=tmp_path / "out",
            purpose="final",
        )


@pytest.mark.parametrize(
    "field", ["sample_metadata", "geometry_sha256", "taxa", "purpose"]
)
def test_younger_observation_support_cannot_be_relabelled(
    tmp_path: Path, field: str
) -> None:
    spec = spec_from_payload(fixture_payload(tmp_path))
    site = spec.older_experiment.sites[-1]
    geometry = json.loads((tmp_path / site.geometry.path).read_text())
    observed = {
        "data_kind": "synthetic",
        "purpose": "exploratory",
        "record_id": site.record.record_id,
        "geometry_sha256": site.geometry.sha256,
        "sample_metadata": geometry["sample_metadata"],
        "taxa": spec.older_experiment.template()["taxa"],
        "vegetation_unit": "fraction",
        "vegetation_fraction": {"Alnus": 0.4, "Betula": 0.6},
        "pollen_unit": "count",
        "pollen_count": {"Alnus": 4, "Betula": 6},
    }
    scoring._observation(observed, spec, geometry)
    observed[field] = "relabelled"
    with pytest.raises(ValidationRefusal):
        scoring._observation(observed, spec, geometry)


def test_failed_prediction_preserves_both_targets_without_outcome_reads(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
        ExperimentProduct,
    )

    from .support import refused_product

    product, spec = refused_product(tmp_path / "generation")
    assert isinstance(product, ExperimentProduct)
    target = spec.temporal_plan.fold.test_record_ids[0]
    inventory = {
        "schema_version": "lra-temporal-outcomes.v1",
        "data_kind": "synthetic",
        "purpose": "exploratory",
        "predictions_manifest_sha256": product.manifest_sha256,
        "records": [
            {
                "record_id": target,
                "observation": {"path": "absent.json", "sha256": "c" * 64},
            }
        ],
    }
    result = scoring.score_temporal_persistence_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "absent",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    rows = json.loads((result.directory / "scores.json").read_text())
    assert len(rows) == 2
    assert {row["target"] for row in rows} == {"vegetation_cover", "pollen"}
    assert all(row["metrics"]["status"] == "failed_prediction" for row in rows)
    assert json.loads((result.directory / "outcome_access.json").read_text()) == []
