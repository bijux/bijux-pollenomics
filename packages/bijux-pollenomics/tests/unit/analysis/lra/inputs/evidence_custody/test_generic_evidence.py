"""Generic evidence is a literal ordinary source, streamed under its own size."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
from tests.unit.analysis.lra.support import request_fixture


@pytest.mark.parametrize("kind", ["leaf_alias", "parent_alias", "hardlink", "fifo"])
def test_generic_evidence_refuses_aliased_or_nonregular_sources_before_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    payload = request_fixture(tmp_path)
    source = tmp_path / "raw_snapshot.txt"
    if kind == "leaf_alias":
        retained = tmp_path / "retained.txt"
        source.rename(retained)
        source.symlink_to(retained)
    elif kind == "parent_alias":
        parent = tmp_path / "physical"
        parent.mkdir()
        source.rename(parent / source.name)
        (tmp_path / "alias").symlink_to(parent, target_is_directory=True)
        payload["evidence"][0]["path"] = f"alias/{source.name}"
    elif kind == "hardlink":
        os.link(source, tmp_path / "second-owner.txt")
    else:
        source.unlink()
        os.mkfifo(source)
    real_open, real_os_open = Path.open, os.open
    attempted: list[Path] = []

    def opened(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.name == source.name:
            attempted.append(path)
            if kind == "fifo":
                raise OSError("Generated FIFO body must not be opened")
        return real_open(path, *args, **kwargs)

    def descriptor_opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if Path(path).name == source.name and not flags & os.O_DIRECTORY:
            attempted.append(Path(path))
            raise AssertionError("Invalid evidence reached a native body open")
        return real_os_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(Path, "open", opened)
    monkeypatch.setattr(os, "open", descriptor_opened)
    with pytest.raises(LRARefusal) as refused:
        validate_request(payload, input_root=tmp_path)
    assert refused.value.reason_code == "evidence_unavailable"
    assert attempted == []


@pytest.mark.parametrize("size", [0, 3 * 1024 * 1024 + 17])
def test_ordinary_evidence_streams_exact_pin_without_reading_siblings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, size: int
) -> None:
    payload = request_fixture(tmp_path)
    source = tmp_path / "raw_snapshot.txt"
    with source.open("wb") as stream:
        stream.truncate(size)
    digest = sha256()
    remaining = size
    while remaining:
        chunk = bytes(min(1024 * 1024, remaining))
        digest.update(chunk)
        remaining -= len(chunk)
    expected = digest.hexdigest()
    payload["evidence"][0]["sha256"] = expected
    os.mkfifo(tmp_path / "unselected-pipe")
    (tmp_path / "unselected-alias").symlink_to(source)
    real_open, real_read = os.open, os.read
    descriptors: list[int] = []
    reads: list[tuple[int, int]] = []

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = real_open(path, flags, *args, **kwargs)
        if Path(path).name == source.name and not flags & os.O_DIRECTORY:
            descriptors.append(descriptor)
        return descriptor

    def read(descriptor: int, count: int) -> bytes:
        raw = real_read(descriptor, count)
        if (
            descriptor in descriptors
            and os.fstat(descriptor).st_ino == source.stat().st_ino
        ):
            reads.append((count, len(raw)))
        return raw

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "read", read)
    accepted = validate_request(payload, input_root=tmp_path).payload()
    assert accepted["evidence"][0]["sha256"] == expected
    assert len(descriptors) == 1 and reads
    assert sum(actual for _, actual in reads) == size
    assert max(requested for requested, _ in reads) <= 1024 * 1024
    assert reads[-1][1] == 0
    with pytest.raises(OSError):
        os.fstat(descriptors[0])


@pytest.mark.parametrize("change", ["growth", "early_eof", "replacement"])
def test_actual_generic_fd_refuses_changed_source_and_closes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    payload = request_fixture(tmp_path)
    source = tmp_path / "raw_snapshot.txt"
    size = source.stat().st_size
    real_open, real_read = os.open, os.read
    descriptors: list[int] = []
    observed: list[int] = []
    events: list[str] = []

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = real_open(path, flags, *args, **kwargs)
        if Path(path).name == source.name and not flags & os.O_DIRECTORY:
            descriptors.append(descriptor)
        return descriptor

    def read(descriptor: int, count: int) -> bytes:
        if descriptor in descriptors:
            if not events:
                if change == "replacement":
                    source.rename(tmp_path / "retained-prior.txt")
                    source.write_bytes(b"B" * size)
                else:
                    with source.open("r+b") as stream:
                        stream.truncate(
                            size + 2 * 1024 * 1024 if change == "growth" else size - 5
                        )
                events.append(change)
            raw = real_read(descriptor, count)
            observed.append(len(raw))
            return raw
        return real_read(descriptor, count)

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "read", read)
    with pytest.raises(LRARefusal) as refused:
        validate_request(payload, input_root=tmp_path)
    assert refused.value.reason_code == "evidence_unavailable"
    assert events == [change] and len(descriptors) == 1
    assert sum(observed) <= size + 1
    with pytest.raises(OSError):
        os.fstat(descriptors[0])
