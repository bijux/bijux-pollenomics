"""Transport preserves exact registered bytes without generic data fallbacks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.lra_validation.native_reference import (
    diagnostics_verification as review,
)
from bijux_pollenomics_dev.lra_validation.native_reference.source_layout_adoption import (
    API_PATH,
)


@pytest.mark.parametrize("relative", sorted(review._REGISTERED_GIT_INPUTS))
def test_registered_member_uses_exact_getter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: str
) -> None:
    calls: list[tuple[Path, str]] = []

    def read(root: Path, member: str) -> bytes:
        calls.append((root, member))
        return b"registered original member"

    monkeypatch.setattr(review, "read_source_path", read)
    assert review._raw(tmp_path, relative) == b"registered original member"
    assert calls == [(tmp_path, relative)]
    assert not (tmp_path / relative).exists()


def test_preimage_uses_two_argument_api_witness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[Path, Path]] = []

    def read(root: Path, api: Path) -> bytes:
        calls.append((root, api))
        return b"historical public API"

    monkeypatch.setattr(review, "api_adoption_preimage", read)
    assert (
        review._raw(tmp_path, review._HISTORICAL_API_PREIMAGE)
        == b"historical public API"
    )
    assert calls == [(tmp_path, tmp_path / API_PATH)]


@pytest.mark.parametrize(
    "error", [OSError("missing"), ReportRebuildError("wrong custody")]
)
def test_registered_failure_cannot_fall_back_to_physical_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    member = min(review._REGISTERED_GIT_INPUTS)
    current = tmp_path / member
    current.parent.mkdir(parents=True)
    current.write_bytes(b"physical alias is not a historical witness")

    def read(*args: Any) -> bytes:
        raise error

    monkeypatch.setattr(review, "read_source_path", read)
    with pytest.raises(ValueError, match="Registered retained input custody differs"):
        review._raw(tmp_path, member)


@pytest.mark.parametrize("relative", ["/absolute", "../outside", "data/../outside"])
def test_unconfined_member_refuses_before_getter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: str
) -> None:
    def forbidden(*args: Any) -> bytes:
        pytest.fail("unconfined paths cannot reach registered getters")

    monkeypatch.setattr(review, "read_source_path", forbidden)
    with pytest.raises(ValueError, match="Confined retained path required"):
        review._raw(tmp_path, relative)


def test_unregistered_data_remains_strictly_physical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: Any) -> bytes:
        pytest.fail("unregistered data cannot use a generic retained-source fallback")

    monkeypatch.setattr(review, "read_source_path", forbidden)
    path = tmp_path / "data/ordinary.json"
    path.parent.mkdir()
    path.write_bytes(b"ordinary retained metadata")
    assert review._raw(tmp_path, "data/ordinary.json") == b"ordinary retained metadata"
    with pytest.raises(FileNotFoundError):
        review._raw(tmp_path, "data/missing.json")
    alias = path.parent / "alias.json"
    alias.symlink_to(path)
    with pytest.raises(ValueError, match="Retained path alias refused"):
        review._raw(tmp_path, "data/alias.json")
