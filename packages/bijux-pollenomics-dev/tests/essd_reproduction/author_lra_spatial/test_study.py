"""Authenticate serialized prediction and selection boundaries before outcomes."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial import products, study
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.outcomes import (
    OutcomeReader,
)

from .test_evaluation import selection_fixture


def test_nominal_failure_preserves_all_rows_before_any_new_prediction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, archive = tmp_path / "repository", tmp_path / "archive"
    repository.mkdir()
    archive.mkdir()
    (repository / "artifacts").mkdir()
    protocol = tmp_path / "protocol.json"
    protocol.write_text(
        json.dumps({"scales_km": [20.0, 100.0], "limits": {"max_output_bytes": 65536}})
    )
    failure = {
        "passed": False,
        "failures": [
            {"context_id": f"context-{index}", "stage": "pollen"}
            for index in range(675)
        ],
    }
    monkeypatch.setattr(study, "code_state", lambda _: {})
    monkeypatch.setattr(study, "load_inputs", lambda *args: {})
    monkeypatch.setattr(study, "check_nominal", lambda _: failure)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("A failed nominal gate must stop before predictions/outcomes")

    monkeypatch.setattr(study, "predict_context", forbidden)
    monkeypatch.setattr(study, "OutcomeReader", forbidden)
    output = repository / "artifacts" / "spatial"
    with pytest.raises(ValueError, match="Nominal correspondence failed"):
        study.produce(repository, archive, protocol, output)
    assert json.loads((output / "nominal.json").read_bytes()) == failure
    assert [path.name for path in output.iterdir()] == ["nominal.json"]


def serialized_workflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, tamper: str | None = None
) -> tuple[Path, Path, Path, dict[str, Any]]:
    """Use actual product I/O, outcome reading, selection and scoring on tiny sources."""
    packet, candidates, source_reader = selection_fixture(tmp_path / "sources")
    packet["sources"] = []
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    protocol = tmp_path / "protocol.json"
    protocol.write_text(
        json.dumps(
            {
                "scales_km": [20.0, 100.0],
                "author_inputs": list(source_reader.geometries.values()),
                "limits": {
                    "producer_wall_seconds": 60,
                    "observer_wall_seconds": 60,
                    "max_rss_bytes": 512 * 1024**2,
                    "max_output_bytes": 8 * 1024**2,
                },
            }
        )
    )
    state = {"head": "0" * 40, "index_sha256": "1" * 64, "python_files": {}}
    monkeypatch.setattr(study, "code_state", lambda _: deepcopy(state))
    monkeypatch.setattr(study, "load_inputs", lambda *args: deepcopy(packet))
    monkeypatch.setattr(study, "check_sources", lambda *args: None)
    monkeypatch.setattr(study, "check_nominal", lambda _: {"passed": True})
    by_context = {
        (row["context_id"], row["length_scale_km"]): row for row in candidates
    }
    observed: dict[str, Any] = {
        "authenticated": {},
        "label_attempts": [],
        "labels": [],
        "prediction_calls": [],
        "events": [],
    }

    def predict(
        context: dict[str, Any], taxa: list[str], scale: float
    ) -> dict[str, Any]:
        assert taxa == packet["taxa"]
        assert observed["label_attempts"] == []
        observed["prediction_calls"].append((context["context_id"], scale))
        return deepcopy(by_context[(context["context_id"], scale)])

    monkeypatch.setattr(study, "predict_context", predict)

    def reopen(directory: Path, pin: dict[str, Any]) -> Any:
        value = products.reopen(directory, pin)
        observed["authenticated"][pin["path"]] = pin["sha256"]
        observed["events"].append(("authenticated", pin["path"]))
        return value

    monkeypatch.setattr(study, "reopen", reopen)
    original_read = OutcomeReader.read

    def read(
        self: OutcomeReader, record_id: str, *, outer_target: str, role: str
    ) -> dict[str, int]:
        observed["label_attempts"].append((role, record_id, outer_target))
        authenticated = observed["authenticated"]
        assert {
            "prediction-manifest.json",
            "inputs.json",
            "candidates.json",
            "nominal.json",
        } <= set(authenticated)
        assert self.prediction_freeze == authenticated["prediction-manifest.json"]
        assert len(observed["prediction_calls"]) == 450
        if role == "outer_scoring":
            assert {
                "selection-manifest.json",
                "choices.json",
                "inner-scores.json",
            } <= set(authenticated)
            assert self.selection_freeze == authenticated["selection-manifest.json"]
        result = original_read(self, record_id, outer_target=outer_target, role=role)
        observed["labels"].append((role, record_id, outer_target))
        observed["events"].append(("label", role))
        return result

    monkeypatch.setattr(OutcomeReader, "read", read)
    if tamper is not None:

        def write(
            directory: Path, name: str, value: Any, maximum: int
        ) -> dict[str, Any]:
            pin = products.write(directory, name, value, maximum)
            trigger = (
                "prediction-manifest.json"
                if tamper in {"candidates.json", "prediction-manifest.json"}
                else "selection-manifest.json"
            )
            if name == trigger:
                path = directory / tamper
                original = path.read_bytes()
                altered = json.loads(original)
                if tamper == "candidates.json":
                    altered[0]["pollen_fraction"] = [0.25, 0.75]
                elif tamper == "choices.json":
                    altered[0]["selected_scale_km"] = 100.0
                else:
                    altered["role"] += " altered"
                changed = (
                    json.dumps(altered, sort_keys=True, separators=(",", ":")).encode()
                    + b"\n"
                )
                assert changed != original
                path.write_bytes(changed)
            return pin

        monkeypatch.setattr(study, "write", write)
    return repository, source_reader.archive, protocol, observed


def test_serialized_predictions_and_choices_authenticate_before_dependent_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, archive, protocol, observed = serialized_workflow(tmp_path, monkeypatch)
    output = repository / "artifacts" / "spatial-workflow"
    result = study.produce(repository, archive, protocol, output)
    assert result["source_guards_passed"] is True
    assert len(observed["prediction_calls"]) == 450
    assert Counter(role for role, _, _ in observed["labels"]) == {
        "inner_training": 210,
        "outer_scoring": 15,
    }
    assert observed["labels"] == observed["label_attempts"]
    assert all(
        record != outer
        for role, record, outer in observed["labels"]
        if role == "inner_training"
    )
    first_inner = observed["events"].index(("label", "inner_training"))
    first_outer = observed["events"].index(("label", "outer_scoring"))
    for name in (
        "prediction-manifest.json",
        "inputs.json",
        "candidates.json",
        "nominal.json",
    ):
        assert observed["events"].index(("authenticated", name)) < first_inner
    for name in ("selection-manifest.json", "choices.json", "inner-scores.json"):
        assert (
            first_inner
            < observed["events"].index(("authenticated", name))
            < first_outer
        )
    closed = {
        name: products.reopen(output, pin) for name, pin in result["products"].items()
    }
    assert len(closed["inputs"]["contexts"]) == 225
    assert len(closed["candidates"]) == 450
    assert len(closed["inner_scores"]) == 420
    assert len(closed["choices"]) == len(closed["outer_scores"]) == 15
    assert all(
        row["status"] == "scored"
        and row["observed_count"] == 4
        and len(row["matched_baselines"]) == 3
        for row in closed["outer_scores"]
    )
    assert len(closed["outcome_access"]) == 225
    assert result["resources"]["output_bytes"] < 8 * 1024**2


@pytest.mark.parametrize(
    "tamper",
    [
        "candidates.json",
        "prediction-manifest.json",
        "choices.json",
        "selection-manifest.json",
    ],
)
def test_changed_closed_member_prevents_dependent_outcome_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    repository, archive, protocol, observed = serialized_workflow(
        tmp_path, monkeypatch, tamper=tamper
    )
    output = repository / "artifacts" / "spatial-workflow"
    with pytest.raises(ValueError, match="Serialized scientific member changed"):
        study.produce(repository, archive, protocol, output)
    assert len(observed["prediction_calls"]) == 450
    assert not (output / "result.json").exists()
    assert not (output / "outer-scores.json").exists()
    if tamper in {"candidates.json", "prediction-manifest.json"}:
        assert observed["label_attempts"] == observed["labels"] == []
    else:
        assert len(observed["labels"]) == 210
        assert {role for role, _, _ in observed["label_attempts"]} == {"inner_training"}
        assert all(role != "outer_scoring" for role, _, _ in observed["labels"])
