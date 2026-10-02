"""Check native readiness routing, original CLI exits and artifact confinement."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.source_completion.propagation import (
    native_readiness as readiness,
)


def fixture_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repository"
    (root / "artifacts").mkdir(parents=True)
    source = root / readiness.SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("# fixture original CLI\n")
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda module: SimpleNamespace(origin=str(source))
    )
    return root


def test_original_success_exit_preserves_arguments_and_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = fixture_repository(tmp_path, monkeypatch)
    output = root / "artifacts/report.json"
    seen: list[list[str]] = []

    def writer(module: str, *, run_name: str) -> None:
        assert module == readiness.MODULE and run_name == "__main__"
        seen.append(list(sys.argv))
        output.write_text(
            json.dumps(
                {
                    "schema_version": "neotoma-source-first-observed-readiness.v1",
                    "denominators": {
                        "sites": 2,
                        "attempts": 256,
                        "refused": 256,
                        "events": 0,
                        "estimator_invocations": 0,
                    },
                    "claims": {
                        "first_observed_events_admitted": False,
                        "scientific_accuracy_or_route_claim": False,
                    },
                }
            )
        )
        raise SystemExit(0)

    monkeypatch.setattr(runpy, "run_module", writer)
    original = sys.argv
    assert readiness.main(["--repository", str(root), "--output", str(output)]) == 0
    assert sys.argv is original
    assert seen == [
        [
            str(root / readiness.SOURCE),
            "--repository",
            str(root),
            "--output",
            str(output),
        ]
    ]


@pytest.mark.parametrize(
    "mode", ("outside", "relative", "existing", "symlink", "ancestor_symlink", "origin")
)
def test_unsafe_destination_and_foreign_source_refused_before_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    root = fixture_repository(tmp_path, monkeypatch)
    output = root / "artifacts/report.json"
    if mode == "outside":
        output = tmp_path / "outside.json"
    elif mode == "relative":
        output = Path("artifacts/report.json")
    elif mode == "existing":
        output.write_text("user work")
    elif mode == "symlink":
        output.symlink_to(tmp_path / "missing.json")
    elif mode == "ancestor_symlink":
        parent = root / "artifacts/linked"
        parent.symlink_to(tmp_path, target_is_directory=True)
        output = parent / "report.json"
    else:
        monkeypatch.setattr(
            importlib.util,
            "find_spec",
            lambda module: SimpleNamespace(origin=str(root / "foreign.py")),
        )
    monkeypatch.setattr(
        runpy, "run_module", lambda *a, **k: pytest.fail("original CLI entered")
    )
    with pytest.raises(ValueError):
        readiness.run(root, output)


@pytest.mark.parametrize("code", (1, "original refusal"))
def test_original_cli_failure_exit_propagates_and_restores_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, code: int | str
) -> None:
    root = fixture_repository(tmp_path, monkeypatch)
    original = sys.argv

    def refused(module: str, *, run_name: str) -> None:
        raise SystemExit(code)

    monkeypatch.setattr(runpy, "run_module", refused)
    with pytest.raises(SystemExit) as error:
        readiness.run(root, root / "artifacts/report.json")
    assert error.value.code == code and sys.argv is original


def test_event_promotion_refused_after_original_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = fixture_repository(tmp_path, monkeypatch)
    output = root / "artifacts/report.json"

    def writer(module: str, *, run_name: str) -> None:
        output.write_text(
            json.dumps(
                {
                    "schema_version": "neotoma-source-first-observed-readiness.v1",
                    "denominators": {
                        "sites": 2,
                        "attempts": 256,
                        "refused": 255,
                        "events": 1,
                        "estimator_invocations": 1,
                    },
                    "claims": {
                        "first_observed_events_admitted": True,
                        "scientific_accuracy_or_route_claim": True,
                    },
                }
            )
        )

    monkeypatch.setattr(runpy, "run_module", writer)
    with pytest.raises(ValueError, match="nonpromotion contract"):
        readiness.run(root, output)
