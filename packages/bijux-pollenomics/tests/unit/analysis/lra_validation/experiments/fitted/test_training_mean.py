"""Grouped training means retain reconstruction lineage without becoming fits."""

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.analysis.lra_validation import manifest_sha256
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FittedSpatialExperimentSpec,
    TRAINING_MEAN_METHOD,
)
from bijux_pollenomics.analysis.lra_validation.experiments.fitted.training_mean import (
    predict_training_mean_target,
    training_mean_model,
)

from .test_model import fitted_fixture, payload


def test_grouped_training_mean_has_own_fold_lineage_and_model_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, fold, fits, groups = fitted_fixture(tmp_path, monkeypatch)
    from bijux_pollenomics.analysis.lra_validation.experiments.fitted import model
    from bijux_pollenomics.analysis.lra_validation.experiments.fitted import (
        training_mean,
    )

    monkeypatch.setattr(
        training_mean, "prepare_target_forward", model.prepare_target_forward
    )
    baseline = cast(dict[str, Any], training_mean_model(spec, fold, fits, groups))
    row = cast(
        dict[str, Any],
        predict_training_mean_target(
            spec,
            spec.sites[-1],
            fold,
            fits,
            groups,
            baseline,
            input_root=tmp_path,
        ),
    )
    assert baseline["schema_version"] == "lra-grouped-outer-training-mean.v1"
    assert "training_admission" not in baseline and "training_admission" not in row
    assert baseline["method"] == row["method"] == TRAINING_MEAN_METHOD
    assert set(fold.train_record_ids).issubset(baseline["allowed_input_closure"])
    assert set(fold.test_record_ids).isdisjoint(baseline["allowed_input_closure"])
    assert row["vegetation_fraction"] == {
        "Alnus": pytest.approx(0.475),
        "Betula": pytest.approx(0.525),
    }
    assert row["baseline_model_sha256"] == manifest_sha256(baseline)
    assert "model_sha256" not in row and "fit_manifest" not in row

    changed_payload = payload(tmp_path)
    changed_payload["method"]["length_scale_km"] = 80
    changed_payload["method"]["ridge_penalty"] = 0.8
    changed_spec = FittedSpatialExperimentSpec(changed_payload)
    assert training_mean_model(changed_spec, fold, fits, groups) == baseline

    changed = deepcopy(baseline)
    changed["training_compositions"][next(iter(changed["training_compositions"]))] = {
        "Alnus": 0.1,
        "Betula": 0.9,
    }
    assert manifest_sha256(changed) != row["baseline_model_sha256"]
