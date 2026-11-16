"""Private RAÄ publication diagnostics preserve caller failures and buffers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.reporting.context.raa import RaaAtlasInputSnapshot
from bijux_pollenomics.reporting.context.raa_staging import stage_raa_publication


@pytest.mark.parametrize("site", ["receipt", "retention"])
@pytest.mark.parametrize("diagnostics", ["ordinary", "notes", "annotation"])
def test_staging_note_preserves_primary_and_retained_buffers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: str, diagnostics: str
) -> None:
    """Literal non-admitted status bytes exercise the actual publication owner."""
    prefix = "RAÄ terminal receipt" if site == "receipt" else "RAÄ retained operation"

    class Primary(OSError):
        def add_note(self, note: str) -> None:
            if diagnostics == "annotation" and note.startswith(prefix):
                raise RuntimeError("generated annotation failure")
            super().add_note(note)

    primary = Primary("generated caller failure")
    if diagnostics == "notes":
        primary.__notes__ = ()  # type: ignore[assignment]
    status = json.dumps(
        {
            "schema_version": "raa-atlas-input-status.v1",
            "source_family": "raa",
            "inputs": {},
            "geometry_publication": {"default_enabled": False},
        }
    ).encode()
    snapshot = RaaAtlasInputSnapshot(status, None, None)
    real_write = OwnedTreeWriter.write_bytes
    attempted: list[str] = []

    def write(writer: OwnedTreeWriter, name: str, raw: bytes) -> None:
        attempted.append(name)
        if site == "receipt" and name == "terminal.json":
            raise OSError("generated terminal receipt failure")
        real_write(writer, name, raw)

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", write)
    output = tmp_path / "public"
    output.mkdir()
    candidates: list[Path] = []
    receipts: list[Path] = []
    with (
        pytest.raises(Primary) as caught,
        stage_raa_publication(snapshot=snapshot, output_dir=output) as owned,
    ):
        candidates.append(owned.directory)
        receipts.append(owned.receipt_path)
        raise primary
    assert caught.value is primary
    assert "terminal.json" in attempted
    assert not (output / "context/raa").exists()
    assert (candidates[0] / "raa_atlas_input_status.json").read_bytes() == status
    assert json.loads(receipts[0].read_bytes())["candidate"] == str(candidates[0])
    if diagnostics == "ordinary":
        assert any(note.startswith(prefix) for note in primary.__notes__)
    elif diagnostics == "notes":
        assert vars(primary)["__notes__"] == ()
    elif site == "receipt":
        assert any("retained operation receipt" in note for note in primary.__notes__)
