"""Native publication failures retain their identity and every recoverable tree."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.core.files import write_json

from .support import NAMES, publish, snapshot


@pytest.mark.parametrize("kind", ["default", "custom_open"])
def test_callback_once_and_canonical_return_paths(tmp_path: Path, kind: str) -> None:
    """Both ordinary supported writers use the supplied descriptor capability."""
    calls: list[tuple[Path, object]] = []

    def write(path: Path, payload: object) -> None:
        calls.append((path, payload))
        if kind == "default":
            write_json(path, payload)
        else:
            with path.open("w", encoding="utf-8") as stream:
                json.dump(payload, stream)

    output = tmp_path / "collection"
    report = publish(output, (b"new-one", b"new-two"), write=write)
    assert report.version == "v66" and report.version_dir == output / "v66"
    assert report.downloaded_files == tuple(output / "v66" / name for name in NAMES)
    assert report.manifest_path == output / "v66/release_manifest.json"
    assert len(calls) == 1 and str(calls[0][0]).startswith("/dev/fd/")
    assert json.loads(report.manifest_path.read_bytes()) == calls[0][1]


def test_primary_callback_survives_secondary_receipt_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Receipt failure cannot replace the native manifest-writer exception."""
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    output = tmp_path / "collection"
    publish(output, (b"old-one", b"old-two"))
    before = snapshot(output)
    primary = OSError("generated primary manifest refusal")
    real_write = OwnedTreeWriter.write_bytes

    def written(writer: OwnedTreeWriter, name: str, raw: bytes) -> None:
        if name == "failed-operation.json":
            raise OSError("generated secondary receipt refusal")
        real_write(writer, name, raw)

    def write(path: Path, payload: object) -> None:
        raise primary

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", written)
    with pytest.raises(OSError) as refused:
        publish(output, (b"new-one", b"new-two"), write=write)
    assert refused.value is primary
    assert snapshot(output) == before
    assert any("receipt failed" in note for note in primary.__notes__)


@pytest.mark.parametrize("failure_type", [OSError, KeyboardInterrupt])
@pytest.mark.parametrize("failed_move", [3, 4])
def test_postattach_primary_survives_secondary_restore_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_type: type[BaseException],
    failed_move: int,
) -> None:
    """An attempted restore cannot replace the original validation failure."""
    import bijux_pollenomics.collection.sources.aadr.download as download
    import bijux_pollenomics.core.filesystem.replacement as replacement

    output = tmp_path / "collection"
    publish(output, (b"old-one", b"old-two"))
    primary = failure_type("generated final validation refusal")
    real_validate = download.validate_downloaded_anno_payload
    real_move = replacement._move
    validations: list[int] = []
    movements: list[str] = []

    def validate(*args: Any, **kwargs: Any) -> None:
        validations.append(1)
        if len(validations) == 5:
            raise primary
        real_validate(*args, **kwargs)

    def move(*args: Any, **kwargs: Any) -> None:
        movements.append(str(args[1]))
        if len(movements) == failed_move:
            raise OSError("generated secondary restore refusal")
        real_move(*args, **kwargs)

    monkeypatch.setattr(download, "validate_downloaded_anno_payload", validate)
    monkeypatch.setattr(replacement, "_move", move)
    with pytest.raises(failure_type) as refused:
        publish(output, (b"new-one", b"new-two"))
    assert len(movements) == failed_move
    assert refused.value is primary
