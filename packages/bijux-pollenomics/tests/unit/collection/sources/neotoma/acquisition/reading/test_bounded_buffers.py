"""File growth and pathname replacement cannot bypass native source byte bounds."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import os
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _object, _read


class ObservedBuffer:
    def __init__(
        self,
        stream: Any,
        reads: list[tuple[int, int]],
        before: Callable[[], None] | None = None,
        after: Callable[[], None] | None = None,
    ) -> None:
        self.stream, self.reads, self.before, self.after = stream, reads, before, after

    def __enter__(self) -> ObservedBuffer:
        return self

    def __exit__(self, *_: object) -> None:
        self.stream.close()

    def fileno(self) -> int:
        return cast(int, self.stream.fileno())

    def read(self, count: int = -1) -> bytes:
        if self.before is not None:
            self.before()
        value = cast(bytes, self.stream.read(count))
        self.reads.append((count, len(value)))
        if self.after is not None:
            self.after()
        return value


def observe(
    monkeypatch: pytest.MonkeyPatch,
    path: Path,
    *,
    before: Callable[[], None] | None = None,
    after: Callable[[], None] | None = None,
) -> list[tuple[int, int]]:
    opening = Path.open
    reads: list[tuple[int, int]] = []

    def opened(candidate: Path, *args: Any, **kwargs: Any) -> Any:
        stream = opening(candidate, *args, **kwargs)
        if candidate == path and (
            args and args[0] == "rb" or kwargs.get("mode") == "rb"
        ):
            return ObservedBuffer(stream, reads, before, after)
        return stream

    monkeypatch.setattr(Path, "open", opened)
    return reads


@pytest.mark.parametrize("bound", [0, 16])
def test_actual_open_growth_reads_one_sentinel_then_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bound: int
) -> None:
    path = tmp_path / "source.body"
    path.write_bytes(b"" if bound == 0 else b"{}")

    def grow() -> None:
        with path.open("ab") as stream:
            stream.write(b" " * 8192)

    reads = observe(monkeypatch, path, before=grow)
    with pytest.raises(ValueError, match="bound|grew"):
        _read(path, bound)
    assert reads == [(bound + 1, bound + 1)]


@pytest.mark.parametrize("body", [b"", b"native\r\nbytes\x00\xff", b'{"value":1}'])
def test_exact_cap_preserves_the_single_literal_buffer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: bytes
) -> None:
    path = tmp_path / "source.body"
    path.write_bytes(body)
    reads = observe(monkeypatch, path)
    assert _read(path, len(body)) == body
    assert reads == [(len(body) + 1, len(body))]


@pytest.mark.parametrize("bound", [True, False, -1, 0.0, 1.5, "16", None])
def test_invalid_native_byte_bound_refuses_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bound: Any
) -> None:
    path = tmp_path / "source.body"
    path.write_bytes(b"")

    def never(*_: Any, **__: Any) -> Any:
        pytest.fail("Invalid native byte bound opened source input")

    monkeypatch.setattr(Path, "open", never)
    with pytest.raises(ValueError, match="bound"):
        _read(path, bound)


@pytest.mark.parametrize(
    "kind", ["oversize", "symlink", "directory", "missing", "fifo"]
)
def test_nonregular_or_oversize_input_refuses_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    path = tmp_path / "source.body"
    if kind == "oversize":
        path.write_bytes(b"123")
    elif kind == "symlink":
        target = tmp_path / "target.body"
        target.write_bytes(b"12")
        path.symlink_to(target)
    elif kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path)
    reads = observe(monkeypatch, path)
    with pytest.raises(ValueError):
        _read(path, 2)
    assert reads == []


def test_opened_inode_replacement_refuses_before_any_buffer_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "source.body"
    path.write_bytes(b"owned")
    other = tmp_path / "foreign.body"
    other.write_bytes(b"other")
    opening = Path.open
    reads: list[tuple[int, int]] = []

    def switched(candidate: Path, *args: Any, **kwargs: Any) -> Any:
        if candidate == path:
            path.rename(tmp_path / "original.body")
            other.rename(path)
            return ObservedBuffer(opening(path, *args, **kwargs), reads)
        return opening(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "open", switched)
    with pytest.raises(ValueError, match="identity|changed"):
        _read(path, 5)
    assert reads == []


def test_hardlinked_source_inputs_remain_byte_compatible(tmp_path: Path) -> None:
    original, alias = tmp_path / "original.body", tmp_path / "alias.body"
    original.write_bytes(b"native source")
    os.link(original, alias)
    assert original.stat().st_nlink == 2
    assert _read(alias, 13) == b"native source"


def test_digest_and_native_json_use_the_same_returned_buffer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "source.body"
    integer = 10**1000
    body = b'{"value":' + str(integer).encode() + b"}\r\n"
    path.write_bytes(body)

    def change_after_read() -> None:
        path.write_bytes(b'{"value":0}')

    reads = observe(monkeypatch, path, after=change_after_read)
    raw = _read(path, len(body))
    assert sha256(raw).hexdigest() == sha256(body).hexdigest()
    parsed = _object(raw)
    assert type(parsed["value"]) is int and parsed["value"] == integer
    assert reads == [(len(body) + 1, len(body))]
    assert path.stat().st_size < len(body)
