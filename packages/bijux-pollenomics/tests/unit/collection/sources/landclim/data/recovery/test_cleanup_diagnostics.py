"""Recovery diagnostics cannot replace transaction failures or owned trees."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.landclim.raw_assets import transaction


@pytest.mark.parametrize("site", ["failed", "displaced", "retained"])
@pytest.mark.parametrize("diagnostics", ["ordinary", "annotation"])
def test_recovery_note_preserves_primary_and_owned_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: str, diagnostics: str
) -> None:
    """Each concrete recovery note remains subordinate to the producer failure."""
    prefix = {
        "failed": "LandClim recovery failed:",
        "displaced": "LandClim recovery originally allocated",
        "retained": "LandClim recovery state retained",
    }[site]

    class Primary(OSError):
        def add_note(self, note: str) -> None:
            if diagnostics == "annotation" and note.startswith(prefix):
                raise RuntimeError("generated annotation failure")
            super().add_note(note)

    primary = Primary("generated producer failure")
    real_receipt = transaction._receipt

    def receipt(run: transaction._Directory, status: str, **fields: object) -> None:
        if site == "failed" and status == "refused":
            raise OSError("generated receipt failure")
        real_receipt(run, status, **fields)

    monkeypatch.setattr(transaction, "_receipt", receipt)
    public = tmp_path / "collection"
    public.mkdir()
    (public / "prior").write_bytes(b"prior owned bytes")
    candidates: list[Path] = []
    foreign: list[Path] = []

    def produce(candidate: Path) -> None:
        (candidate / "generated").write_bytes(b"candidate owned bytes")
        if site == "displaced":
            run = candidate.parent
            detached = run.with_name("detached-owned-recovery")
            run.rename(detached)
            run.mkdir()
            (run / "foreign").write_bytes(b"foreign owner")
            foreign.append(run)
            candidates.append(detached / "candidate")
        else:
            candidates.append(candidate)
        raise primary

    with pytest.raises(Primary) as caught:
        transaction.transact(public, produce)
    assert caught.value is primary
    assert (public / "prior").read_bytes() == b"prior owned bytes"
    assert (candidates[0] / "generated").read_bytes() == b"candidate owned bytes"
    if foreign:
        assert (foreign[0] / "foreign").read_bytes() == b"foreign owner"
    if diagnostics == "ordinary":
        assert any(note.startswith(prefix) for note in primary.__notes__)
    elif site == "failed":
        assert any("recovery state retained" in note for note in primary.__notes__)


@pytest.mark.parametrize("diagnostics", ["notes", "format"])
def test_recovery_diagnostic_protocol_failure_preserves_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, diagnostics: str
) -> None:
    """Malformed notes and a secondary formatter cannot escape recovery."""
    primary = OSError("generated producer failure")
    if diagnostics == "notes":
        primary.__notes__ = ()  # type: ignore[assignment]

    class Unprintable(OSError):
        def __str__(self) -> str:
            raise RuntimeError("generated formatting failure")

    real_receipt = transaction._receipt

    def receipt(run: transaction._Directory, status: str, **fields: object) -> None:
        if status == "refused" and diagnostics == "format":
            raise Unprintable()
        real_receipt(run, status, **fields)

    monkeypatch.setattr(transaction, "_receipt", receipt)

    def produce(candidate: Path) -> None:
        (candidate / "generated").write_bytes(b"candidate")
        raise primary

    with pytest.raises(OSError) as caught:
        transaction.transact(tmp_path / "collection", produce)
    assert caught.value is primary
    if diagnostics == "notes":
        assert vars(primary)["__notes__"] == ()
    else:
        assert any("state retained" in note for note in primary.__notes__)
