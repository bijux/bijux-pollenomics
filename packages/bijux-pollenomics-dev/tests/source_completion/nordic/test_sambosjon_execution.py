"""Exercise Sämbosjön source-stage routing with fixture source CLIs only."""

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
from bijux_pollenomics_dev.source_completion.nordic import (
    sambosjon_predictions as predictions,
)
from bijux_pollenomics_dev.source_completion.nordic import (
    sambosjon_preparation as preparation,
)


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


def test_preparation_only_invokes_original_prepare_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    bind_origin(monkeypatch, repository)
    output = repository / "artifacts/source-products"
    calls: list[list[str]] = []

    def fake_run(module: str, *, run_name: str) -> None:
        assert module.endswith("sambosjon_direct_pollen") and run_name == "__main__"
        calls.append(list(sys.argv))
        output.mkdir()
        for name in ("training.json.gz", "metadata.json", "input-manifest.json"):
            (output / name).write_bytes(b"fixture prepared output")

    monkeypatch.setattr(runpy, "run_module", fake_run)
    old = sys.argv
    assert (
        preparation.main(["--repository", str(repository), "--output", str(output)])
        == 0
    )
    assert sys.argv is old
    assert calls == [
        [
            str(repository / execution.SOURCE),
            "prepare",
            "--repository",
            str(repository),
            "--output",
            str(output),
        ]
    ]


def test_prediction_retains_complete_stage_and_exposes_only_prediction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    bind_origin(monkeypatch, repository)
    output = repository / "artifacts/source-products"
    calls: list[list[str]] = []

    def fake_run(module: str, *, run_name: str) -> None:
        assert module.endswith("sambosjon_direct_pollen") and run_name == "__main__"
        calls.append(list(sys.argv))
        fake_complete_stage(repository, Path(sys.argv[-1]))

    monkeypatch.setattr(runpy, "run_module", fake_run)
    old = sys.argv
    assert (
        predictions.main(["--repository", str(repository), "--output", str(output)])
        == 0
    )
    assert sys.argv is old
    assert len(calls) == 1 and calls[0][1:6] == [
        "predict",
        "--repository",
        str(repository),
        "--prepared",
        str(repository / execution.PREPARED),
    ]
    assert sorted(path.name for path in output.iterdir()) == ["predictions.json"]
    stage_roots = list(
        (repository / "artifacts/jobs/retained-pollen-freezes/sambosjon").iterdir()
    )
    assert len(stage_roots) == 1
    stage = stage_roots[0] / "complete-stage"
    assert sorted(path.name for path in stage.iterdir()) == [
        "freeze.json",
        "predictions.json",
    ]
    assert sha(stage / "predictions.json") == sha(output / "predictions.json")


@pytest.mark.parametrize(
    "mode", ("outside", "existing", "relative", "symlink", "origin")
)
def test_refuses_unsafe_destination_or_source_origin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    repository = fixture_repository(tmp_path)
    output = repository / "artifacts/source-products"
    bind_origin(monkeypatch, repository)
    if mode == "outside":
        output = tmp_path / "outside"
    elif mode == "existing":
        output.mkdir()
    elif mode == "relative":
        output = Path("artifacts/source-products")
    elif mode == "symlink":
        output.symlink_to(tmp_path, target_is_directory=True)
    else:
        monkeypatch.setattr(
            importlib.util,
            "find_spec",
            lambda module: SimpleNamespace(origin=str(repository / "foreign.py")),
        )
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("source entered")
    )
    with pytest.raises(ValueError):
        preparation.run(repository, output)


@pytest.mark.parametrize(
    "mode", ("changed_prepared", "target_in_prepared", "changed_protocol")
)
def test_prediction_refuses_changed_prepared_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    repository = fixture_repository(tmp_path)
    prepared = repository / execution.PREPARED
    if mode == "changed_prepared":
        (prepared / "training.json.gz").write_bytes(b"other")
    elif mode == "target_in_prepared":
        path = prepared / "input-manifest.json"
        value = json.loads(path.read_bytes())
        value["target_observation_profile_in_prepared_inputs"] = True
        path.write_text(json.dumps(value))
    else:
        (repository / execution.PROTOCOL).write_text("{}")
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("source entered")
    )
    with pytest.raises(ValueError):
        predictions.run(repository, repository / "artifacts/source-products")


def test_prediction_source_refusal_restores_argv_and_keeps_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    bind_origin(monkeypatch, repository)
    monkeypatch.setattr(
        runpy,
        "run_module",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("source refusal")),
    )
    old = sys.argv
    with pytest.raises(RuntimeError, match="source refusal"):
        predictions.run(repository, repository / "artifacts/source-products")
    assert sys.argv is old
    stage_roots = list(
        (repository / "artifacts/jobs/retained-pollen-freezes/sambosjon").iterdir()
    )
    assert (
        len(stage_roots) == 1 and (stage_roots[0] / "complete-stage").exists() is False
    )


@pytest.mark.parametrize(
    "mode", ("target_read", "wrong_rows", "wrong_prediction_sha", "extra_stage_file")
)
def test_prediction_refuses_unverified_complete_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    repository = fixture_repository(tmp_path)
    bind_origin(monkeypatch, repository)

    def fake_run(module: str, *, run_name: str) -> None:
        stage = Path(sys.argv[-1])
        fake_complete_stage(repository, stage)
        freeze_path = stage / "freeze.json"
        freeze = json.loads(freeze_path.read_bytes())
        if mode == "target_read":
            freeze["target_observations_used_for_prediction"] = True
        elif mode == "wrong_rows":
            freeze["prediction_rows"] = 65
        elif mode == "wrong_prediction_sha":
            freeze["predictions_sha256"] = "0" * 64
        else:
            (stage / "extra.txt").write_text("unexpected")
        if mode != "extra_stage_file":
            freeze_path.write_text(json.dumps(freeze))

    monkeypatch.setattr(runpy, "run_module", fake_run)
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError):
        predictions.run(repository, output)
    assert not output.exists()
    stage_roots = list(
        (repository / "artifacts/jobs/retained-pollen-freezes/sambosjon").iterdir()
    )
    assert len(stage_roots) == 1
    assert (stage_roots[0] / "complete-stage/freeze.json").is_file()


def test_prediction_refuses_duplicate_bin_with_complete_row_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    bind_origin(monkeypatch, repository)
    payload = prediction_payload()
    rows = payload["predictions"]
    assert isinstance(rows, list)
    rows[3]["bin_id"] = 1
    protocol_path = repository / execution.PROTOCOL
    protocol = json.loads(protocol_path.read_bytes())
    protocol["pre_score_predictions_sha256"] = hashlib.sha256(
        json.dumps(payload).encode()
    ).hexdigest()
    protocol_path.write_text(json.dumps(protocol))
    manifest_path = repository / execution.PREPARED / "input-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["protocol_sha256"] = sha(protocol_path)
    manifest_path.write_text(json.dumps(manifest))

    def fake_run(module: str, *, run_name: str) -> None:
        stage = Path(sys.argv[-1])
        fake_complete_stage(repository, stage)
        predictions_path = stage / "predictions.json"
        predictions_path.write_text(json.dumps(payload))
        freeze_path = stage / "freeze.json"
        freeze = json.loads(freeze_path.read_bytes())
        freeze["predictions_sha256"] = sha(predictions_path)
        freeze_path.write_text(json.dumps(freeze))

    monkeypatch.setattr(runpy, "run_module", fake_run)
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError, match="prediction bin-method grid differs"):
        predictions.run(repository, output)
    assert not output.exists()


def test_prediction_refuses_duplicate_candidate_bin_before_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    metadata_path = repository / execution.PREPARED / "metadata.json"
    metadata = json.loads(metadata_path.read_bytes())
    metadata["sites"][0]["candidate_bin_ids"][-1] = "21"
    metadata_path.write_text(json.dumps(metadata))
    manifest_path = repository / execution.PREPARED / "input-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["metadata_sha256"] = sha(metadata_path)
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("source entered")
    )
    with pytest.raises(ValueError, match="candidate bin identities differ"):
        predictions.run(repository, repository / "artifacts/source-products")
