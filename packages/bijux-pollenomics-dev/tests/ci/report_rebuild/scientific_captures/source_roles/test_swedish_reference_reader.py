"""Keep the Swedish reference-reader extension within its three metadata spans."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    readers as source,
)

Case = tuple[Path, dict[str, Any], str, Any, Path]


def _texts() -> tuple[bytes, bytes]:
    """Invent module boundaries around only the three reviewed metadata spans."""
    gap = b"\n# own separator\n"
    old = gap.join(pair[0] for pair in source._SWEDISH_REFERENCE_READER_SPANS)
    current = gap.join(pair[1] for pair in source._SWEDISH_REFERENCE_READER_SPANS)
    return b"# header\n" + old + b"# tail\n", b"# header\n" + current + b"# tail\n"


@pytest.fixture
def bound_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Case:
    """Bind own bytes to each real capture coordinate without copying a source file."""
    old, current = _texts()
    checksum = hashlib.sha256(old).hexdigest()
    monkeypatch.setattr(source, "_SWEDISH_REFERENCE_READER_SHA256", checksum)
    monkeypatch.setattr(source, "_SWEDISH_REFERENCE_READER_BYTES", len(old))
    prefix = "data/method-certification/author-optimizer-diagnostic-source-capture"
    capture_sha = "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93"
    logical_prefix = "executions/optimizer-diagnostics/first-party-inputs/"
    logical = logical_prefix + source.SWEDISH_REFERENCE_READER_SOURCE
    identity = {"sha256": checksum, "bytes": len(old)}
    descriptor = SimpleNamespace(
        capture={"sha256": capture_sha},
        members={logical: identity},
        groups=[
            {"resolved_paths": [(logical, source.SWEDISH_REFERENCE_READER_SOURCE)]}
        ],
    )

    def read(selected: str) -> bytes:
        assert selected == logical
        return old

    resolver = SimpleNamespace(
        repository=tmp_path,
        prefix=prefix,
        descriptor=descriptor,
        detached=frozenset({logical}),
        fresh=lambda: None,
        read_source=read,
    )
    path = tmp_path / source.SWEDISH_REFERENCE_READER_SOURCE
    path.parent.mkdir(parents=True)
    path.write_bytes(current)
    return (
        tmp_path,
        {"path": source.SWEDISH_REFERENCE_READER_SOURCE, **identity},
        logical,
        resolver,
        path,
    )


def _check(case: Case) -> dict[str, Any]:
    """Call the real maintained source-role boundary with the constructed resolver."""
    return source.validated_swedish_reference_reader_source(*case[:4])


def test_declared_optimizer_context_keeps_reference_scope(bound_case: Case) -> None:
    result = _check(bound_case)
    assert result["classification"] == "finite_swedish_reference_reader_extension"
    assert result["whole_old_reader_reconstructed"] is True
    assert result["original_nine_capture_pins_preserved"] is True
    assert (
        result["current_additional_reference_record_requires_separate_qualification"]
        is True
    )
    assert result["current_native_or_numerical_equivalence_claimed"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "unqualified_capture",
        "capture_sha",
        "repository",
        "logical",
        "detached",
        "resolved_path",
        "duplicate_mapping",
        "member_identity",
        "historical_path",
        "historical_size",
        "boolean_size",
        "extra_identity_key",
        "current_body",
        "concurrent_change",
        "symlink",
        "ancestor_symlink",
        "hardlink",
    ],
)
def test_capture_binding_and_current_custody_refuse(
    bound_case: Case, damage: str, tmp_path: Path
) -> None:
    root, identity, logical, resolver, path = bound_case
    if damage == "unqualified_capture":
        resolver.prefix = "data/unqualified-capture"
    elif damage == "capture_sha":
        resolver.descriptor.capture["sha256"] = "0" * 64
    elif damage == "repository":
        resolver.repository = tmp_path / "other"
    elif damage == "logical":
        logical = "source/" + source.SWEDISH_REFERENCE_READER_SOURCE
    elif damage == "detached":
        resolver.detached = frozenset()
    elif damage == "resolved_path":
        resolver.descriptor.groups[0]["resolved_paths"] = [(logical, "foreign.py")]
    elif damage == "duplicate_mapping":
        resolver.descriptor.groups.append(resolver.descriptor.groups[0])
    elif damage == "member_identity":
        resolver.descriptor.members[logical] = {"sha256": "0" * 64, "bytes": 0}
    elif damage == "historical_path":
        identity["path"] = "packages/foreign.py"
    elif damage == "historical_size":
        identity["bytes"] += 1
    elif damage == "boolean_size":
        identity["bytes"] = True
    elif damage == "extra_identity_key":
        identity["unreviewed"] = True
    elif damage == "current_body":
        path.write_bytes(path.read_bytes() + b"# unrelated current change\n")
    elif damage == "concurrent_change":
        calls = 0

        def changed() -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                path.write_bytes(path.read_bytes() + b"# concurrent change\n")

        resolver.fresh = changed
    elif damage == "hardlink":
        os.link(path, tmp_path / "second.py")
    elif damage == "symlink":
        outside = tmp_path / "outside.py"
        path.rename(outside)
        path.symlink_to(outside)
    else:
        outside = path.parent.with_name(path.parent.name + "-outside")
        path.parent.rename(outside)
        path.parent.symlink_to(outside, target_is_directory=True)
    expected = (
        ReportOwnershipError
        if damage in {"symlink", "ancestor_symlink"}
        else ReportRebuildError
    )
    with pytest.raises(expected):
        source.validated_swedish_reference_reader_source(
            root, identity, logical, resolver
        )


@pytest.mark.parametrize(
    "damage",
    ["prefix", "suffix", "span-0", "span-1", "span-2", "duplicate", "old_body"],
)
def test_full_reader_inverse_rejects_every_undeclared_byte(
    monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    old, current = _texts()
    monkeypatch.setattr(
        source, "_SWEDISH_REFERENCE_READER_SHA256", hashlib.sha256(old).hexdigest()
    )
    monkeypatch.setattr(source, "_SWEDISH_REFERENCE_READER_BYTES", len(old))
    assert source.swedish_reference_reader_extension_matches(old, current)
    if damage == "prefix":
        current = b"# added import/default/decorator\n" + current
    elif damage == "suffix":
        current += b"# unrelated statement\n"
    elif damage.startswith("span-"):
        index = int(damage.removeprefix("span-"))
        current = current.replace(
            source._SWEDISH_REFERENCE_READER_SPANS[index][1], b"# unreviewed metadata\n"
        )
    elif damage == "duplicate":
        current += source._SWEDISH_REFERENCE_READER_SPANS[0][1]
    else:
        old += b"# wrong captured source\n"
    assert not source.swedish_reference_reader_extension_matches(old, current)
