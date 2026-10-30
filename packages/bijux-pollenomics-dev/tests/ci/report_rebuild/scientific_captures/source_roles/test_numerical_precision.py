"""Refuse changes beyond the bounded Hellinger precision source correspondence."""

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
    numerical_precision as source,
)

Case = tuple[Path, dict[str, Any], str, Any, Path]


def _texts() -> tuple[bytes, bytes]:
    """Invent only a module prefix/suffix around the two reviewed expression spans."""
    before = b"# invented module header\n" + source._OLD_RETURN + b"\n# invented tail\n"
    after = b"# invented module header\n" + source._NEW_RETURN + b"\n# invented tail\n"
    return before, after


@pytest.fixture(params=tuple(source._QUALIFIED_CAPTURES))
def bound_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Case:
    """Bind own bytes to each real capture coordinate without copying a source file."""
    old, current = _texts()
    checksum = hashlib.sha256(old).hexdigest()
    monkeypatch.setattr(source, "_HISTORICAL_SHA256", checksum)
    monkeypatch.setattr(source, "_HISTORICAL_BYTES", len(old))
    prefix = str(request.param)
    capture_sha, logical_prefix = source._QUALIFIED_CAPTURES[prefix]
    logical = logical_prefix + source.METRICS_SOURCE
    identity = {"sha256": checksum, "bytes": len(old)}
    descriptor = SimpleNamespace(
        capture={"sha256": capture_sha},
        members={logical: identity},
        groups=[{"resolved_paths": [(logical, source.METRICS_SOURCE)]}],
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
    path = tmp_path / source.METRICS_SOURCE
    path.parent.mkdir(parents=True)
    path.write_bytes(current)
    return (
        tmp_path,
        {"path": source.METRICS_SOURCE, **identity},
        logical,
        resolver,
        path,
    )


def _check(case: Case) -> dict[str, Any]:
    """Call the real maintained source-role boundary with the constructed resolver."""
    return source.validated_hellinger_precision_source(*case[:4])


def test_declared_capture_keeps_dated_math_scope(bound_case: Case) -> None:
    result = _check(bound_case)
    assert result["classification"] == "finite_hellinger_precision_extension"
    assert result["whole_old_module_reconstructed"] is True
    assert result["historical_numeric_outputs_regenerated"] is False
    assert result["historical_native_software_equal_current_claimed"] is False
    assert result["saved_output_equality_from_source_law_claimed"] is False


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
        logical = "source/" + source.METRICS_SOURCE
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
        source.validated_hellinger_precision_source(root, identity, logical, resolver)


@pytest.mark.parametrize(
    "damage",
    ["prefix", "suffix", "expression", "comment", "duplicate", "missing", "old_body"],
)
def test_full_module_inverse_rejects_every_undeclared_byte(
    monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    old, current = _texts()
    monkeypatch.setattr(source, "_HISTORICAL_SHA256", hashlib.sha256(old).hexdigest())
    monkeypatch.setattr(source, "_HISTORICAL_BYTES", len(old))
    assert source.hellinger_precision_extension_matches(old, current)
    if damage == "prefix":
        current = b"# added import/default/decorator\n" + current
    elif damage == "suffix":
        current += b"# unrelated statement\n"
    elif damage == "expression":
        current = current.replace(b"hypot(", b"unreviewed(")
    elif damage == "comment":
        current = current.replace(b"Rationalize", b"Different")
    elif damage == "duplicate":
        current += source._NEW_RETURN
    elif damage == "missing":
        current = current.replace(source._NEW_RETURN, b"return 0")
    else:
        old += b"# wrong captured source\n"
    assert not source.hellinger_precision_extension_matches(old, current)
