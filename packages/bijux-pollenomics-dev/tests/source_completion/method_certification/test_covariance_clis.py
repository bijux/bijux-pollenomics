"""Constructed covariance routes preserve protocol, source and artifact custody."""

from __future__ import annotations

import importlib
from pathlib import Path
import runpy
import sys
from types import ModuleType

import pytest

NAMES = (
    "method_certification.fixed_site_covariance",
    "method_certification.joint_site_draws",
)


def _module(name: str) -> ModuleType:
    return importlib.import_module(f"bijux_pollenomics_dev.source_completion.{name}")


def _repository(tmp_path: Path, module: ModuleType) -> tuple[Path, Path]:
    repo = tmp_path / "repository"
    source = repo / module.SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("# retained producer fixture\n")
    (repo / "artifacts").mkdir()
    return repo, source


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("fails", (False, True))
def test_fixed_source_route_and_argument_restoration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, fails: bool
) -> None:
    module = _module(name)
    repo, source = _repository(tmp_path, module)
    destination = repo / "artifacts/owner/source-products"
    calls: list[tuple[str, str, list[str]]] = []

    def invoke(path: str, *, run_name: str) -> None:
        calls.append((path, run_name, list(sys.argv)))
        if fails:
            raise ValueError("retained producer refusal")

    monkeypatch.setattr(runpy, "run_path", invoke)
    original = sys.argv
    if fails:
        with pytest.raises(ValueError, match="retained producer refusal"):
            module.run(repo, destination)
    else:
        module.run(repo, destination)
    assert sys.argv is original
    args = ["--repository", str(repo)]
    assert calls == [
        (str(source), "__main__", [str(source), *args, "--output", str(destination)])
    ]
    assert not destination.exists()


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize(
    "unsafe",
    (
        "existing-output",
        "outside-output",
        "source-link",
        "source-parent-link",
        "artifact-root-link",
        "output-ancestor-link",
    ),
)
def test_unsafe_paths_refused_before_producer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, unsafe: str
) -> None:
    module = _module(name)
    repo, source = _repository(tmp_path, module)
    output = repo / "artifacts/owner/source-products"
    if unsafe == "existing-output":
        output.mkdir(parents=True)
    elif unsafe == "outside-output":
        output = tmp_path / "outside-output"
    elif unsafe == "source-link":
        other = repo / "other.py"
        other.write_text(source.read_text())
        source.unlink()
        source.symlink_to(other)
    elif unsafe == "source-parent-link":
        actual = source.parent.with_name("retained-source")
        source.parent.rename(actual)
        source.parent.symlink_to(actual, target_is_directory=True)
    elif unsafe == "artifact-root-link":
        (repo / "artifacts").rename(repo / "artifact-target")
        (repo / "artifacts").symlink_to(
            repo / "artifact-target", target_is_directory=True
        )
    else:
        target = repo / "artifacts/actual-owner"
        target.mkdir()
        (repo / "artifacts/owner").symlink_to(target, target_is_directory=True)
    calls: list[object] = []
    monkeypatch.setattr(runpy, "run_path", lambda *a, **k: calls.append(True))
    with pytest.raises(
        ValueError,
        match="absent repository artifact|outside repository|invalid|real directory|ancestor may not be a symlink",
    ):
        module.run(repo, output)
    assert not calls


@pytest.mark.parametrize("name", NAMES)
def test_cli_requires_paths_and_rejects_seed_override(name: str) -> None:
    module = _module(name)
    for args in (
        ["--repository", "."],
        ["--output", "artifacts/output"],
        ["--repository", ".", "--output", "artifacts/output", "--seed", "42"],
    ):
        with pytest.raises(SystemExit, match="2"):
            module.main(args)
