"""Manifest callbacks retain one bounded source descriptor and canonical payload."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.aadr.publication import (
    MANIFEST_MAX_BYTES,
    ManifestOutput,
)
from bijux_pollenomics.core.files import write_json
from bijux_pollenomics.core.filesystem import DirectoryAnchor

from .support import publish, snapshot


@pytest.mark.parametrize("change", ["growth", "early_eof", "replacement"])
def test_actual_manifest_descriptor_refuses_changed_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    """A callback buffer cannot grow, truncate or change attachment during read."""
    with DirectoryAnchor(tmp_path) as anchor:
        output = ManifestOutput(anchor)
        real_read = os.read
        events: list[str] = []

        def read(fd: int, count: int) -> bytes:
            if fd == output.fd and not events:
                events.append(change)
                if change == "replacement":
                    (tmp_path / "manifest.json").rename(tmp_path / "retained.json")
                    (tmp_path / "manifest.json").write_bytes(b"foreign")
                else:
                    size = os.fstat(fd).st_size
                    os.ftruncate(fd, size + 5 if change == "growth" else size - 1)
            return real_read(fd, count)

        monkeypatch.setattr(os, "read", read)
        try:
            with pytest.raises(ValueError):
                output.capture(write_json, {"source": "AADR"})
            assert events == [change]
        finally:
            output.close()
        with pytest.raises(OSError):
            os.fstat(output.fd)
        if change == "replacement":
            assert (tmp_path / "manifest.json").read_bytes() == b"foreign"


@pytest.mark.parametrize(
    "kind", ["wrong_source", "duplicate_key", "oversized", "native_scalar_type"]
)
def test_bad_callback_output_preserves_prior_release(tmp_path: Path, kind: str) -> None:
    """A successful callback return cannot publish malformed or altered metadata."""
    output = tmp_path / "collection"
    publish(output, (b"old-one", b"old-two"))
    before = snapshot(output)
    calls: list[Path] = []

    def write(path: Path, payload: object) -> None:
        calls.append(path)
        if kind == "duplicate_key":
            path.write_bytes(b'{"source":"other","source":"AADR"}')
        elif kind == "oversized":
            path.write_bytes(b"x" * (MANIFEST_MAX_BYTES + 1))
        else:
            raw: Any = json.loads(json.dumps(payload))
            if kind == "wrong_source":
                raw["source"] = "other"
            else:
                raw["anno_files"][0]["file_id"] = True
            path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(ValueError):
        publish(output, (b"new-one", b"new-two"), write=write)
    assert len(calls) == 1 and snapshot(output) == before


@pytest.mark.parametrize(
    "field", ["versionNumber", "versionMinorNumber", "releaseTime", "lastUpdateTime"]
)
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_release_metadata_refuses_before_acquisition(
    tmp_path: Path, field: str, value: float
) -> None:
    """Every manifest control value is finite before assets or callbacks run."""
    from bijux_pollenomics.collection.sources.aadr.download import (
        download_aadr_anno_files,
    )

    from .support import metadata

    output = tmp_path / "collection"
    publish(output, (b"old-one", b"old-two"))
    before = snapshot(output)
    values = (b"new-one", b"new-two")
    source: Any = metadata(values)
    source["data"][0][field] = value
    binary_calls: list[str] = []
    callback_calls: list[Path] = []

    def fetch(url: str, **kwargs: Any) -> bytes:
        binary_calls.append(url)
        return values[int(url.rsplit("/", 1)[1]) - 1]

    def write(path: Path, payload: object) -> None:
        callback_calls.append(path)
        write_json(path, payload)

    with pytest.raises(ValueError):
        download_aadr_anno_files(
            output,
            "v66",
            fetch_binary_fn=fetch,
            fetch_release_history_metadata_fn=lambda: source,
            write_json_fn=write,
        )
    assert binary_calls == [] and callback_calls == []
    assert snapshot(output) == before
