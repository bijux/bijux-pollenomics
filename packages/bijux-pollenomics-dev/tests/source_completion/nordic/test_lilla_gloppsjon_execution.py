"""Check fixed retained Lilla routes with fake source writers only."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.nordic import (
    lilla_gloppsjon_contained_age as contained,
)
from bijux_pollenomics_dev.source_completion.nordic import (
    lilla_gloppsjon_execution as execution,
)
from bijux_pollenomics_dev.source_completion.nordic import (
    lilla_gloppsjon_predictions as predictions,
)
from bijux_pollenomics_dev.source_completion.nordic import (
    lilla_gloppsjon_scores as scores,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))


def fixture_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    for source in (
        execution.PREDICT_SOURCE,
        execution.SCORE_SOURCE,
        execution.INTERVAL_SOURCE,
    ):
        path = repository / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture source\n")
    study = repository / execution.STUDY
    protocol = study / "protocol.json"
    write_json(protocol, {"target_site_id": execution.SITE})
    prepared = study / "inputs"
    write_json(prepared / "metadata.json", {"site_id": execution.SITE})
    write_json(
        prepared / "input-manifest.json",
        {
            "protocol_sha256": sha(protocol),
            "metadata_sha256": sha(prepared / "metadata.json"),
            "target_observations_used_for_prediction": False,
        },
    )
    frozen = study / "frozen"
    write_json(frozen / "predictions.json", {"predictions": [{}] * 69, "refusals": []})
    write_json(
        frozen / "freeze.json",
        {
            "schema_version": "lilla-gloppsjon-direct-pollen-freeze.v1",
            "target_site_id": execution.SITE,
            "target_observations_used_for_prediction": False,
            "predictions_sha256": sha(frozen / "predictions.json"),
            "prediction_rows": 69,
            "predicted_bins": 23,
            "refused_bins": 0,
        },
    )
    scored = study / "scored"
    for name in execution.SCORED_FILES - {"report.json"}:
        path = scored / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"retained score fixture\n")
    write_json(scored / "report.json", {"scored_common_bins": 23})
    return repository


def fake_frozen(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "predictions.json", {"predictions": [{}] * 69, "refusals": []})
    write_json(
        output / "freeze.json",
        {
            "schema_version": "lilla-gloppsjon-direct-pollen-freeze.v1",
            "target_observations_used_for_prediction": False,
            "target_site_id": execution.SITE,
            "prediction_rows": 69,
            "predicted_bins": 23,
            "refused_bins": 0,
            "predictions_sha256": sha(output / "predictions.json"),
        },
    )


def fake_scored(output: Path, freeze_sha: str) -> None:
    output.mkdir(parents=True, exist_ok=False)
    for name in execution.SCORED_FILES - {"report.json"}:
        (output / name).write_bytes(b"score fixture\n")
    write_json(
        output / "report.json",
        {
            "candidate_bins": 23,
            "predicted_bins": 23,
            "scored_common_bins": 23,
            "refused_or_failed_bins": 0,
            "prediction_freeze_sha256": freeze_sha,
        },
    )


def fake_interval(output: Path, freeze_sha: str) -> None:
    output.mkdir(parents=True, exist_ok=False)
    for name in execution.INTERVAL_FILES - {"report.json"}:
        (output / name).write_bytes(b"interval fixture\n")
    write_json(
        output / "report.json",
        {
            "candidate_bins": 23,
            "scored_common_bins": 20,
            "refused_or_failed_bins": 3,
            "prediction_freeze_sha256": freeze_sha,
            "sample_statuses": {
                "age_refused": 2,
                "contained": 42,
                "crosses_boundary": 42,
            },
        },
    )


@pytest.mark.parametrize("route", ("predict", "score"))
def test_fixed_package_route_and_exact_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: str
) -> None:
    repository = fixture_repository(tmp_path)
    source = execution.PREDICT_SOURCE if route == "predict" else execution.SCORE_SOURCE
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(repository / source)),
    )
    seen: list[tuple[str, list[str]]] = []

    def fake_run(module: str, *, run_name: str) -> None:
        assert run_name == "__main__"
        seen.append((module, sys.argv.copy()))
        output = Path(sys.argv[-1])
        if route == "predict":
            fake_frozen(output)
        else:
            frozen = repository / execution.STUDY / "frozen"
            assert sys.argv[sys.argv.index("--freeze-sha256") + 1] == sha(
                frozen / "freeze.json"
            )
            fake_scored(output, sha(frozen / "freeze.json"))

    monkeypatch.setattr(runpy, "run_module", fake_run)
    original = sys.argv
    output = repository / "artifacts/source-products"
    wrapper = predictions if route == "predict" else scores
    assert wrapper.main(["--repository", str(repository), "--output", str(output)]) == 0
    assert sys.argv is original
    assert len(seen) == 1
    assert seen[0][0] == (
        "bijux_pollenomics_dev.source_completion.lilla_gloppsjon_direct_pollen"
        if route == "predict"
        else "bijux_pollenomics_dev.source_completion.lilla_gloppsjon_direct_pollen_scoring"
    )
    assert {path.name for path in output.iterdir()} == (
        execution.FROZEN_FILES if route == "predict" else execution.SCORED_FILES
    )


def test_original_interval_script_route_and_argument_restoration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    seen: list[tuple[str, list[str]]] = []

    def fake_run(path: str, *, run_name: str) -> None:
        assert run_name == "__main__"
        seen.append((path, sys.argv.copy()))
        fake_interval(
            Path(sys.argv[-1]),
            sha(repository / execution.STUDY / "frozen/freeze.json"),
        )

    monkeypatch.setattr(runpy, "run_path", fake_run)
    original = sys.argv
    output = repository / "artifacts/source-products"
    assert (
        contained.main(["--repository", str(repository), "--output", str(output)]) == 0
    )
    assert sys.argv is original
    assert seen == [
        (
            str(repository / execution.INTERVAL_SOURCE),
            [
                str(repository / execution.INTERVAL_SOURCE),
                "--repository",
                str(repository),
                "--output",
                str(output),
            ],
        )
    ]
    assert {path.name for path in output.iterdir()} == execution.INTERVAL_FILES


@pytest.mark.parametrize("relative", ("../outside", "docs/report/output"))
def test_destination_outside_artifacts_refused(tmp_path: Path, relative: str) -> None:
    repository = fixture_repository(tmp_path)
    with pytest.raises(ValueError, match="artifact destination|outside repository"):
        predictions.main(
            ["--repository", str(repository), "--output", str(repository / relative)]
        )


def test_symlinked_source_and_foreign_module_origin_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    source = repository / execution.PREDICT_SOURCE
    source.unlink()
    source.symlink_to(repository / execution.SCORE_SOURCE)
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError, match="symlink"):
        predictions.main(["--repository", str(repository), "--output", str(output)])
    source.unlink()
    source.write_text("# restored fixture\n")
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin="/foreign/producer.py"),
    )
    with pytest.raises(ValueError, match="origin"):
        predictions.main(["--repository", str(repository), "--output", str(output)])


def test_retained_freeze_refusal_precedes_scoring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    frozen = repository / execution.STUDY / "frozen/freeze.json"
    value = json.loads(frozen.read_bytes())
    value["target_observations_used_for_prediction"] = True
    write_json(frozen, value)
    monkeypatch.setattr(runpy, "run_module", lambda *a, **k: pytest.fail("ran source"))
    with pytest.raises(ValueError, match="freeze differs"):
        scores.main(
            [
                "--repository",
                str(repository),
                "--output",
                str(repository / "artifacts/source-products"),
            ]
        )


def test_unexpected_output_and_argument_restoration_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(
            origin=str(repository / execution.PREDICT_SOURCE)
        ),
    )

    def fake_run(module: str, *, run_name: str) -> None:
        fake_frozen(Path(sys.argv[-1]))
        (Path(sys.argv[-1]) / "undeclared.txt").write_text("extra")

    monkeypatch.setattr(runpy, "run_module", fake_run)
    original = sys.argv
    with pytest.raises(ValueError, match="population differs"):
        predictions.main(
            [
                "--repository",
                str(repository),
                "--output",
                str(repository / "artifacts/source-products"),
            ]
        )
    assert sys.argv is original


def test_reused_output_and_symlinked_parent_refused(tmp_path: Path) -> None:
    repository = fixture_repository(tmp_path)
    existing = repository / "artifacts/source-products"
    existing.mkdir()
    with pytest.raises(ValueError, match="absent"):
        contained.main(["--repository", str(repository), "--output", str(existing)])
    alias = repository / "artifacts/alias"
    alias.symlink_to(repository / "artifacts/source-products")
    with pytest.raises(ValueError, match="symlink"):
        contained.main(
            ["--repository", str(repository), "--output", str(alias / "other")]
        )
