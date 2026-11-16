"""Source replacement diagnostics preserve the original failure and candidate."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.publication import replacement
from bijux_pollenomics.core.filesystem import OwnedTreeWriter


@pytest.mark.parametrize("site", ["receipt", "runtime_receipt", "build", "publication"])
@pytest.mark.parametrize("diagnostics", ["ordinary", "notes", "annotation"])
def test_replacement_diagnostic_preserves_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: str, diagnostics: str
) -> None:
    """Failed build, receipt and publication paths retain their actual owner."""
    prefix = (
        "Neotoma refusal receipt"
        if site in {"receipt", "runtime_receipt"}
        else "Neotoma recovery state"
    )

    class Primary(OSError):
        def add_note(self, note: str) -> None:
            if diagnostics == "annotation" and note.startswith(prefix):
                raise RuntimeError("generated annotation failure")
            super().add_note(note)

    primary = Primary("generated source failure")
    if diagnostics == "notes":
        primary.__notes__ = ()  # type: ignore[assignment]
    real_write = OwnedTreeWriter.write_bytes

    def write(writer: OwnedTreeWriter, name: str, raw: bytes) -> None:
        if site in {"receipt", "runtime_receipt"} and name == "refused-build.json":
            error = RuntimeError if site == "runtime_receipt" else OSError
            raise error("generated receipt failure")
        real_write(writer, name, raw)

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", write)
    monkeypatch.setattr(replacement, "_destination_repository", lambda _: None)
    candidates: list[Path] = []

    def build(writer: OwnedTreeWriter) -> None:
        writer.write_bytes("generated", b"owned candidate")
        candidates.append(writer.root)
        if site != "publication":
            raise primary

    def validate(path: Path) -> None:
        assert (path / "generated").read_bytes() == b"owned candidate"
        raise primary

    final = tmp_path / "published"
    with pytest.raises(Primary) as caught:
        replacement.replace_neotoma_tree(
            final,
            build=build,
            validate=validate,
            max_bytes=replacement.SOURCE_MAX_BYTES,
        )
    assert caught.value is primary
    assert not final.exists()
    assert (candidates[0] / "generated").read_bytes() == b"owned candidate"
    if diagnostics == "ordinary":
        assert any(note.startswith(prefix) for note in primary.__notes__)
    elif diagnostics == "notes":
        assert vars(primary)["__notes__"] == ()
    elif site in {"receipt", "runtime_receipt"}:
        assert any("recovery state retained" in note for note in primary.__notes__)
