"""Public experiment orchestration refuses invalid budgets before work starts."""

import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.experiments import (
    prepare_experiment_predictions,
    read_withheld_predictions,
    score_experiment_predictions,
)

from .test_inputs import fixture_inputs, source_fixture_inputs, store


def test_source_fixture_prepare_reopen_and_score(tmp_path: Path) -> None:
    """Exercise the source-posture route on constructed software inputs only."""
    inputs = tmp_path / "inputs"
    payload = source_fixture_inputs(inputs)
    product = prepare_experiment_predictions(
        payload,
        input_root=inputs,
        cache_root=tmp_path / "cache",
        destination=tmp_path / "prediction",
    )
    _, _, folds, predictions, methods = read_withheld_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    assert len(folds) == 4
    assert len(predictions) == 4 * len(methods)
    training = json.loads((product.directory / "training.json").read_text())
    assert all(
        row["outer_fold"]["test_record_ids"][0]
        not in {item["record_id"] for item in row["training_products"]}
        for row in training
    )
    for (fold_id, _), row in predictions.items():
        lineage = row["prediction_manifest"]["input_lineage"]
        regional = next(
            key for key in lineage if key.startswith("experiment-regional:")
        )
        assert set(lineage[regional]) == set(folds[fold_id]["train_record_ids"])
        assert not set(lineage[regional]) & set(folds[fold_id]["test_record_ids"])
    inventory = {
        "schema_version": "lra-source-pollen-outcomes.v1",
        "data_kind": "source_observations",
        "records": {site["record_id"]: site["raw"] for site in payload["sites"]},
    }
    scored = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=inputs,
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    scores = json.loads((scored.directory / "scores.json").read_text())
    assert len(scores) == len(predictions)
    assert all(row["score"]["status"] == "scored" for row in scores)
    target = payload["sites"][0]
    raw = json.loads((inputs / target["raw"]["path"]).read_text())
    raw["sample"]["counts"] = [100, 900]
    target["raw"] = store(inputs, target["raw"]["path"], raw)
    perturbed = prepare_experiment_predictions(
        payload,
        input_root=inputs,
        cache_root=tmp_path / "perturbed-cache",
        destination=tmp_path / "perturbed-prediction",
    )
    _, _, _, changed, _ = read_withheld_predictions(
        perturbed.directory, expected_manifest_sha256=perturbed.manifest_sha256
    )
    heldout_fold = next(
        fold_id
        for fold_id, fold in folds.items()
        if fold["test_record_ids"] == [target["record_id"]]
    )
    assert {key: row for key, row in predictions.items() if key[0] == heldout_fold} == {
        key: row for key, row in changed.items() if key[0] == heldout_fold
    }


@pytest.mark.parametrize("workers", [0, -1, True, 1_000_000])
def test_worker_budget_is_validated_before_work(tmp_path: Path, workers: int) -> None:
    payload = fixture_inputs(tmp_path / "inputs")
    with pytest.raises(ValueError):
        prepare_experiment_predictions(
            payload,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "prediction",
            workers=workers,
        )
    assert not (tmp_path / "prediction").exists()
    assert not (tmp_path / "cache").exists()


@pytest.mark.parametrize("source", ["raw", "geometry", "parameters"])
def test_consumed_source_mutation_is_refused_before_publication(
    tmp_path: Path, source: str
) -> None:
    from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
    from bijux_pollenomics.analysis.lra_validation.experiments import ExperimentSpec
    from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
        verify_consumed_sources,
    )

    payload = fixture_inputs(tmp_path)
    spec = ExperimentSpec(payload)
    path = tmp_path / (
        spec.sites[0].raw.path
        if source == "raw"
        else spec.sites[0].geometry.path
        if source == "geometry"
        else "parameters.json"
    )
    verify_consumed_sources(
        spec,
        tmp_path,
        pollen_record_ids={"p01"},
        geometry_record_ids={"p01", "p04"},
        template_used=True,
    )
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValidationRefusal):
        verify_consumed_sources(
            spec,
            tmp_path,
            pollen_record_ids={"p01"},
            geometry_record_ids={"p01", "p04"},
            template_used=True,
        )


def test_unconsumed_target_pollen_is_never_opened_by_final_source_check(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments import ExperimentSpec
    from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
        verify_consumed_sources,
    )

    spec = ExperimentSpec(fixture_inputs(tmp_path))
    (tmp_path / spec.sites[-1].raw.path).unlink()
    verify_consumed_sources(
        spec,
        tmp_path,
        pollen_record_ids={"p01"},
        geometry_record_ids={"p01", "p04"},
        template_used=True,
    )


def check_failed_source_revalidation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    operation: str,
    payload: dict[str, object],
    *,
    local: bool = False,
) -> None:
    """Real admitted reads survive an injected later computation failure."""
    import importlib
    from types import SimpleNamespace
    from typing import Any

    from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
    from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
        make_request,
    )

    module = importlib.import_module(module_name)
    monkeypatch.setattr(module, "load_engine", lambda: object())
    monkeypatch.setattr(
        module, "capture_code_identity", lambda _: SimpleNamespace(payload=dict)
    )
    monkeypatch.setattr(module, "verify_code_identity", lambda *args: None)
    monkeypatch.setattr(module, "_implementation", dict)
    calls = 0

    def failed(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 1:
            if local:
                make_request(*args, **kwargs)
                site = args[1]
            else:
                spec, fold = args[:2]
                admitted = [
                    site
                    for site in spec.sites
                    if site.record.record_id in fold.train_record_ids
                ]
                site = admitted[0]
                make_request(
                    spec,
                    site,
                    admitted[1],
                    fold,
                    kwargs["input_root"],
                    consumed_pollen=kwargs["consumed_pollen"],
                    consumed_geometry=kwargs["consumed_geometry"],
                )
            path = tmp_path / "inputs" / site.raw.path
            path.write_bytes(path.read_bytes() + b"\n")
        raise ValidationRefusal(
            "injected_after_admitted_source", "No fit result returned"
        )

    monkeypatch.setattr(module, "make_request" if local else "reconstruct_fold", failed)
    with pytest.raises(ValidationRefusal, match="frozen reference"):
        getattr(module, operation)(
            payload,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "product",
        )
    assert calls > 1 and not (tmp_path / "product").exists()


def test_failed_baseline_fold_rechecks_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    check_failed_source_revalidation(
        tmp_path,
        monkeypatch,
        "bijux_pollenomics.analysis.lra_validation.experiments.workflow",
        "prepare_experiment_predictions",
        fixture_inputs(tmp_path / "inputs"),
    )
