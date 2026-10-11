"""Check the contained-age source route without running the retained study."""

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
    sambosjon_contained_age as route,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))


def fixture_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    source = repository / route.SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("# fixture source\n")
    for relative in (
        "protocol.json",
        "inputs/input-manifest.json",
        "inputs/metadata.json",
        "inputs/training.json.gz",
        "frozen/freeze.json",
        "frozen/predictions.json",
        "coverage.csv",
        "report.json",
        "scores.csv",
        "age-bounds/report.json",
        "age-bounds/samples.csv",
    ):
        path = repository / route.STUDY / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"retained fixture\n")
    return repository


def fake_writer(output: Path, freeze_sha: str, *, wrong_status: bool = False) -> None:
    output.mkdir(parents=True, exist_ok=False)
    for name in route.OUTPUTS - {"report.json"}:
        (output / name).write_bytes(b"fixture output\n")
    write_json(
        output / "report.json",
        {
            "schema_version": "sambosjon-interval-support.v1",
            "sample_statuses": {
                "contained": 52 if wrong_status else 53,
                "crosses_boundary": 58,
            },
            "candidate_bins": 22,
            "scored_common_bins": 21,
            "refused_or_failed_bins": 1,
            "attempted_method_bin_scores": 66,
            "input_sha256": {"frozen/freeze.json": freeze_sha},
        },
    )


def test_fixed_source_module_and_four_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(repository / route.SOURCE)),
    )
    seen: list[tuple[str, list[str]]] = []

    def fake_run(module: str, *, run_name: str) -> None:
        assert run_name == "__main__"
        seen.append((module, sys.argv.copy()))
        fake_writer(
            Path(sys.argv[-1]), sha(repository / route.STUDY / "frozen/freeze.json")
        )

    monkeypatch.setattr(runpy, "run_module", fake_run)
    output = repository / "artifacts/source-products"
    original = sys.argv
    assert route.main(["--repository", str(repository), "--output", str(output)]) == 0
    assert sys.argv is original
    assert seen == [
        (
            "bijux_pollenomics_dev.source_completion.pollen_age_support.sambosjon",
            [
                str(repository / route.SOURCE),
                "--repository",
                str(repository),
                "--output",
                str(output),
            ],
        )
    ]
    assert {path.name for path in output.iterdir()} == route.OUTPUTS


def test_foreign_origin_and_symlinked_input_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    output = repository / "artifacts/source-products"
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin="/foreign.py"),
    )
    with pytest.raises(ValueError, match="origin"):
        route.main(["--repository", str(repository), "--output", str(output)])
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(repository / route.SOURCE)),
    )
    training = repository / route.STUDY / "inputs/training.json.gz"
    training.unlink()
    training.symlink_to(repository / route.STUDY / "scores.csv")
    with pytest.raises(ValueError, match="symlink"):
        route.main(["--repository", str(repository), "--output", str(output)])


def test_wrong_denominator_refused_and_argv_restored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = fixture_repository(tmp_path)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(repository / route.SOURCE)),
    )

    def fake_run(module: str, *, run_name: str) -> None:
        fake_writer(
            Path(sys.argv[-1]),
            sha(repository / route.STUDY / "frozen/freeze.json"),
            wrong_status=True,
        )

    monkeypatch.setattr(runpy, "run_module", fake_run)
    original = sys.argv
    with pytest.raises(ValueError, match="denominator"):
        route.main(
            [
                "--repository",
                str(repository),
                "--output",
                str(repository / "artifacts/source-products"),
            ]
        )
    assert sys.argv is original


@pytest.mark.parametrize("relative", ("../outside", "artifacts/existing"))
def test_output_confinement_and_reuse(tmp_path: Path, relative: str) -> None:
    repository = fixture_repository(tmp_path)
    output = repository / relative
    if relative == "artifacts/existing":
        output.mkdir()
    with pytest.raises(ValueError, match="absent artifact"):
        route.main(["--repository", str(repository), "--output", str(output)])
