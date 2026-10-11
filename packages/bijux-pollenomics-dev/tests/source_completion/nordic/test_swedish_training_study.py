"""Exercise fixed training-scope routing with small fake original stage writers."""

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
    swedish_training_study as study,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def repository_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    source = repository / study.SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("# fixture original stage source\n")
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda module: SimpleNamespace(origin=str(source))
    )
    return repository


def fake_stage(argv: list[str], *, invalid_freeze: bool = False) -> None:
    command = argv[1]
    output = Path(argv[argv.index("--output") + 1])
    output.mkdir()
    if command == "prepare":
        folds = []
        for scope in study.SCOPES:
            for site in study.SITES:
                folder = output / scope / site
                (folder / "inputs").mkdir(parents=True)
                for name in ("training-SE.json.gz", "metadata-SE.json.gz"):
                    (folder / "inputs" / name).write_bytes(b"fixture input")
                manifest = folder / "input-manifest.json"
                write(
                    manifest,
                    {
                        "target_outcomes_in_prediction_inputs": False,
                        "training_site_count": 2 if scope == "sweden_only" else 83,
                        "produced_file_sha256": {
                            "inputs/" + name: sha(folder / "inputs" / name)
                            for name in ("training-SE.json.gz", "metadata-SE.json.gz")
                        },
                    },
                )
                folds.append(
                    {
                        "scope": scope,
                        "site_id": site,
                        "input_manifest_sha256": sha(manifest),
                    }
                )
        write(
            output / "prepare.json",
            {"schema_version": "swedish-training-scope-preparation.v1", "folds": folds},
        )
    elif command == "predict":
        prepared = Path(argv[argv.index("--prepared") + 1])
        receipt = json.loads((prepared / "prepare.json").read_bytes())
        folds = []
        for fold in receipt["folds"]:
            path = output / fold["scope"] / fold["site_id"] / "predictions-SE.json.gz"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"fixture prediction")
            folds.append({**fold, "prediction_sha256": sha(path)})
        write(
            output / "freeze.json",
            {
                "schema_version": "swedish-training-scope-freeze.v1",
                "prepare_sha256": "0" * 64
                if invalid_freeze
                else sha(prepared / "prepare.json"),
                "folds": folds,
            },
        )
    elif command == "score":
        frozen = Path(argv[argv.index("--frozen") + 1])
        assert argv[argv.index("--freeze-sha256") + 1] == sha(frozen / "freeze.json")
        for name in study.SCORED - {"report.json"}:
            (output / name).write_bytes(b"fixture scored output")
        write(
            output / "report.json",
            {
                "score_rows": 279,
                "paired_score_rows": 117,
                "paired_site_bins": 39,
                "target_sites": 3,
                "coverage_rows": 6,
                "prediction_freeze_sha256": sha(frozen / "freeze.json"),
            },
        )
    else:
        pytest.fail("unexpected stage")


def test_original_stage_routes_and_thirty_complete_owned_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = repository_fixture(tmp_path, monkeypatch)
    output = repository / "artifacts/source-products"
    calls: list[list[str]] = []

    def writer(module: str, *, run_name: str) -> None:
        assert module.endswith("swedish_training_scope") and run_name == "__main__"
        calls.append(list(sys.argv))
        fake_stage(sys.argv)

    monkeypatch.setattr(runpy, "run_module", writer)
    original = sys.argv
    assert study.main(["--repository", str(repository), "--output", str(output)]) == 0
    assert sys.argv is original and [args[1] for args in calls] == [
        "prepare",
        "predict",
        "score",
    ]
    assert (
        "--repository" in calls[0]
        and "--repository" not in calls[1]
        and "--repository" in calls[2]
    )
    assert "--freeze-sha256" in calls[2]
    paths = [p for p in output.rglob("*") if p.is_file()]
    assert len(paths) == 30
    stage = next(
        (
            repository / "artifacts/jobs/retained-pollen-studies/swedish-training-scope"
        ).iterdir()
    )
    for path in paths:
        relative = path.relative_to(output).as_posix()
        original_path = (
            stage / relative
            if relative.startswith(("prepared/", "frozen/"))
            else stage / "scored" / relative
        )
        assert sha(path) == sha(original_path)


@pytest.mark.parametrize(
    "mode", ("outside", "relative", "existing", "symlink", "origin")
)
def test_unsafe_output_or_foreign_source_refused_before_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    repository = repository_fixture(tmp_path, monkeypatch)
    output = repository / "artifacts/source-products"
    if mode == "outside":
        output = tmp_path / "outside"
    elif mode == "relative":
        output = Path("artifacts/source-products")
    elif mode == "existing":
        output.mkdir()
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
        study.run(repository, output)


def test_changed_prediction_freeze_refused_before_target_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = repository_fixture(tmp_path, monkeypatch)
    seen: list[str] = []

    def writer(module: str, *, run_name: str) -> None:
        seen.append(sys.argv[1])
        assert sys.argv[1] != "score"
        fake_stage(sys.argv, invalid_freeze=True)

    monkeypatch.setattr(runpy, "run_module", writer)
    output = repository / "artifacts/source-products"
    with pytest.raises(ValueError, match="freeze differs"):
        study.run(repository, output)
    assert seen == ["prepare", "predict"] and not output.exists()


def test_source_failure_restores_arguments_and_retains_incomplete_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = repository_fixture(tmp_path, monkeypatch)
    original = sys.argv

    def refused(module: str, *, run_name: str) -> None:
        raise RuntimeError("original stage refused")

    monkeypatch.setattr(runpy, "run_module", refused)
    with pytest.raises(RuntimeError, match="original stage refused"):
        study.run(repository, repository / "artifacts/source-products")
    assert sys.argv is original
    assert (
        len(
            list(
                (
                    repository
                    / "artifacts/jobs/retained-pollen-studies/swedish-training-scope"
                ).iterdir()
            )
        )
        == 1
    )
