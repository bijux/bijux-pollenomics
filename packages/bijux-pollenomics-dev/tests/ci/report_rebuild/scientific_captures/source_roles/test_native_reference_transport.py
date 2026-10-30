"""Keep native reference transports bound to their original source evidence."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    source_correspondence as router,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    native_reference_transport as source,
)

Case = tuple[Path, dict[str, Any], str, Any, Path]
NAME = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/capture.py"
OLD = b"# own header\nsource = physical()\n# own suffix\n"
NEW = b"# own header\nsource = authenticated()\n# own suffix\n"


def _own_contract() -> tuple[int, str, tuple[tuple[bytes, bytes], ...]]:
    """Describe a tiny invented retrieval span, without copying package source."""
    return (
        len(OLD),
        hashlib.sha256(OLD).hexdigest(),
        ((b"source = physical()", b"source = authenticated()"),),
    )


@pytest.fixture(params=tuple(source._NATIVE_REFERENCE_TRANSPORT_CAPTURES))
def bound_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Case:
    """Exercise each real capture coordinate with own bytes and a resolver spy."""
    monkeypatch.setattr(
        source, "_NATIVE_REFERENCE_TRANSPORT_CONTRACTS", {NAME: _own_contract()}
    )
    prefix = str(request.param)
    capture_sha, logical_prefix = source._NATIVE_REFERENCE_TRANSPORT_CAPTURES[prefix]
    logical = logical_prefix + NAME
    identity = {"sha256": hashlib.sha256(OLD).hexdigest(), "bytes": len(OLD)}
    descriptor = SimpleNamespace(
        capture={"sha256": capture_sha},
        members={logical: identity},
        groups=[{"resolved_paths": [(logical, NAME)]}],
    )

    def read(selected: str) -> bytes:
        assert selected == logical
        return OLD

    resolver = SimpleNamespace(
        repository=tmp_path,
        prefix=prefix,
        descriptor=descriptor,
        detached=frozenset({logical}),
        fresh=lambda: None,
        read_source=read,
    )
    path = tmp_path / NAME
    path.parent.mkdir(parents=True)
    path.write_bytes(NEW)
    return tmp_path, {"path": NAME, **identity}, logical, resolver, path


def test_declared_native_transport_retains_dated_execution(bound_case: Case) -> None:
    """Use the actual central dispatcher, with explicit scope rather than a postimage."""
    role = router.validated_current_scientific_source(*bound_case[:4])
    assert role is not None
    assert role["classification"] == "finite_native_reference_transport_extension"
    assert role["whole_old_module_reconstructed"] is True
    assert role["native_math_runtime_and_count_predicates_preserved"] is True
    assert role["historical_native_execution_equal_current_claimed"] is False
    assert role["historical_outputs_regenerated"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "capture",
        "capture_sha",
        "repository",
        "logical",
        "detached",
        "member",
        "resolved_path",
        "duplicate_path",
        "historical_path",
        "boolean_size",
        "extra_key",
        "captured_bytes",
        "current_body",
        "concurrent_body",
        "symlink",
        "ancestor_symlink",
        "hardlink",
    ],
)
def test_native_transport_custody_refusals(
    bound_case: Case, damage: str, tmp_path: Path
) -> None:
    """Reject identity substitution, unreviewed changes, links and changing files."""
    root, identity, logical, resolver, path = bound_case
    if damage == "capture":
        resolver.prefix = "data/unqualified-capture"
    elif damage == "capture_sha":
        resolver.descriptor.capture["sha256"] = "0" * 64
    elif damage == "repository":
        resolver.repository = tmp_path / "other"
    elif damage == "logical":
        logical += "/other"
    elif damage == "detached":
        resolver.detached = frozenset()
    elif damage == "member":
        resolver.descriptor.members[logical] = {"bytes": 0, "sha256": "0" * 64}
    elif damage == "resolved_path":
        resolver.descriptor.groups[0]["resolved_paths"] = [(logical, "foreign.py")]
    elif damage == "duplicate_path":
        resolver.descriptor.groups.append(resolver.descriptor.groups[0])
    elif damage == "historical_path":
        identity["path"] = "packages/foreign.py"
    elif damage == "boolean_size":
        identity["bytes"] = True
    elif damage == "extra_key":
        identity["other"] = True
    elif damage == "captured_bytes":
        resolver.read_source = lambda _: OLD + b"# changed\n"
    elif damage == "current_body":
        path.write_bytes(NEW + b"# changed clause\n")
    elif damage == "concurrent_body":
        calls = 0

        def changing() -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                path.write_bytes(NEW + b"# concurrent\n")

        resolver.fresh = changing
    elif damage == "symlink":
        outside = tmp_path / "outside.py"
        path.rename(outside)
        path.symlink_to(outside)
    elif damage == "ancestor_symlink":
        outside = path.parent.with_name(path.parent.name + "-outside")
        path.parent.rename(outside)
        path.parent.symlink_to(outside, target_is_directory=True)
    else:
        os.link(path, tmp_path / "linked.py")
    expected = (
        ReportOwnershipError
        if damage in {"symlink", "ancestor_symlink"}
        else ReportRebuildError
    )
    with pytest.raises(expected):
        source.validated_native_reference_transport_source(
            root, identity, logical, resolver
        )


@pytest.mark.parametrize("name", sorted(source.NATIVE_REFERENCE_TRANSPORT_SOURCES))
@pytest.mark.parametrize(
    "damage",
    ["none", "unrelated_byte", "changed_seam", "duplicate_seam", "old_identity"],
)
def test_native_transport_whole_byte_inverse(
    monkeypatch: pytest.MonkeyPatch, name: str, damage: str
) -> None:
    """Every fixed path must preserve all bytes outside its exact own IO span."""
    monkeypatch.setattr(
        source, "_NATIVE_REFERENCE_TRANSPORT_CONTRACTS", {name: _own_contract()}
    )
    old, current = OLD, NEW
    if damage == "unrelated_byte":
        current += b"# unknown math or statement\n"
    elif damage == "changed_seam":
        current = current.replace(b"authenticated()", b"unchecked()")
    elif damage == "duplicate_seam":
        current += b"source = authenticated()\n"
    elif damage == "old_identity":
        old += b"# different old source\n"
    assert source.native_reference_transport_extension_matches(name, old, current) is (
        damage == "none"
    )


def test_unknown_programme_cannot_borrow_transport_role() -> None:
    """The seven fixed readers are not a general code correspondence namespace."""
    assert not source.native_reference_transport_extension_matches(
        "packages/unknown.py", OLD, NEW
    )
