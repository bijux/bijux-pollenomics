"""Controlled API boundaries keep all six predictions closed before any score."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    ValidationRefusal,
    grouped_leave_one_out,
)
from bijux_pollenomics.analysis.lra_validation.experiments import SourceExperimentSpec
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import workflow as shared
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.cohorts import (
    krageholm_regional as cohort,
)
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import digest
from tests.essd_reproduction.nordic_coupled.cohorts.test_krageholm_regional import stage


def fake_apis(
    monkeypatch: pytest.MonkeyPatch, *, refuse_bin: str | None = None
) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []
    specifications: dict[str, Any] = {}

    def prepare(spec: Any, **kwargs: Any) -> Any:
        name = kwargs["destination"].name
        specifications[name] = spec
        calls.append(("prepare", name))
        assert kwargs["workers"] == 1
        if name == refuse_bin:
            raise ValidationRefusal(
                "invalid_composition", "Synthetic signed negative retained"
            )
        kwargs["destination"].mkdir()
        return SimpleNamespace(
            directory=kwargs["destination"], manifest_sha256="d" * 64
        )

    def receipt(directory: Path, checksum: str, api: Any) -> dict[str, Any]:
        calls.append(("reopen", directory.name))
        spec = specifications[directory.name]
        folds = grouped_leave_one_out(
            [site.record for site in spec.sites],
            target_record_ids=spec.target_record_ids,
        )
        return {
            "directory": str(directory),
            "manifest_sha256": checksum,
            "scientific_content_sha256": "e" * 64,
            "failures": [],
            "method_dispositions": [
                {"fold_id": fold.fold_id, "method": method, "status": "predicted"}
                for fold in folds
                for method in cohort.METHODS
            ],
        }

    def score(directory: Path, **kwargs: Any) -> Any:
        assert len([call for call in calls if call[0] == "reopen"]) >= 12
        calls.append(("score", directory.name))
        spec = specifications[directory.name]
        assert set(kwargs["outcome_inventory"]["records"]) == set(
            spec.target_record_ids
        )
        assert not any(
            "23013" in record for record in kwargs["outcome_inventory"]["records"]
        )
        kwargs["destination"].mkdir()
        return SimpleNamespace(
            directory=kwargs["destination"],
            manifest_sha256="f" * 64,
            scientific_content_sha256="a" * 64,
        )

    def product(directory: Path, **kwargs: Any) -> Any:
        spec = specifications[directory.name]
        folds = grouped_leave_one_out(
            [site.record for site in spec.sites],
            target_record_ids=spec.target_record_ids,
        )
        scores = [
            {"fold_id": fold.fold_id, "baseline": method, "score": {"status": "scored"}}
            for fold in folds
            for method in cohort.METHODS
        ]
        return None, {
            "files": {"batches/fold-0000/receipt.json": "b" * 64},
            "scientific_payload": {"scores": scores},
        }

    monkeypatch.setattr(
        shared,
        "apis",
        lambda: {
            "spec": SourceExperimentSpec,
            "prepare": prepare,
            "score": score,
            "product": product,
            "refusals": (ValidationRefusal,),
        },
    )
    monkeypatch.setattr(shared, "prediction_receipt", receipt)
    return calls


def test_all_six_predictions_close_before_any_score_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    index, checksum, _ = stage(tmp_path, monkeypatch)
    calls = fake_apis(monkeypatch)
    original = cohort.pinned

    def guarded(repository: Path, pin: dict[str, Any], maximum: int = 4194304) -> Any:
        if pin["path"].endswith("-raw.json") or pin["path"].endswith(
            "/projection.json"
        ):
            assert len([call for call in calls if call[0] == "reopen"]) >= 12
        return original(repository, pin, maximum)

    monkeypatch.setattr(cohort, "pinned", guarded)
    prepared = cohort.run(
        tmp_path, index, checksum, tmp_path / "artifacts/prepare", operation="prepare"
    )
    assert (
        prepared["requested_folds"] == 18
        and len(prepared["method_dispositions"]) == 54
        and prepared["status_counts"] == {"predicted": 54}
    )
    prediction = tmp_path / "artifacts/prepare/batch.json"
    result = cohort.run(
        tmp_path,
        index,
        checksum,
        tmp_path / "artifacts/score",
        operation="score",
        prediction_index=prediction,
        prediction_sha256=digest(prediction.read_bytes()),
    )
    assert result["all_bins_accounted"] and result["status_counts"] == {"scored": 54}
    assert [call for call in calls if call[0] == "score"] == [
        ("score", name) for name in cohort.NAMES
    ]
    first_score = next(index for index, call in enumerate(calls) if call[0] == "score")
    assert [call for call in calls[:first_score] if call[0] == "reopen"][-6:] == [
        ("reopen", name) for name in cohort.NAMES
    ]


def test_prepare_never_opens_raw_or_projection_outside_native_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    index, checksum, _ = stage(tmp_path, monkeypatch)
    fake_apis(monkeypatch)
    original = cohort.pinned

    def forbid_quantitative(
        repository: Path, pin: dict[str, Any], maximum: int = 4194304
    ) -> Any:
        assert not pin["path"].endswith("-raw.json") and not pin["path"].endswith(
            "/projection.json"
        )
        return original(repository, pin, maximum)

    monkeypatch.setattr(cohort, "pinned", forbid_quantitative)
    result = cohort.run(
        tmp_path, index, checksum, tmp_path / "artifacts/prepare", operation="prepare"
    )
    assert len(result["method_dispositions"]) == 54


def test_refused_bin_keeps_all_nine_dispositions_without_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    index, checksum, _ = stage(tmp_path, monkeypatch)
    calls = fake_apis(monkeypatch, refuse_bin=cohort.NAMES[2])
    result = cohort.run(
        tmp_path, index, checksum, tmp_path / "artifacts/prepare", operation="prepare"
    )
    assert len(result["method_dispositions"]) == 54 and result["status_counts"] == {
        "predicted": 45,
        "refused": 9,
    }
    assert result["bins"][2]["reason_code"] == "invalid_composition"
    assert len([call for call in calls if call[0] == "prepare"]) == 6


def test_incomplete_prediction_batch_refused_before_score_or_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    index, checksum, _ = stage(tmp_path, monkeypatch)
    calls = fake_apis(monkeypatch)
    cohort.run(
        tmp_path, index, checksum, tmp_path / "artifacts/prepare", operation="prepare"
    )
    prediction = tmp_path / "artifacts/prepare/batch.json"
    prior = json.loads(prediction.read_bytes())
    prior["bins"].pop()
    prediction.write_text(json.dumps(prior))
    with pytest.raises(ValueError, match="complete prediction batch"):
        cohort.run(
            tmp_path,
            index,
            checksum,
            tmp_path / "artifacts/score",
            operation="score",
            prediction_index=prediction,
            prediction_sha256=digest(prediction.read_bytes()),
        )
    assert not (tmp_path / "artifacts/score").exists()
    assert not any(call[0] == "score" for call in calls)
