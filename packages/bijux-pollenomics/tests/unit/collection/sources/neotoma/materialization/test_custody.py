"""Every relational candidate write remains anchored to its authored tree."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import materialization

from .native_snapshot import _snapshot


def test_relational_writer_preserves_foreign_substituted_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = materialization._write_json_exclusive
    foreign: list[Path] = []

    def substituted(path: Path, payload: Any, **kwargs: Any) -> str:
        writer = kwargs.get("writer")
        root = (
            next(parent for parent in path.parents if parent.name == ".output.staging")
            if writer is None
            else writer.root
        )
        root.rename(root.with_name("displaced-owned"))
        root.mkdir()
        (root / "foreign.txt").write_text("preserve foreign")
        foreign.append(root)
        result = original(path, payload, **kwargs)
        raise OSError(f"stop after attempted write {result}")

    monkeypatch.setattr(materialization, "_write_json_exclusive", substituted)
    with pytest.raises((ValueError, OSError)):
        materialization.materialize_neotoma_relational_snapshot(
            tmp_path / "output", _snapshot()
        )
    assert len(foreign) == 1
    assert (foreign[0] / "foreign.txt").read_text() == "preserve foreign"
    assert {p.name for p in foreign[0].iterdir()} == {"foreign.txt"}


def test_repeated_relational_updates_keep_canonical_bytes_and_recoverable_prior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.publication import replacement
    from bijux_pollenomics.evidence.sources.neotoma import (
        validate_neotoma_relational_materialization,
    )

    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "pyproject.toml").write_text('[project]\nname="bijux-pollenomics"\n')
    monkeypatch.setattr(replacement, "find_repository_root", lambda _: repository)
    output = repository / "output"
    snapshots = []
    for _ in range(3):
        result = materialization.materialize_neotoma_relational_snapshot(
            output, _snapshot()
        )
        assert result == output / "manifest.json"
        validate_neotoma_relational_materialization(output)
        snapshots.append(
            {
                p.relative_to(output).as_posix(): p.read_bytes()
                for p in output.rglob("*")
                if p.is_file()
            }
        )
    assert snapshots[0] == snapshots[1] == snapshots[2]
    priors = list((repository / "artifacts/neotoma-publication").glob("*/prior"))
    assert len(priors) == 2
    for prior in priors:
        validate_neotoma_relational_materialization(prior)


def test_installed_source_location_preserves_standalone_relational_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.publication import replacement
    from bijux_pollenomics.core.repository import (
        RepositoryRootNotFoundError,
        find_repository_root,
    )

    installed = tmp_path / "installed" / "replacement.py"
    installed.parent.mkdir()
    installed.write_text('"""Installed module fixture."""\n')
    with pytest.raises(RepositoryRootNotFoundError):
        find_repository_root(installed)
    project = tmp_path / "standalone"
    project.mkdir()
    (project / "pyproject.toml").write_text('[project]\nname="standalone-user"\n')
    monkeypatch.setattr(replacement, "__file__", str(installed))
    output = project / "output"
    assert (
        materialization.materialize_neotoma_relational_snapshot(output, _snapshot())
        == output / "manifest.json"
    )
    materialization.materialize_neotoma_relational_snapshot(output, _snapshot())
    recoveries = list(project.glob(".neotoma-recovery-*"))
    assert len(recoveries) == 2
    assert sum((root / "prior").is_dir() for root in recoveries) == 1
    for root in recoveries:
        receipt = json.loads((root / "receipts/published.json").read_text())
        assert receipt["owning_repository"] is None
