"""Block scheduling and outcome-free baseline preparation stay explicit."""

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import manifest_sha256
from bijux_pollenomics.analysis.lra_validation.experiments import (
    prepare_spatial_block_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    BLOCK_BASELINE_METHOD,
    SpatialBlockExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.fitted.admission import (
    admit_block_training,
    read_block_supports,
)
from bijux_pollenomics.analysis.lra_validation.experiments.fitted.blocks import (
    _failure,
    _predict_training_mean_target,
    _training_mean_model,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reconstruction import (
    FoldFits,
)
from bijux_pollenomics.analysis.lra_validation.splits import (
    grouped_block_holdouts,
    grouped_leave_one_out,
)

from .test_admission import block_payload


@pytest.mark.parametrize("workers", [0, -1, True, 1000000])
def test_block_worker_budget_precedes_backend_and_cache(
    tmp_path: Path, workers: int
) -> None:
    request = block_payload(tmp_path / "inputs")
    with pytest.raises(ValueError):
        prepare_spatial_block_predictions(
            request,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "product",
            workers=workers,
        )
    assert not (tmp_path / "product").exists() and not (tmp_path / "cache").exists()


def test_interrupt_receipt_preserves_actual_target_and_exception() -> None:
    row = _failure("block:a", "target", "group", KeyboardInterrupt(), True)
    assert row["record_id"] == "target" and row["group_id"] == "group"
    assert row["status"] == "not_run" and row["exception_type"] == "KeyboardInterrupt"


def training_mean_row_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    """Build one admitted baseline row without fitting or reading a target outcome."""
    spec = SpatialBlockExperimentSpec(block_payload(tmp_path))
    records = [site.record for site in spec.sites]
    groups = {
        record: outer.test_group_ids[0]
        for outer in grouped_leave_one_out(records)
        for record in outer.test_record_ids
    }
    fold = next(
        outer
        for outer in grouped_block_holdouts(records)
        if outer.fold_id == "block:block-1"
    )
    admission = admit_block_training(
        spec, fold, groups, read_block_supports(spec, tmp_path)
    )
    anchor = next(
        site
        for record in spec.regional_priority
        for site in spec.sites
        if site.record.record_id == record and record in admission.admitted_record_ids
    )
    predictors = tuple(
        site
        for site in spec.sites
        if site.record.record_id in admission.admitted_record_ids
        and site.record.record_id != anchor.record.record_id
    )
    compositions = {
        groups[site.record.record_id]: {
            "Alnus": 0.2 + index * 0.1,
            "Betula": 0.8 - index * 0.1,
        }
        for index, site in enumerate(predictors)
    }
    products: tuple[dict[str, object], ...] = tuple(
        {
            "record_id": site.record.record_id,
            "group_id": groups[site.record.record_id],
            "composition": compositions[groups[site.record.record_id]],
            "scientific_identity_sha256": site.raw.sha256,
        }
        for site in predictors
    )
    fits = FoldFits(
        anchor,
        predictors,
        compositions,
        (0.5, 0.5),
        products,
        {},
    )
    baseline_model = _training_mean_model(spec, fold, fits, admission)
    target = next(
        site for site in spec.sites if site.record.record_id == fold.test_record_ids[0]
    )

    def prepare(*args: object, **kwargs: object) -> tuple[Any, Any, Any, str]:
        assert args[1] == target

        def forward(**values: Any) -> SimpleNamespace:
            return SimpleNamespace(
                method_profile="disqover-0.9.14-homogeneous-local-forward",
                pollen_fraction=values["local_cover"],
            )

        geometry = json.loads((tmp_path / target.geometry.path).read_text())
        bounds = tuple(
            (ring["inner_m"], ring["outer_m"]) for ring in geometry["forward_rings"]
        )
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
            ring_bounds_m=bounds,
            regional_cutoff_m=bounds[-1][1],
        )
        return (
            SimpleNamespace(api=SimpleNamespace(forward_deposition=forward)),
            prepared,
            geometry,
            "test-bin",
        )

    monkeypatch.setattr(
        "bijux_pollenomics.analysis.lra_validation.experiments.fitted.training_mean."
        "prepare_target_forward",
        prepare,
    )
    row = _predict_training_mean_target(
        spec,
        target,
        fold,
        fits,
        admission,
        groups,
        baseline_model,
        input_root=tmp_path,
    )
    return row, fold.as_dict(), admission.as_dict(), manifest_sha256(baseline_model)


def test_training_mean_uses_only_admitted_reconstructions_and_has_own_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    row, outer, admission, model_sha256 = training_mean_row_fixture(
        tmp_path, monkeypatch
    )
    assert row["method"] == BLOCK_BASELINE_METHOD
    assert row["baseline_model_sha256"] == model_sha256
    assert "model_sha256" not in row and "fit_manifest" not in row
    assert row["vegetation_fraction"] == {
        "Alnus": pytest.approx(0.35),
        "Betula": pytest.approx(0.65),
    }
    model = row["baseline_model_manifest"]
    assert model["schema_version"] == "lra-spatial-block-training-mean.v1"
    assert model["training_admission"] == admission
    assert row["training_admission"] == admission
    excluded = set(outer["train_record_ids"]) - set(
        admission["admitted_training_record_ids"]
    )
    assert excluded.isdisjoint(model["allowed_input_closure"])
    assert set(outer["test_record_ids"]).isdisjoint(model["allowed_input_closure"])
    changed = deepcopy(model)
    changed["training_compositions"][next(iter(changed["training_compositions"]))] = {
        "Alnus": 0.1,
        "Betula": 0.9,
    }
    assert manifest_sha256(changed) != row["baseline_model_sha256"]
