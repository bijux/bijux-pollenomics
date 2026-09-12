"""Fitted spatial methods retain actual source identity and both target holdouts."""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    ValidationRefusal,
    grouped_leave_one_out,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.experiments import (
    ExperimentSpec,
    FittedSpatialExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FITTED_METHOD,
    FITTED_PROFILE,
)
from bijux_pollenomics.analysis.lra_validation.experiments.fitted import (
    predict_fitted_fold,
    validate_fitted_prediction,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reconstruction import (
    FoldFits,
)

from .test_inputs import fixture_inputs


def payload(root: Path) -> dict[str, Any]:
    value = fixture_inputs(root)
    value.pop("baselines")
    value.update(
        profile=FITTED_PROFILE,
        method={"profile": FITTED_METHOD, "length_scale_km": 20, "ridge_penalty": 0.2},
    )
    return value


@pytest.mark.parametrize("value", [0, -1, True, "20", float("inf")])
def test_fixed_model_configuration_refuses_nonpositive_or_untyped_parameters(
    tmp_path: Path, value: object
) -> None:
    row = payload(tmp_path)
    row["method"]["length_scale_km"] = value
    with pytest.raises(ValidationRefusal):
        FittedSpatialExperimentSpec(row)


def test_fitted_configuration_is_distinct_from_baselines(tmp_path: Path) -> None:
    row = payload(tmp_path)
    spec = FittedSpatialExperimentSpec(row)
    assert not hasattr(spec, "baselines")
    with pytest.raises(ValidationRefusal):
        ExperimentSpec(row)
    row["method"]["support_id"] = "unrelated"
    with pytest.raises(ValidationRefusal):
        FittedSpatialExperimentSpec(row)


def fitted_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[FittedSpatialExperimentSpec, Any, FoldFits, dict[str, str]]:
    spec = FittedSpatialExperimentSpec(payload(tmp_path))
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    fold = next(f for f in folds if f.test_record_ids == ("p04",))
    groups = {r: f.test_group_ids[0] for f in folds for r in f.test_record_ids}
    anchor, *predictors = spec.sites[:3]
    compositions = {
        groups["p02"]: {"Alnus": 0.25, "Betula": 0.75},
        groups["p03"]: {"Alnus": 0.7, "Betula": 0.3},
    }
    fits = FoldFits(
        anchor,
        tuple(predictors),
        compositions,
        (0.5, 0.5),
        tuple(
            {
                "record_id": site.record.record_id,
                "group_id": groups[site.record.record_id],
                "composition": compositions[groups[site.record.record_id]],
                "scientific_identity_sha256": site.raw.sha256,
            }
            for site in predictors
        ),
        {},
    )

    def prepare(*args: object, **kwargs: object) -> tuple[Any, Any, Any, str]:
        target = args[1]
        assert target == spec.sites[-1]

        def forward(**values: Any) -> SimpleNamespace:
            return SimpleNamespace(
                method_profile="disqover-0.9.14-homogeneous-local-forward",
                pollen_fraction=values["local_cover"],
            )

        binding = SimpleNamespace(api=SimpleNamespace(forward_deposition=forward))
        prepared = SimpleNamespace(
            taxa=("Alnus", "Betula"),
            method_profile="disqover-0.9.14-homogeneous-local-forward",
            preparation_profile="disqover-0.9.14-corrected-matrix-homogeneous-v1",
            geometry_profile="circular-shore-contiguous-v1",
            deposition_units="relative-kernel-mass",
            local_k=((1.0, 2.0), (1.0, 2.0)),
            terrestrial_fraction=(1.0, 1.0),
            ppe=(1.0, 1.0),
            regional_deposition=(0.5, 0.5),
            regional_cover=(0.5, 0.5),
            ring_bounds_m=((20.0, 1000.0),),
            regional_cutoff_m=1000.0,
        )
        geometry = json.loads((tmp_path / spec.sites[-1].geometry.path).read_text())
        prepared.ring_bounds_m = tuple(
            (ring["inner_m"], ring["outer_m"]) for ring in geometry["forward_rings"]
        )
        prepared.regional_cutoff_m = prepared.ring_bounds_m[-1][1]
        return binding, prepared, geometry, "test-bin"

    monkeypatch.setattr(
        "bijux_pollenomics.analysis.lra_validation.experiments.fitted.prepare_target_forward",
        prepare,
    )
    return spec, fold, fits, groups


def test_actual_fitted_model_keeps_regional_ancestry_and_changes_identity_for_new_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, fold, fits, groups = fitted_fixture(tmp_path, monkeypatch)
    row, _ = predict_fitted_fold(
        spec, fold, spec.sites[-1], fits, groups, input_root=tmp_path
    )
    encoded = json.loads(json.dumps(row))
    validate_fitted_prediction(encoded, json.loads(json.dumps(fold.as_dict())))
    assert row["method_kind"] == "fitted_spatial" and "baseline" not in row
    fit = encoded["fit_manifest"]
    assert set(fold.train_record_ids).issubset(fit["allowed_input_closure"])
    assert "p04" not in fit["allowed_input_closure"]
    assert groups["p01"] not in fit["predictor_group_ids"]
    changed = deepcopy(fits.fit_identities)
    changed[0]["scientific_identity_sha256"] = "a" * 64
    other, _ = predict_fitted_fold(
        spec,
        fold,
        spec.sites[-1],
        replace(fits, fit_identities=changed),
        groups,
        input_root=tmp_path,
    )
    assert other["vegetation_fraction"] == row["vegetation_fraction"]
    assert other["model_sha256"] != row["model_sha256"]


@pytest.mark.parametrize(
    "mutation",
    [
        "role",
        "cover",
        "ancestry",
        "support",
        "heldout_predictor",
        "composition",
        "anchor_group",
        "regional_source",
        "empty_kernel",
        "posture",
    ],
)
def test_changed_fitted_envelope_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    spec, fold, fits, groups = fitted_fixture(tmp_path, monkeypatch)
    row, _ = predict_fitted_fold(
        spec, fold, spec.sites[-1], fits, groups, input_root=tmp_path
    )
    value = json.loads(json.dumps(row))
    if mutation == "role":
        value["evaluation_roles"]["pollen_composition"] = "in_sample_diagnostic"
    elif mutation == "cover":
        value["vegetation_fraction"] = {"Alnus": 0.4, "Betula": 0.6}
    elif mutation == "ancestry":
        node = next(
            key
            for key in value["training_dependency_graph"]
            if key.startswith("experiment-fit:")
        )
        value["training_dependency_graph"][node] = ["p04"]
    elif mutation == "support":
        value["support"]["local_support_radius_m"] = 999
    elif mutation == "heldout_predictor":
        value["fit_manifest"]["predictor_group_ids"][0] = fold.test_group_ids[0]
    elif mutation == "composition":
        first = next(iter(value["fit_manifest"]["training_compositions"]))
        value["fit_manifest"]["training_compositions"][first] = {
            "Alnus": 0.1,
            "Betula": 0.9,
        }
    elif mutation == "anchor_group":
        value["regional_anchor_group_id"] = fold.test_group_ids[0]
    elif mutation == "regional_source":
        value["regional_value_source_record_ids"] = [fold.test_record_ids[0]]
    elif mutation == "empty_kernel":
        value["forward_preparation"]["local_k"] = []
    else:
        value["scientific_acceptance"] = "accepted"
    if mutation in {"heldout_predictor", "composition"}:
        value["model_sha256"] = manifest_sha256(value["fit_manifest"])
        value["spatial_prediction_manifest"]["model_sha256"] = value["model_sha256"]
        value["spatial_prediction_sha256"] = manifest_sha256(
            value["spatial_prediction_manifest"]
        )
    value["prediction_manifest_sha256"] = manifest_sha256(
        {k: v for k, v in value.items() if k != "prediction_manifest_sha256"}
    )
    with pytest.raises(ValidationRefusal):
        validate_fitted_prediction(value, json.loads(json.dumps(fold.as_dict())))


def test_zero_training_fraction_is_refused_without_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, fold, fits, groups = fitted_fixture(tmp_path, monkeypatch)
    compositions = deepcopy(fits.compositions)
    compositions[groups["p02"]] = {"Alnus": 0.0, "Betula": 1.0}
    with pytest.raises(ValidationRefusal):
        predict_fitted_fold(
            spec,
            fold,
            spec.sites[-1],
            replace(fits, compositions=compositions),
            groups,
            input_root=tmp_path,
        )
