"""Routing and destination guards for the governed SEAD writer entry points."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

import pytest


def _load(name: str) -> ModuleType:
    return importlib.import_module(
        f"bijux_pollenomics_dev.source_completion.sead.{name}"
    )


@pytest.mark.parametrize(
    ("name", "writer"),
    [
        ("chronology_age_review", "write_sead_chronology_age_review"),
        ("record_intervals", "write_sead_interval_set_review"),
    ],
)
def test_run_passes_repository_data_and_absent_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, writer: str
) -> None:
    module = _load(name)
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "artifacts").mkdir()
    destination = repository / "artifacts/source-products"
    calls: list[tuple[Path, Path]] = []

    def fake(data: Path, output: Path) -> dict[str, str]:
        calls.append((data, output))
        return {"status": "routed"}

    monkeypatch.setattr(module, writer, fake)
    assert module.run(repository, destination) == {"status": "routed"}
    assert calls == [(repository / "data", destination)]
    assert (
        module.main(["--repository", str(repository), "--output", str(destination)])
        == 0
    )
    assert calls == [(repository / "data", destination)] * 2
    assert not destination.exists()


@pytest.mark.parametrize(
    ("name", "writer"),
    [
        ("chronology_age_review", "write_sead_chronology_age_review"),
        ("record_intervals", "write_sead_interval_set_review"),
    ],
)
def test_run_refuses_existing_and_external_destinations_before_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, writer: str
) -> None:
    module = _load(name)
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    existing = repository / "artifacts/existing"
    existing.mkdir()
    external = tmp_path / "outside"
    linked = repository / "artifacts/linked"
    linked.symlink_to(external)
    escape_parent = repository / "artifacts/escape"
    escape_parent.symlink_to(tmp_path, target_is_directory=True)
    calls: list[object] = []
    monkeypatch.setattr(module, writer, lambda *_: calls.append(True))
    for destination in (
        existing,
        external,
        linked,
        escape_parent / "new",
        repository / "artifacts",
    ):
        with pytest.raises(ValueError, match="destination"):
            module.run(repository, destination)
    assert not calls


@pytest.mark.parametrize("name", ["chronology_age_review", "record_intervals"])
def test_main_requires_fixed_repository_and_output_flags(name: str) -> None:
    module = _load(name)
    with pytest.raises(SystemExit, match="2"):
        module.main(["--repository", "."])
    with pytest.raises(SystemExit, match="2"):
        module.main(["--output", "somewhere"])
    with pytest.raises(SystemExit, match="2"):
        module.main(["--repository", ".", "--output", "somewhere", "--capture", "x"])


@pytest.mark.parametrize(
    ("name", "writer"),
    [
        ("chronology_age_review", "write_sead_chronology_age_review"),
        ("record_intervals", "write_sead_interval_set_review"),
    ],
)
def test_core_writer_refusal_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, writer: str
) -> None:
    module = _load(name)
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)

    def fake_writer(_data: Path, _output: Path) -> dict[str, str]:
        raise ValueError("core source identity changed")

    monkeypatch.setattr(module, writer, fake_writer)
    with pytest.raises(ValueError, match="core source identity changed"):
        module.run(repository, repository / "artifacts/result")
