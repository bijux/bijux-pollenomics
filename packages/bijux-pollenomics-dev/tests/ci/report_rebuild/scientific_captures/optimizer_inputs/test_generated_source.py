"""Keep generated-source correspondence scoped to the original declared member."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_development import (
    admission as subject,
)


def test_generated_source_uses_only_the_authenticated_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = b"x" * 539
    checksum = hashlib.sha256(raw).hexdigest()
    calls: list[tuple[Path, str]] = []

    def source(repository: Path, member: str) -> bytes:
        calls.append((repository, member))
        return raw

    monkeypatch.setattr(subject, "RUNTIME_SHA256", checksum)
    monkeypatch.setattr(subject, "read_source_path", source)
    current = tmp_path / subject.RUNTIME_SOURCE
    current.parent.mkdir(parents=True)
    current.write_bytes(b"unrelated-current-version")
    assert subject._read(tmp_path, subject.RUNTIME_SOURCE, checksum, 539) == raw
    assert calls == [(tmp_path, subject.RUNTIME_CAPTURE_MEMBER)]
    assert current.read_bytes() == b"unrelated-current-version"


@pytest.mark.parametrize(
    ("checksum", "size"),
    [("0" * 64, 539), (subject.RUNTIME_SHA256, 538), (subject.RUNTIME_SHA256, True)],
)
def test_wrong_generated_identity_refuses_before_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, checksum: str, size: int
) -> None:
    def source(_repository: Path, _member: str) -> bytes:
        raise AssertionError("Invalid source identity reached transport")

    monkeypatch.setattr(subject, "read_source_path", source)
    with pytest.raises(ReportRebuildError, match="generated source identity"):
        subject._read(tmp_path, subject.RUNTIME_SOURCE, checksum, size)


@pytest.mark.parametrize("raw", [b"x" * 538, b"x" * 539])
def test_changed_generated_body_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: bytes
) -> None:
    monkeypatch.setattr(subject, "read_source_path", lambda _repository, _member: raw)
    with pytest.raises(ReportRebuildError, match="generated source bytes"):
        subject._read(tmp_path, subject.RUNTIME_SOURCE, subject.RUNTIME_SHA256, 539)


def test_other_source_paths_keep_the_physical_identity_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def source(_repository: Path, _member: str) -> bytes:
        raise AssertionError("Ordinary source path reached generated transport")

    monkeypatch.setattr(subject, "read_source_path", source)
    raw = b"constructed-ordinary-source"
    (tmp_path / "source.py").write_bytes(raw)
    checksum = hashlib.sha256(raw).hexdigest()
    assert subject._read(tmp_path, "source.py", checksum, len(raw)) == raw
    with pytest.raises(ReportRebuildError):
        subject._read(tmp_path, "source.py", "0" * 64, len(raw))
