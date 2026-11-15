"""Body-open proofs observe the secure descriptor, not a simulated trace."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import receipts
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)


def test_source_and_direct_readers_preserve_their_actual_open_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "selected.body"
    source.write_bytes(b"literal")
    opening, descriptor_open = capture_opening(), os.open
    observed: list[Path] = []
    actual: list[tuple[Path, int]] = []

    def descriptor(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        actual.append((Path(path), flags))
        return descriptor_open(path, flags, *args, **kwargs)

    def counted(path: Path, *args: Any, **kwargs: Any) -> Any:
        observed.append(path)
        return opening(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", descriptor)
    observe_opening(monkeypatch, counted)
    assert receipts._read(source, 7) == b"literal"
    assert source.read_bytes() == b"literal"
    assert observed == [source, source]
    assert [path for path, _ in actual] == [source]
    assert all(flags & os.O_NOFOLLOW and flags & os.O_NONBLOCK for _, flags in actual)


def test_direct_pathname_symlink_keeps_its_unobserved_read_behavior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, alias = tmp_path / "source.body", tmp_path / "alias.body"
    source.write_bytes(b"literal")
    alias.symlink_to(source)
    expected = alias.read_bytes()
    opening = capture_opening()
    observed: list[Path] = []

    def counted(path: Path, *args: Any, **kwargs: Any) -> Any:
        observed.append(path)
        return opening(path, *args, **kwargs)

    observe_opening(monkeypatch, counted)
    assert alias.read_bytes() == expected
    assert observed == [alias]


@pytest.mark.parametrize("refuse", [False, True])
def test_nested_pathname_reads_and_callback_errors_preserve_each_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, refuse: bool
) -> None:
    source, alias = tmp_path / "source.body", tmp_path / "alias.body"
    source.write_bytes(b"literal")
    alias.symlink_to(source)
    opening, descriptor_open = capture_opening(), os.open
    observed: list[Path] = []
    actual: list[Path] = []

    def descriptor(path: Any, *args: Any, **kwargs: Any) -> int:
        actual.append(Path(path))
        return descriptor_open(path, *args, **kwargs)

    def counted(path: Path, *args: Any, **kwargs: Any) -> Any:
        observed.append(path)
        if path == source:
            assert alias.read_bytes() == b"literal"
            if refuse:
                raise RuntimeError("synthetic observer refusal")
        return opening(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", descriptor)
    observe_opening(monkeypatch, counted)
    if refuse:
        with pytest.raises(RuntimeError, match="synthetic observer refusal"):
            receipts._read(source, 7)
    else:
        assert receipts._read(source, 7) == b"literal"
    assert alias.read_bytes() == b"literal"
    assert observed == [source, alias, alias]
    assert actual == ([] if refuse else [source])


def test_forbidden_body_guard_refuses_before_real_descriptor_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "sibling.body"
    source.write_bytes(b"private")
    descriptors: list[Any] = []
    opening = os.open

    def descriptor(*args: Any, **kwargs: Any) -> int:
        descriptors.append(args)
        return opening(*args, **kwargs)

    def forbidden(path: Path, *_: Any, **__: Any) -> Any:
        raise AssertionError(f"Forbidden source body: {path.name}")

    monkeypatch.setattr(os, "open", descriptor)
    observe_opening(monkeypatch, forbidden)
    with pytest.raises(AssertionError, match="Forbidden source body"):
        receipts._read(source, 7)
    assert descriptors == []


def test_observer_does_not_reopen_a_substituted_symlink_by_pathname(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, foreign = tmp_path / "selected.body", tmp_path / "foreign.body"
    source.write_bytes(b"owned")
    foreign.write_bytes(b"other")
    opening = capture_opening()
    observed: list[Path] = []

    def substituted(path: Path, *args: Any, **kwargs: Any) -> Any:
        observed.append(path)
        source.unlink()
        source.symlink_to(foreign)
        return opening(path, *args, **kwargs)

    observe_opening(monkeypatch, substituted)
    with pytest.raises(ValueError, match="regular|bounded"):
        receipts._read(source, 5)
    assert observed == [source]


def test_stream_observation_wraps_the_actual_fd_and_single_bounded_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "selected.body"
    source.write_bytes(b"native")
    opening = capture_opening()
    reads: list[tuple[int, int]] = []
    descriptors: list[int] = []

    class Buffer:
        def __init__(self, stream: Any) -> None:
            self.stream = stream
            descriptors.append(stream.fileno())

        def __enter__(self) -> Buffer:
            return self

        def __exit__(self, *_: Any) -> None:
            self.stream.close()

        def fileno(self) -> int:
            return int(self.stream.fileno())

        def read(self, bound: int) -> bytes:
            raw = bytes(self.stream.read(bound))
            reads.append((bound, len(raw)))
            return raw

    observe_opening(monkeypatch, lambda path, *a, **k: Buffer(opening(path, *a, **k)))
    assert receipts._read(source, 6) == b"native"
    assert reads == [(7, 6)]
    assert len(descriptors) == 1
    with pytest.raises(OSError):
        os.fstat(descriptors[0])
