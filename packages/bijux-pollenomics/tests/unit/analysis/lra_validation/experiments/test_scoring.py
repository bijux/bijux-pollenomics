"""Outcome admission is separate, reproducible and denominator-preserving."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    ValidationRefusal,
    grouped_leave_one_out,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    ExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
    publish_phase,
    stage_directory,
    write_json,
)
from bijux_pollenomics.analysis.lra_validation.experiments.scoring import (
    read_withheld_predictions,
    score_experiment_predictions,
)

from .test_inputs import fixture_inputs, store


def prediction_product(root: Path) -> tuple[ExperimentProduct, dict[str, Any]]:
    spec = ExperimentSpec(fixture_inputs(root / "inputs"))
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    methods: list[Literal["training_mean", "nearest_site"]] = [
        "training_mean",
        "nearest_site",
    ]
    rows = []
    outcomes = {}
    for fold in folds:
        record = fold.test_record_ids[0]
        outcomes[record] = store(
            root / "inputs",
            record + "-outcome.json",
            {
                "schema_version": "lra-experiment-observation.v1",
                "data_kind": "synthetic",
                "record_id": record,
                "bin_id": "test-bin",
                "vegetation_unit": "fraction",
                "pollen_unit": "count",
                "vegetation_fraction": {"Alnus": 0.5, "Betula": 0.5},
                "pollen_count": {"Alnus": 6, "Betula": 4},
            },
        )
        from bijux_pollenomics.analysis.lra_validation.prediction import (
            ForwardInputs,
            predict_withheld_site,
        )

        context = ForwardInputs(
            ("Alnus", "Betula"),
            (0.0, 0.0),
            ((1.0, 1.0),),
            (1.0,),
            (1.0, 1.0),
            ("regional",),
            ("parameters",),
            ("geometry",),
            "time",
            "synthetic-test-forward",
            "test",
        )

        def forward(
            local_cover: tuple[float, ...],
            regional_deposition: tuple[float, ...],
            local_k: tuple[tuple[float, ...], ...],
            terrestrial_fraction: tuple[float, ...],
            ppe: tuple[float, ...],
        ) -> Any:
            return SimpleNamespace(
                pollen_fraction=(0.7, 0.3), method_profile="synthetic-test-forward"
            )

        for method in methods:
            predicted = predict_withheld_site(
                fold,
                fold.test_group_ids[0],
                {
                    group: {"Alnus": 0.6, "Betula": 0.4}
                    for group in fold.train_group_ids
                },
                context,
                forward,
                spatial_method=method,
                training_input_ids=fold.train_record_ids,
                dependency_graph={
                    **dict.fromkeys(fold.train_record_ids, ()),
                    "regional": fold.train_record_ids,
                    "parameters": (),
                    "geometry": (),
                    "time": (),
                },
                admitted_external_ids=("regional", "parameters", "geometry", "time"),
                distances_km=dict.fromkeys(fold.train_group_ids, 1.0),
            )
            rows.append(
                {
                    "fold_id": fold.fold_id,
                    "record_id": record,
                    "bin_id": "test-bin",
                    "baseline": method,
                    "vegetation_fraction": dict(predicted.vegetation_fraction),
                    "pollen_fraction": dict(predicted.pollen_fraction),
                    "prediction_manifest_sha256": predicted.prediction_manifest_sha256,
                    "prediction_manifest": json.loads(predicted.input_manifest_json),
                }
            )
    scientific: dict[str, object] = {
        "folds": [fold.as_dict() for fold in folds],
        "predictions": rows,
        "baselines": methods,
        "failures": [],
    }
    destination = root / "prediction"
    stage = stage_directory(destination)
    write_json(stage, "predictions.json", rows)
    return publish_phase(
        stage, destination, phase="predictions", scientific=scientific
    ), {
        "schema_version": "lra-experiment-outcomes.v1",
        "data_kind": "synthetic",
        "records": outcomes,
    }


def test_final_access_refused_before_any_paths_are_opened(tmp_path: Path) -> None:
    with pytest.raises(ValidationRefusal) as error:
        score_experiment_predictions(
            tmp_path / "absent",
            expected_manifest_sha256="bad",
            outcome_root=tmp_path / "absent",
            outcome_inventory={},
            destination=tmp_path / "result",
            purpose="final",
        )
    assert error.value.reason_code == "final_experiment_not_implemented"
    assert list(tmp_path.iterdir()) == []


def test_target_scores_keep_denominators_and_raw_recomputation_inputs(
    tmp_path: Path,
) -> None:
    product, inventory = prediction_product(tmp_path)
    inventory["records"].pop("p01")
    scored = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "inputs",
        outcome_inventory=inventory,
        destination=tmp_path / "score",
    )
    summaries = json.loads((scored.directory / "summaries.json").read_text())
    assert len(summaries) == 4
    for summary in summaries:
        assert summary["requested"] == 4
        assert summary["by_status"] == {"missing_observation": 1, "scored": 3}
        assert summary["mean_mae_fraction"] == pytest.approx(0.1)
        assert summary["interval_coverage"] is None
    scores = json.loads((scored.directory / "scores.json").read_text())
    assert len(scores) == 16
    assert len([row for row in scores if "observation" in row]) == 12
    assert all("prediction" in row for row in scores)
    paired = json.loads(
        (scored.directory / "paired_baseline_differences.json").read_text()
    )
    assert len(paired) == 6
    assert all(row["mae_improvement_fraction"] == 0 for row in paired)


def test_tampered_prediction_refused_before_missing_outcome_read(
    tmp_path: Path,
) -> None:
    product, inventory = prediction_product(tmp_path)
    (product.directory / "predictions.json").write_text("[]")
    with pytest.raises(ValidationRefusal) as error:
        score_experiment_predictions(
            product.directory,
            expected_manifest_sha256=product.manifest_sha256,
            outcome_root=tmp_path / "absent",
            outcome_inventory=inventory,
            destination=tmp_path / "score",
        )
    assert error.value.reason_code == "invalid_experiment_product"


def test_bad_outcome_hash_is_counted_without_dropping_other_units(
    tmp_path: Path,
) -> None:
    product, inventory = prediction_product(tmp_path)
    (tmp_path / "inputs" / inventory["records"]["p01"]["path"]).write_text("changed")
    scored = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "inputs",
        outcome_inventory=inventory,
        destination=tmp_path / "score",
    )
    summaries = json.loads((scored.directory / "summaries.json").read_text())
    assert all(
        row["by_status"] == {"observation_refused": 1, "scored": 3} for row in summaries
    )
    accesses = json.loads((scored.directory / "outcome_access.json").read_text())
    assert len(accesses) == 4
    assert all(
        row["prediction_manifest_sha256"] == product.manifest_sha256 for row in accesses
    )


def test_prediction_failure_preserves_all_requested_target_denominators(
    tmp_path: Path,
) -> None:
    product, inventory = prediction_product(tmp_path)
    manifest = json.loads((product.directory / "manifest.json").read_text())
    scientific = manifest["scientific_payload"]
    failed = scientific["folds"][0]["fold_id"]
    scientific["predictions"] = [
        row for row in scientific["predictions"] if row["fold_id"] != failed
    ]
    scientific["failures"] = [{"fold_id": failed, "reason_code": "source_refused"}]
    destination = tmp_path / "refused-prediction"
    stage = stage_directory(destination)
    write_json(stage, "predictions.json", scientific["predictions"])
    product = publish_phase(
        stage, destination, phase="predictions", scientific=scientific
    )
    scored = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "inputs",
        outcome_inventory=inventory,
        destination=tmp_path / "score",
    )
    summaries = json.loads((scored.directory / "summaries.json").read_text())
    assert all(
        row["by_status"] == {"prediction_failed": 1, "scored": 3}
        and row["requested"] == 4
        for row in summaries
    )


def test_shared_withheld_reader_returns_owned_copies_and_authenticates_parent(
    tmp_path: Path,
) -> None:
    product, _ = prediction_product(tmp_path)
    opened = read_withheld_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    first = next(iter(opened[3]))
    opened[3][first]["pollen_fraction"] = {"Alnus": 1, "Betula": 0}
    assert (
        read_withheld_predictions(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        )[3][first]["pollen_fraction"]
        != opened[3][first]["pollen_fraction"]
    )
    with pytest.raises(ValidationRefusal):
        read_withheld_predictions(product.directory, expected_manifest_sha256="a" * 64)


def test_shared_withheld_reader_refuses_observed_local_pollen(tmp_path: Path) -> None:
    from .test_assimilation import synthetic_local_product

    product, _ = synthetic_local_product(tmp_path)
    with pytest.raises(ValidationRefusal) as error:
        read_withheld_predictions(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        )
    assert error.value.reason_code == "experiment_outcome_profile_mismatch"


@pytest.mark.parametrize(
    "methods", [["training_mean", "training_mean"], ["invented_method"], []]
)
def test_invalid_baseline_inventory_refuses_even_when_all_folds_failed(
    tmp_path: Path, methods: list[str]
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments.reading import (
        _predictions,
    )

    product, _ = prediction_product(tmp_path)
    manifest = json.loads((product.directory / "manifest.json").read_text())
    scientific = manifest["scientific_payload"]
    scientific["baselines"] = methods
    scientific["predictions"] = []
    scientific["failures"] = [
        {"fold_id": fold["fold_id"]} for fold in scientific["folds"]
    ]
    with pytest.raises(ValidationRefusal) as error:
        _predictions(manifest, [])
    assert error.value.reason_code == "invalid_prediction_methods"
