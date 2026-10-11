"""Bind original Sämbosjön scoring to its retained freeze and source route."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.source_completion.nordic import (
    sambosjon_execution as execution,
)
from bijux_pollenomics_dev.source_completion.nordic import sambosjon_scores as scores


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prediction_payload() -> dict[str, object]:
    rows = [
        {
            "site_id": execution.SITE,
            "bin_id": bin_id,
            "method": method,
            "training_site_ids": ["other-site"],
        }
        for bin_id in range(1, 23)
        for method in execution.METHODS
    ]
    return {"predictions": rows, "refusals": []}


def fixture_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    source = repository / execution.SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("# fake original source\n")
    protocol_path = repository / execution.PROTOCOL
    protocol_path.parent.mkdir(parents=True)
    protocol_path.write_text(
        json.dumps(
            {
                "target_site_id": execution.SITE,
                "methods": list(execution.METHODS),
                "pre_score_predictions_sha256": hashlib.sha256(
                    json.dumps(prediction_payload()).encode()
                ).hexdigest(),
            }
        )
    )
    prepared = repository / execution.PREPARED
    prepared.mkdir()
    training = prepared / "training.json.gz"
    metadata = prepared / "metadata.json"
    training.write_bytes(b"fixture training")
    metadata.write_text(
        json.dumps(
            {
                "sites": [
                    {
                        "site_id": execution.SITE,
                        "candidate_bin_ids": [str(bin_id) for bin_id in range(1, 23)],
                    }
                ]
            }
        )
    )
    (prepared / "input-manifest.json").write_text(
        json.dumps(
            {
                "protocol_sha256": sha(protocol_path),
                "training_sha256": sha(training),
                "metadata_sha256": sha(metadata),
                "target_observation_profile_in_prepared_inputs": False,
                "training_physical_sites": 84,
                "target_samples": 111,
                "target_candidate_bins": 22,
            }
        )
    )
    return repository


def bind_origin(monkeypatch: pytest.MonkeyPatch, repository: Path) -> None:
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(repository / execution.SOURCE)),
    )


def fake_complete_stage(repository: Path, stage: Path) -> None:
    stage.mkdir()
    prepared = repository / execution.PREPARED
    protocol_path = repository / execution.PROTOCOL
    prediction_path = stage / "predictions.json"
    prediction_path.write_text(json.dumps(prediction_payload()))
    manifest_path = prepared / "input-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    (stage / "freeze.json").write_text(
        json.dumps(
            {
                "schema_version": "sambosjon-direct-pollen-freeze.v1",
                "created_at_utc": datetime.now(UTC).isoformat(),
                "protocol_sha256": sha(protocol_path),
                "input_manifest_sha256": sha(manifest_path),
                "training_sha256": manifest["training_sha256"],
                "metadata_sha256": manifest["metadata_sha256"],
                "predictions_sha256": sha(prediction_path),
                "target_observations_used_for_prediction": False,
                "target_site_id": execution.SITE,
                "prediction_rows": 66,
                "refused_bins": 0,
            }
        )
    )


def scoring_repository(tmp_path: Path) -> Path:
    repository = fixture_repository(tmp_path)
    fake_complete_stage(repository, repository / scores.FROZEN)
    return repository


def test_original_score_route_preserves_historical_freeze(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = scoring_repository(tmp_path)
    bind_origin(monkeypatch, repository)
    output = repository / "artifacts/score-products"
    frozen = repository / scores.FROZEN
    original_sha = sha(frozen / "freeze.json")
    calls: list[list[str]] = []

    def source(module: str, *, run_name: str) -> None:
        assert module.endswith("sambosjon_direct_pollen") and run_name == "__main__"
        calls.append(list(sys.argv))
        output.mkdir()
        (output / "scores.csv").write_text("fixture score output")

    monkeypatch.setattr(runpy, "run_module", source)
    original_argv = sys.argv
    assert scores.main(["--repository", str(repository), "--output", str(output)]) == 0
    assert sys.argv is original_argv
    assert calls == [
        [
            str(repository / execution.SOURCE),
            "score",
            "--repository",
            str(repository),
            "--prepared",
            str(repository / execution.PREPARED),
            "--frozen",
            str(frozen),
            "--freeze-sha256",
            original_sha,
            "--output",
            str(output),
        ]
    ]
    assert sha(frozen / "freeze.json") == original_sha
    assert (output / "scores.csv").read_text() == "fixture score output"


@pytest.mark.parametrize(
    "mode",
    ("target_read", "changed_training", "extra_frozen_file", "changed_prediction"),
)
def test_refuses_changed_score_freeze_before_source_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    repository = scoring_repository(tmp_path)
    frozen = repository / scores.FROZEN
    if mode == "target_read":
        path = frozen / "freeze.json"
        payload = json.loads(path.read_bytes())
        payload["target_observations_used_for_prediction"] = True
        path.write_text(json.dumps(payload))
    elif mode == "changed_training":
        (repository / execution.PREPARED / "training.json.gz").write_bytes(b"changed")
    elif mode == "extra_frozen_file":
        (frozen / "unexpected.json").write_text("{}")
    else:
        (frozen / "predictions.json").write_text("{}")
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("counts source entered")
    )
    with pytest.raises(ValueError):
        scores.run(repository, repository / "artifacts/score-products")


def test_source_failure_restores_argv_without_replacing_freeze(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = scoring_repository(tmp_path)
    bind_origin(monkeypatch, repository)
    frozen = repository / scores.FROZEN / "freeze.json"
    original_sha = sha(frozen)
    original_argv = sys.argv

    def refusal(module: str, *, run_name: str) -> None:
        raise RuntimeError("original scorer refused")

    monkeypatch.setattr(runpy, "run_module", refusal)
    with pytest.raises(RuntimeError, match="original scorer refused"):
        scores.run(repository, repository / "artifacts/score-products")
    assert sys.argv is original_argv and sha(frozen) == original_sha


def test_score_refuses_foreign_original_source_origin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = scoring_repository(tmp_path)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(repository / "foreign.py")),
    )
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("foreign source entered")
    )
    with pytest.raises(ValueError, match="origin differs"):
        scores.run(repository, repository / "artifacts/score-products")


def test_score_refuses_duplicate_bin_before_target_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = scoring_repository(tmp_path)
    frozen = repository / scores.FROZEN
    prediction_path = frozen / "predictions.json"
    predictions = json.loads(prediction_path.read_bytes())
    predictions["predictions"][3]["bin_id"] = 1
    prediction_path.write_text(json.dumps(predictions))
    protocol_path = repository / execution.PROTOCOL
    protocol = json.loads(protocol_path.read_bytes())
    protocol["pre_score_predictions_sha256"] = sha(prediction_path)
    protocol_path.write_text(json.dumps(protocol))
    manifest_path = repository / execution.PREPARED / "input-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["protocol_sha256"] = sha(protocol_path)
    manifest_path.write_text(json.dumps(manifest))
    freeze_path = frozen / "freeze.json"
    freeze = json.loads(freeze_path.read_bytes())
    freeze["protocol_sha256"] = sha(protocol_path)
    freeze["input_manifest_sha256"] = sha(manifest_path)
    freeze["predictions_sha256"] = sha(prediction_path)
    freeze_path.write_text(json.dumps(freeze))
    original_freeze = sha(freeze_path)
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("target counts entered")
    )
    output = repository / "artifacts/score-products"
    with pytest.raises(ValueError, match="prediction bin-method grid differs"):
        scores.run(repository, output)
    assert not output.exists()
    assert sha(freeze_path) == original_freeze
