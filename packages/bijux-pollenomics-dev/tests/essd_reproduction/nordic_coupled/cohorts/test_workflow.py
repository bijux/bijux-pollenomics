"""Controlled four-place routing and fold-atomic custody, without fitted models."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import workflow as shared
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.cohorts import (
    flink_nordic,
    workflow,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.sensitivity import encoded
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import digest

from .test_flink_nordic import fixture as input_fixture


@pytest.fixture
def cohort(tmp_path: Path) -> dict[str, Any]:
    nominal, projection, declaration = input_fixture(tmp_path)
    repository = tmp_path / "repository"
    repository.mkdir()
    nominal_pin = repository / "nominal-members.json"
    nominal_raw = encoded(
        [
            {"path": name, "sha256": digest(raw), "bytes": len(raw)}
            for name, raw in sorted(nominal.items())
        ]
    )
    nominal_pin.write_bytes(nominal_raw)
    declaration.update(
        nominal_manifest="nominal-members.json",
        input_pins=[
            {
                "path": "nominal-members.json",
                "sha256": digest(nominal_raw),
                "bytes": len(nominal_raw),
            }
        ],
    )
    protocol_path = repository / flink_nordic.PROTOCOL
    protocol_path.parent.mkdir(parents=True)
    protocol_raw = encoded(declaration)
    protocol_path.write_bytes(protocol_raw)
    buffers = flink_nordic.extend(nominal, projection, declaration)
    root = repository / "artifacts/cohort"
    for name, raw in buffers.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    manifest = repository / "artifacts/input-members.json"
    manifest_raw = encoded(
        [
            {"path": name, "sha256": digest(raw), "bytes": len(raw)}
            for name, raw in sorted(buffers.items())
        ]
    )
    manifest.write_bytes(manifest_raw)
    return {
        "root": root,
        "manifest": manifest,
        "checksum": digest(manifest_raw),
        "protocol": protocol_path,
        "protocol_sha256": digest(protocol_raw),
        "binding": {
            "path": str(protocol_path),
            "sha256": digest(protocol_raw),
            "bytes": len(protocol_raw),
        },
        "output": repository / "artifacts",
    }


def test_real117_reader_and_old80_boundary_remain_separate(
    cohort: dict[str, Any],
) -> None:
    rows, pins = workflow.input_scope(
        cohort["root"], cohort["manifest"], cohort["checksum"], cohort["binding"]
    )
    assert len(pins) == 117 and [r["directory"] for r in rows] == list(shared.NAMES)
    assert all(r["experiment"]["path"] == "cohort-experiment.json" for r in rows)
    with pytest.raises(ValueError, match="80-member"):
        shared.input_scope(cohort["root"], cohort["manifest"], cohort["checksum"])


@pytest.mark.parametrize(
    "change", ["extra", "missing", "wrong_protocol", "duplicate_inventory"]
)
def test_cohort_namespace_and_protocol_refusals(
    cohort: dict[str, Any], change: str
) -> None:
    checksum = cohort["checksum"]
    if change == "extra":
        (cohort["root"] / "foreign.json").write_text("{}")
    elif change == "missing":
        (cohort["root"] / shared.NAMES[0] / "FLINK-raw.json").unlink()
    elif change == "wrong_protocol":
        cohort["binding"]["sha256"] = "0" * 64
    else:
        pins = json.loads(cohort["manifest"].read_bytes())
        pins[-1] = pins[0]
        raw = encoded(pins)
        cohort["manifest"].write_bytes(raw)
        checksum = digest(raw)
    with pytest.raises((ValueError, FileNotFoundError)):
        workflow.input_scope(
            cohort["root"], cohort["manifest"], checksum, cohort["binding"]
        )


class Refusal(Exception):
    reason_code = "artificial_refusal"


def apis(events: list[str], *, not_run: bool = False) -> dict[str, Any]:
    def prepare(spec: dict[str, Any], **kwargs: Any) -> SimpleNamespace:
        assert len(spec["sites"]) == 4
        events.append("prepare")
        return SimpleNamespace(
            directory=kwargs["destination"], manifest_sha256="1" * 64
        )

    def reopen(directory: Path, **kwargs: Any) -> tuple[Any, ...]:
        events.append("reopen")
        folds: dict[str, dict[str, Any]] = {f"fold{i}": {} for i in range(4)}
        # Successful method rows may differ; failed folds remain atomic.
        predictions = {
            (fold, method): {"stored_value": method}
            for fold in ("fold0", "fold1")
            for method in shared.METHODS
        }
        failures = [
            {
                "fold_id": "fold2",
                "status": "refused",
                "reason_code": "invalid_composition",
            },
            {
                "fold_id": "fold3",
                "status": "not_run" if not_run else "refused",
                "reason_code": "experiment_interrupted"
                if not_run
                else "invalid_composition",
            },
        ]
        product = SimpleNamespace(
            directory=directory,
            manifest_sha256=kwargs["expected_manifest_sha256"],
            scientific_content_sha256="2" * 64,
        )
        manifest = {
            "files": dict.fromkeys(
                (
                    "training.json",
                    "preparations.json",
                    "operations.json",
                    "failures.json",
                    "predictions.json",
                ),
                "3" * 64,
            ),
            "scientific_payload": {"failures": failures, "interrupted": not_run},
        }
        return product, manifest, folds, predictions, shared.METHODS

    def score(directory: Path, **kwargs: Any) -> SimpleNamespace:
        assert events[-1] == "reopen"
        assert len(kwargs["outcome_inventory"]["records"]) == 4
        events.append("score")
        return SimpleNamespace(
            directory=kwargs["destination"],
            manifest_sha256="4" * 64,
            scientific_content_sha256="5" * 64,
        )

    def product(directory: Path, **kwargs: Any) -> tuple[None, dict[str, Any]]:
        return None, {
            "phase": "scores",
            "scientific_payload": {
                "prediction_manifest_sha256": "1" * 64,
                "scores": [{"score": {"status": "scored"}}] * 6
                + [{"score": {"status": "prediction_failed"}}] * 6,
            },
        }

    return {
        "spec": lambda payload: payload,
        "prepare": prepare,
        "reopen": reopen,
        "score": score,
        "product": product,
        "refusals": (Refusal,),
    }


def run(cohort: dict[str, Any], phase: str) -> dict[str, Any]:
    prior = cohort["output"] / "prepare/batch.json"
    return workflow.batch(
        cohort["root"],
        cohort["manifest"],
        cohort["checksum"],
        cohort["output"] / phase,
        phase=phase,
        execution_epoch="a" * 40,
        protocol_path=cohort["protocol"],
        protocol_sha256=cohort["protocol_sha256"],
        prediction_index=prior if phase == "score" else None,
        prediction_index_sha256=digest(prior.read_bytes())
        if phase == "score"
        else None,
    )


def test_shared_prepare_reopen_score_keeps72_dispositions_and_freeze(
    cohort: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    monkeypatch.setattr(shared, "apis", lambda: apis(events))
    prepared = run(cohort, "prepare")
    assert prepared["cohort"] == workflow.COHORT
    assert prepared["protocol_sha256"] == cohort["protocol_sha256"]
    assert prepared["all_bins_accounted"] is True and len(prepared["bins"]) == 6
    for row in prepared["bins"]:
        assert row["prediction"]["status_counts"] == {"predicted": 6, "refused": 6}
        assert len(row["prediction"]["method_dispositions"]) == 12
    assert "score" not in events
    events.clear()
    scored = run(cohort, "score")
    assert events[:6] == ["reopen"] * 6
    assert scored["prediction_index_sha256"] == digest(
        (cohort["output"] / "prepare/batch.json").read_bytes()
    )
    assert all(
        row["scoring"]["status_counts"] == {"scored": 6, "prediction_failed": 6}
        for row in scored["bins"]
    )


def test_unknown_failure_is_fatal_and_later_bins_unrun(
    cohort: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    api = apis([])

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("unrecognized")

    api["prepare"] = fail
    monkeypatch.setattr(shared, "apis", lambda: api)
    with pytest.raises(RuntimeError, match="unrecognized"):
        run(cohort, "prepare")
    ledger = json.loads((cohort["output"] / "prepare/batch.json").read_bytes())
    assert [row["status"] for row in ledger["bins"]] == ["fatal"] + ["not_run"] * 5
    assert "all_bins_accounted" not in ledger


def test_foreign_cohort_cannot_authorize_scores(
    cohort: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    monkeypatch.setattr(shared, "apis", lambda: apis(events))
    run(cohort, "prepare")
    path = cohort["output"] / "prepare/batch.json"
    prior = json.loads(path.read_bytes())
    prior["cohort"] = "foreign"
    path.write_bytes(encoded(prior))
    events.clear()
    with pytest.raises(ValueError, match="cohort"):
        run(cohort, "score")
    assert "score" not in events


def test_partial_method_success_is_not_promoted_to_a_complete_fold() -> None:
    api = apis([])
    original = api["reopen"]

    def partial(directory: Path, **kwargs: Any) -> tuple[Any, ...]:
        values: tuple[Any, ...] = original(directory, **kwargs)
        del values[3][("fold0", shared.METHODS[0])]
        return values

    api["reopen"] = partial
    with pytest.raises(ValueError, match="Twelve"):
        workflow.prediction_receipt(Path("/artificial"), "1" * 64, api)


def test_notrun_receipt_retains_interruption_without_a_completed_batch() -> None:
    receipt = workflow.prediction_receipt(
        Path("/artificial"), "1" * 64, apis([], not_run=True)
    )
    assert receipt["interrupted"] is True
    assert receipt["status_counts"] == {"predicted": 6, "refused": 3, "not_run": 3}
