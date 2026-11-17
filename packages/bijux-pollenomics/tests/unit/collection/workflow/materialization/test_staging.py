"""Collection callbacks preserve complete output and retain private failures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.workflow import (
    build_staging_output_dir,
    collect_into_staging_dir,
)
from bijux_pollenomics.core.filesystem import replacement


def test_build_staging_output_dir_keeps_historical_sibling_name() -> None:
    assert build_staging_output_dir(Path("/tmp/data/neotoma")) == Path(
        "/tmp/data/.neotoma.staging"
    )


def test_collect_into_staging_dir_swaps_in_completed_output(tmp_path: Path) -> None:
    final = tmp_path / "neotoma"

    def collect(root: Path) -> str:
        (root / "normalized").mkdir()
        (root / "normalized/fresh.csv").write_text("fresh", encoding="utf-8")
        return "ok"

    assert collect_into_staging_dir(final, collect) == "ok"
    assert (final / "normalized/fresh.csv").read_text(encoding="utf-8") == "fresh"
    assert not (tmp_path / ".neotoma.recovery").exists()


def test_collect_into_staging_dir_retains_failed_candidate(tmp_path: Path) -> None:
    final = tmp_path / "neotoma"
    candidates: list[Path] = []

    def collect(root: Path) -> None:
        candidates.append(root)
        (root / "partial.csv").write_text("partial", encoding="utf-8")
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        collect_into_staging_dir(final, collect)
    assert not final.exists()
    assert (candidates[0] / "partial.csv").read_text(encoding="utf-8") == "partial"
    assert not build_staging_output_dir(final).exists()


def test_collect_into_staging_dir_restores_prior_on_attachment_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    final = tmp_path / "neotoma"
    final.mkdir()
    prior = final / "prior.csv"
    prior.write_text("prior", encoding="utf-8")
    candidates: list[Path] = []
    original = replacement._rename_directory

    def fail_candidate(
        descriptor: int, source: str, target: str, **options: Any
    ) -> None:
        if candidates and source == candidates[0].name:
            raise OSError("candidate rename failed")
        original(descriptor, source, target, **options)

    def collect(root: Path) -> str:
        candidates.append(root)
        (root / "candidate.csv").write_text("candidate", encoding="utf-8")
        return "unreachable"

    monkeypatch.setattr(replacement, "_rename_directory", fail_candidate)
    with pytest.raises(OSError, match="candidate rename failed"):
        collect_into_staging_dir(final, collect)
    assert prior.read_text(encoding="utf-8") == "prior"
    assert (candidates[0] / "candidate.csv").read_text(encoding="utf-8") == "candidate"
    assert not build_staging_output_dir(final).exists()


@pytest.mark.parametrize("prior_present", [False, True])
def test_collect_into_staging_dir_preserves_interrupted_recovery(
    tmp_path: Path, prior_present: bool
) -> None:
    final = tmp_path / "neotoma"
    recovery = tmp_path / ".neotoma.recovery"
    recovery.mkdir()
    prior = recovery / "prior.csv"
    prior.write_text("prior", encoding="utf-8")
    if prior_present:
        final.mkdir()
        (final / "current.csv").write_text("current", encoding="utf-8")
    calls: list[Path] = []
    with pytest.raises(FileExistsError, match="recovery requires review"):
        collect_into_staging_dir(final, lambda root: calls.append(root))
    assert calls == []
    assert prior.read_text(encoding="utf-8") == "prior"
    assert final.exists() is prior_present
