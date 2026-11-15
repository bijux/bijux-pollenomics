"""Nonblocking descriptor custody closes substitution races before source reads."""

from __future__ import annotations

import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import receipts

FIFO_CHILD = r"""
import json
import os
from pathlib import Path
import sys
from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read
path = Path(sys.argv[1])
path.write_bytes(b"x")
original = Path.stat
def swap(candidate, *args, **kwargs):
    node = original(candidate, *args, **kwargs)
    if candidate == path:
        path.unlink()
        os.mkfifo(path)
        print("FIFO_AFTER_REGULAR_STAT", flush=True)
    return node
Path.stat = swap
try:
    _read(path, 1)
except ValueError as error:
    print(json.dumps({"status": "refused", "error": str(error)}), file=sys.stderr, flush=True)
else:
    raise AssertionError("FIFO accepted")
"""


def test_fifo_substitution_refuses_after_real_stat_handshake(tmp_path: Path) -> None:
    path = tmp_path / "source.body"
    child = subprocess.Popen(
        [sys.executable, "-B", "-c", FIFO_CHILD, str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert child.stdout is not None
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            assert selector.select(30), "Child did not reach the substitution boundary"
            assert child.stdout.readline().strip() == "FIFO_AFTER_REGULAR_STAT"
        try:
            _, error = child.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            pytest.fail("Source open blocked after confirmed FIFO substitution")
        assert child.returncode == 0, error
        assert json.loads(error)["status"] == "refused"
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate()
        path.unlink(missing_ok=True)


@pytest.mark.parametrize("change", ["symlink", "inode", "size"])
def test_open_boundary_substitution_refuses_before_buffer_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    source, foreign = tmp_path / "source.body", tmp_path / "foreign.body"
    source.write_bytes(b"owned")
    foreign.write_bytes(b"other")
    opening, fdopen = os.open, os.fdopen
    descriptors: list[int] = []
    reads: list[int] = []

    def changed(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if Path(path) == source:
            if change != "size":
                source.rename(tmp_path / "displaced.body")
                if change == "symlink":
                    source.symlink_to(foreign)
                else:
                    foreign.rename(source)
            descriptor = opening(path, flags, *args, **kwargs)
            descriptors.append(descriptor)
            if change == "size":
                source.write_bytes(b"too large")
            return descriptor
        return opening(path, flags, *args, **kwargs)

    class Buffer:
        def __init__(self, stream: Any) -> None:
            self.stream = stream

        def __enter__(self) -> Buffer:
            return self

        def __exit__(self, *_: Any) -> None:
            self.stream.close()

        def fileno(self) -> int:
            return int(self.stream.fileno())

        def read(self, size: int) -> bytes:
            reads.append(size)
            return bytes(self.stream.read(size))

    monkeypatch.setattr(os, "open", changed)
    monkeypatch.setattr(os, "fdopen", lambda *a, **k: Buffer(fdopen(*a, **k)))
    with pytest.raises(ValueError, match="regular|bounded|identity|changed"):
        receipts._read(source, 5)
    assert reads == []
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)


@pytest.mark.parametrize("failure", ["success", "read", "fstat", "fdopen"])
def test_descriptor_is_closed_for_every_stream_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    source = tmp_path / "source.body"
    source.write_bytes(b"native")
    opening, fdopen, fstat = os.open, os.fdopen, os.fstat
    descriptors: list[int] = []

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = opening(path, flags, *args, **kwargs)
        if Path(path) == source:
            descriptors.append(descriptor)
        return descriptor

    class Buffer:
        def __init__(self, stream: Any) -> None:
            self.stream = stream

        def __enter__(self) -> Buffer:
            return self

        def __exit__(self, *_: Any) -> None:
            self.stream.close()

        def fileno(self) -> int:
            return int(self.stream.fileno())

        def read(self, size: int) -> bytes:
            if failure == "read":
                raise RuntimeError("synthetic read refusal")
            return bytes(self.stream.read(size))

    def attached(*args: Any, **kwargs: Any) -> Buffer:
        if failure == "fdopen":
            raise RuntimeError("synthetic stream attachment refusal")
        return Buffer(fdopen(*args, **kwargs))

    def inspected(descriptor: int) -> os.stat_result:
        if failure == "fstat" and descriptor in descriptors:
            raise RuntimeError("synthetic descriptor inspection refusal")
        return fstat(descriptor)

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "fdopen", attached)
    monkeypatch.setattr(os, "fstat", inspected)
    if failure == "success":
        assert receipts._read(source, 6) == b"native"
    else:
        with pytest.raises(RuntimeError, match="synthetic"):
            receipts._read(source, 6)
    assert len(descriptors) == 1
    for descriptor in descriptors:
        with pytest.raises(OSError):
            fstat(descriptor)
