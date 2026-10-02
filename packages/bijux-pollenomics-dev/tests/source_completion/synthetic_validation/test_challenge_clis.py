"""Constructed report routes retain source origin, argument and failure custody."""

from __future__ import annotations

from collections.abc import Callable
import importlib
from pathlib import Path
import sys
from types import ModuleType
from typing import cast

import pytest

from bijux_pollenomics_dev.source_completion.synthetic_validation.writer_execution import (
    run_writer,
)

NAMES = ("change_time", "spatial_eligibility")


def _module(name: str) -> ModuleType:
    return importlib.import_module(
        f"bijux_pollenomics_dev.source_completion.synthetic_validation.{name}"
    )


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("status", (0, 1))
def test_fixed_writer_route_and_argument_restoration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, status: int
) -> None:
    module = _module(name)
    calls: list[tuple[list[str], object]] = []

    def route(repository: Path, output: Path, writer: object) -> int:
        assert repository == tmp_path
        assert output == tmp_path / "report.json"
        calls.append((list(sys.argv), writer))
        return status

    monkeypatch.setattr(module, "run_writer", route)
    original = sys.argv
    if status:
        with pytest.raises(ValueError, match="contract refused"):
            module.run(tmp_path, tmp_path / "report.json")
    else:
        module.run(tmp_path, tmp_path / "report.json")
    assert sys.argv is original
    assert calls == [
        (
            [f"{name}_challenge", "--output", str(tmp_path / "report.json")],
            module.producer_main,
        )
    ]


def _writer(repo: Path) -> Callable[[], int]:
    source = repo / "packages/bijux-pollenomics-dev/src/fake_writer.py"
    source.parent.mkdir(parents=True)
    source.write_text("# maintained writer fixture\n")
    namespace: dict[str, object] = {}
    exec(compile("def writer():\n    return 0\n", str(source), "exec"), namespace)
    return cast(Callable[[], int], namespace["writer"])


@pytest.mark.parametrize(
    "unsafe",
    (
        "existing",
        "outside",
        "source-link",
        "source-parent-link",
        "artifact-link",
        "output-parent-link",
    ),
)
def test_writer_source_and_output_confinement(tmp_path: Path, unsafe: str) -> None:
    repo = tmp_path / "repository"
    (repo / "artifacts").mkdir(parents=True)
    writer = _writer(repo)
    source = Path(writer.__code__.co_filename)
    output = repo / "artifacts/owner/report.json"
    if unsafe == "existing":
        output.parent.mkdir()
        output.write_text("existing")
    elif unsafe == "outside":
        output = tmp_path / "outside.json"
    elif unsafe == "source-link":
        other = repo / "other.py"
        other.write_text(source.read_text())
        source.unlink()
        source.symlink_to(other)
    elif unsafe == "source-parent-link":
        other = source.parent.with_name("actual-source")
        source.parent.rename(other)
        source.parent.symlink_to(other, target_is_directory=True)
    elif unsafe == "artifact-link":
        (repo / "artifacts").rename(repo / "artifact-target")
        (repo / "artifacts").symlink_to(
            repo / "artifact-target", target_is_directory=True
        )
    else:
        target = repo / "artifacts/target"
        target.mkdir()
        output.parent.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="invalid|symlink|outside|absent"):
        run_writer(repo, output, writer)


def test_writer_retains_native_status_without_creating_output(tmp_path: Path) -> None:
    repo = tmp_path / "repository"
    (repo / "artifacts").mkdir(parents=True)
    writer = _writer(repo)
    output = repo / "artifacts/owner/report.json"
    assert run_writer(repo, output, writer) == 0
    assert not output.exists()


@pytest.mark.parametrize("name", NAMES)
def test_cli_requires_paths_and_rejects_protocol_override(name: str) -> None:
    module = _module(name)
    with pytest.raises(SystemExit, match="2"):
        module.main(
            ["--repository", ".", "--output", "artifacts/output", "--seed", "2"]
        )
