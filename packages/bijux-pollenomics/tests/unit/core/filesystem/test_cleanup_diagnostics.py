"""Recovery diagnostics cannot replace validation failures or discard owned bytes."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.core.filesystem import OwnedTreeWriter, replacement
from bijux_pollenomics.core.filesystem.anchors import DirectoryAnchor


class _BrokenDiagnostic(OSError):
    def __str__(self) -> str:
        raise RuntimeError("cleanup formatting failed")


@pytest.mark.parametrize("boundary", ["receipt", "recovery"])
@pytest.mark.parametrize("diagnostic", ["notes", "annotation", "format"])
def test_replacement_diagnostics_preserve_primary_and_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boundary: str, diagnostic: str
) -> None:
    class Primary(OSError):
        def add_note(self, note: str) -> None:
            if diagnostic == "annotation":
                raise RuntimeError("annotation failed")
            super().add_note(note)

    primary = Primary("primary validation refusal")
    if diagnostic == "notes":
        primary.__notes__ = ()  # type: ignore[assignment]
    secondary = (
        _BrokenDiagnostic("secondary")
        if diagnostic == "format"
        else OSError("secondary recovery refusal")
    )
    final, run = tmp_path / "output", tmp_path / "run"
    run.mkdir()
    failed = False
    real_attached = replacement._attached

    def attached(*args: Any, **kwargs: Any) -> Any:
        if failed and boundary == "recovery":
            raise secondary
        return real_attached(*args, **kwargs)

    def validate(root: Path) -> None:
        nonlocal failed
        failed = True
        raise primary

    def record(status: str, fields: dict[str, Any]) -> None:
        raise secondary

    with (
        DirectoryAnchor(run) as recovery,
        OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
    ):
        writer.write_bytes("value", b"candidate")
        monkeypatch.setattr(replacement, "_attached", attached)
        with pytest.raises(Primary) as caught:
            replacement.publish_owned_replacement(
                writer,
                final=final,
                prior=None,
                recovery=recovery,
                validate=validate,
                record=record,
            )
        assert caught.value is primary
        assert (run / "candidate/value").read_bytes() == b"candidate"
        assert not final.exists()
