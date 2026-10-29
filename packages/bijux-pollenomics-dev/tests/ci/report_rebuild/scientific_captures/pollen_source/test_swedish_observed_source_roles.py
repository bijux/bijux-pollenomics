"""Check the observed Swedish source caller with confined own-string inputs."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source import (
    swedish_direct_pollen as subject,
)

NAME = "packages/example/reviewed.py"
LOGICAL = "original-source/source/" + NAME


def _pin(raw: bytes) -> JsonObject:
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def _source(repository: Path, raw: bytes) -> Path:
    path = repository / NAME
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    return path


def _capsule(expected: JsonObject) -> SourceCapsule:
    return cast(
        SourceCapsule,
        SimpleNamespace(
            detached={LOGICAL},
            descriptor=SimpleNamespace(members={LOGICAL: expected}),
        ),
    )


def test_exact_observed_source_keeps_the_strict_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Accept exact source bytes without asking for a historical role."""
    raw = b"literal owned test source\n"
    _source(tmp_path, raw)

    def refuse_role(*args: object) -> None:
        raise AssertionError("Exact source must not borrow a role")

    monkeypatch.setattr(subject, "validated_current_scientific_source", refuse_role)
    assert (
        subject._observed_source_correspondence(
            tmp_path, NAME, _pin(raw), _capsule(_pin(raw))
        )
        is None
    )


def test_changed_observed_source_binds_the_exact_existing_router_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pass the original logical owner and pin to the maintained role router."""
    _source(tmp_path, b"current own test source\n")
    expected = _pin(b"historical own test source\n")
    capsule = _capsule(expected)
    role: JsonObject = {"kind": "reviewed_test_role"}
    calls: list[tuple[Path, JsonObject, str, SourceCapsule]] = []

    def router(
        repository: Path, reference: JsonObject, logical: str, supplied: SourceCapsule
    ) -> JsonObject:
        calls.append((repository, reference, logical, supplied))
        return role

    monkeypatch.setattr(subject, "validated_current_scientific_source", router)
    assert (
        subject._observed_source_correspondence(tmp_path, NAME, expected, capsule)
        is role
    )
    assert calls == [(tmp_path, {"path": NAME, **expected}, LOGICAL, capsule)]


@pytest.mark.parametrize("fault", ["missing_detached", "wrong_bytes", "wrong_sha"])
def test_changed_source_refuses_missing_or_mismatched_historical_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    """Reject missing or altered detached identity before calling the router."""
    _source(tmp_path, b"current own test source\n")
    expected = _pin(b"historical own test source\n")
    declared = dict(expected)
    detached = {LOGICAL}
    if fault == "missing_detached":
        detached = set()
    elif fault == "wrong_bytes":
        byte_count = declared["bytes"]
        assert isinstance(byte_count, int)
        declared["bytes"] = byte_count + 1
    else:
        declared["sha256"] = "0" * 64
    capsule = cast(
        SourceCapsule,
        SimpleNamespace(
            detached=detached, descriptor=SimpleNamespace(members={LOGICAL: declared})
        ),
    )

    def refuse_role(*args: object) -> None:
        raise AssertionError("Invalid authority must fail before role lookup")

    monkeypatch.setattr(subject, "validated_current_scientific_source", refuse_role)
    with pytest.raises(ReportRebuildError):
        subject._observed_source_correspondence(tmp_path, NAME, expected, capsule)


def test_changed_source_without_a_reviewed_role_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep unknown current source changes outside the finite role policy."""
    _source(tmp_path, b"current own test source\n")
    expected = _pin(b"historical own test source\n")

    def unknown_role(*args: object) -> None:
        return None

    monkeypatch.setattr(subject, "validated_current_scientific_source", unknown_role)
    with pytest.raises(ReportRebuildError, match="Reviewed source correspondence"):
        subject._observed_source_correspondence(
            tmp_path, NAME, expected, _capsule(expected)
        )


@pytest.mark.parametrize("kind", ["missing", "symlink", "hardlink"])
def test_observed_source_requires_a_confined_regular_single_link_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """Reject physical identity defects before either equality or role admission."""
    expected = _pin(b"own test source\n")
    path = tmp_path / NAME
    path.parent.mkdir(parents=True)
    if kind != "missing":
        target = tmp_path / "owned-source.txt"
        target.write_bytes(b"own test source\n")
        if kind == "symlink":
            path.symlink_to(target)
        else:
            os.link(target, path)

    def refuse_role(*args: object) -> None:
        raise AssertionError("Physical defects must fail before role lookup")

    monkeypatch.setattr(subject, "validated_current_scientific_source", refuse_role)
    with pytest.raises((ReportRebuildError, ReportOwnershipError)):
        subject._observed_source_correspondence(
            tmp_path, NAME, expected, _capsule(expected)
        )
