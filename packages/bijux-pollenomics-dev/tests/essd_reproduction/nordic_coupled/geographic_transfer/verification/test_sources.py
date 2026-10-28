"""Bind the new source projection to original manifests rather than its own labels."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer.inputs import (
    load_inputs,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer.verification import (
    sources,
)

from ..test_inputs import _fixture


def test_independent_projection_joins_original_arrays_and_native_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, protocol = _fixture(tmp_path / "source")
    packet = load_inputs(repository, protocol)
    # The old 141-file source algorithm has its own qualified full-source controls.
    monkeypatch.setattr(
        sources,
        "bind_sources",
        lambda *args: {"status": "passed", "source_files_verified": 141},
    )
    counts, facts = sources.bind_projection(repository, protocol, packet)
    assert len(counts) == 3
    assert all(set(row) == {"Betula", "Ulmus"} for row in counts.values())
    assert facts["source_files_verified"] == 141


@pytest.mark.parametrize("key", ["request", "cover_csv", "regional_csv"])
def test_same_hash_under_another_native_member_name_cannot_change_responsibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str
) -> None:
    repository, protocol = _fixture(tmp_path / "source")
    packet = load_inputs(repository, protocol)
    monkeypatch.setattr(sources, "bind_sources", lambda *args: {"status": "passed"})
    ref = packet["candidate_cases"][0]["scientific_refs"]["nominal_fits"][0][key]
    original = repository / ref["path"]
    alternate = original.with_name("other-" + original.name)
    alternate.write_bytes(original.read_bytes())
    ref["path"] = alternate.relative_to(repository).as_posix()
    with pytest.raises(
        ValueError, match="manifest-bound request|exact native fit member"
    ):
        sources.bind_projection(repository, protocol, packet)


def test_candidate_cannot_replace_an_original_signed_fit_draw(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, protocol = _fixture(tmp_path / "source")
    packet = load_inputs(repository, protocol)
    monkeypatch.setattr(sources, "bind_sources", lambda *args: {"status": "passed"})
    packet["candidate_cases"][0]["cached_fit"]["local_signed_cover"][0][0][1] = [
        0.3,
        0.7,
    ]
    with pytest.raises(ValueError, match="cached fit draws"):
        sources.bind_projection(repository, protocol, packet)
