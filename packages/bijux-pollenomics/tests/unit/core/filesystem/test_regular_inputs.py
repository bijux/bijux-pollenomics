"""Bounded input trees count unique source bytes and read actual opened files."""

import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.core.filesystem.regular_inputs import BoundedInputTree


def test_aggregate_and_member_limits_precede_buffering(tmp_path: Path) -> None:
    (tmp_path / "a").write_bytes(b"123")
    (tmp_path / "b").write_bytes(b"456")
    with pytest.raises(ValueError, match="budget|bound"):
        BoundedInputTree(tmp_path, max_bytes=5, max_files=2)
    with pytest.raises(ValueError, match="budget|bound"):
        BoundedInputTree(tmp_path, max_bytes=6, max_files=1)
    with BoundedInputTree(tmp_path, max_bytes=6, max_files=2) as tree:
        assert tree.read(tmp_path / "a") == b"123"
        assert tree.read(tmp_path / "a") == b"123"
        assert tree.read(tmp_path / "b") == b"456"
        tree.validate()


def test_actual_growth_reads_only_declared_bytes_and_sentinel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "body"
    source.write_bytes(b"x")
    with BoundedInputTree(tmp_path, max_bytes=3, max_files=1) as tree:
        original = os.read
        calls: list[tuple[int, int]] = []

        def growing(descriptor: int, size: int) -> bytes:
            source.write_bytes(b"x" * 10000)
            result = original(descriptor, size)
            calls.append((size, len(result)))
            return result

        monkeypatch.setattr(os, "read", growing)
        with pytest.raises(ValueError, match="growth|bound|changed"):
            tree.read(source)
        assert calls == [(2, 2)]


def test_substituted_fifo_opens_nonblocking_and_closes_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "body"
    source.write_bytes(b"x")
    opening = os.open
    descriptors: list[int] = []
    with BoundedInputTree(tmp_path, max_bytes=1, max_files=1) as tree:

        def fifo(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
            if str(path) == "body":
                source.unlink()
                os.mkfifo(source)
            result = opening(path, flags, *args, **kwargs)
            if str(path) == "body":
                assert flags & os.O_NONBLOCK
                descriptors.append(result)
            return result

        monkeypatch.setattr(os, "open", fifo)
        with pytest.raises(ValueError, match="regular|changed|identity"):
            tree.read(source)
    assert len(descriptors) == 1
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)


def test_dependency_seam_receives_exact_verified_buffer_with_one_real_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.core.filesystem.regular_inputs import read_regular_file

    source = tmp_path / "body"
    source.write_bytes(b"source")
    opening = os.open
    actual: list[int] = []

    def counted(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = opening(path, flags, *args, **kwargs)
        if str(path) == "body":
            actual.append(descriptor)
        return descriptor

    with BoundedInputTree(tmp_path, max_bytes=6, max_files=1) as tree:
        monkeypatch.setattr(os, "open", counted)
        assert (
            tree.read_with(source, lambda path: read_regular_file(path, max_bytes=6))
            == b"source"
        )
    assert len(actual) == 1
    with pytest.raises(OSError):
        os.fstat(actual[0])


def test_input_digest_pin_survives_a_legal_size_rewrite(tmp_path: Path) -> None:
    source = tmp_path / "body"
    source.write_bytes(b"owned")
    with BoundedInputTree(tmp_path, max_bytes=5, max_files=1) as tree:
        assert tree.read(source) == b"owned"
        source.write_bytes(b"other")
        with pytest.raises(ValueError, match="identity|changed"):
            tree.read(source)


def test_copied_callback_context_cannot_reuse_a_completed_verified_buffer(
    tmp_path: Path,
) -> None:
    from contextvars import copy_context

    from bijux_pollenomics.core.filesystem.regular_inputs import read_regular_file

    source = tmp_path / "body"
    source.write_bytes(b"first")
    contexts = []
    with BoundedInputTree(tmp_path, max_bytes=5, max_files=1) as tree:

        def callback(path: Path) -> bytes:
            contexts.append(copy_context())
            return read_regular_file(path, max_bytes=5)

        assert tree.read_with(source, callback) == b"first"
    source.write_bytes(b"other")
    assert contexts[0].run(read_regular_file, source, max_bytes=5) == b"other"
