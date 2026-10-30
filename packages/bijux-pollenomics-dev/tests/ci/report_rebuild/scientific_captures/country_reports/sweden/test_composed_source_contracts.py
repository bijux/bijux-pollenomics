"""Keep Sweden's three existing Atlas source laws finite and default-strict."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.country_reports.sweden import (
    metadata as subject,
)
import bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles.atlas_context as context_law
import bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles.atlas_evidence_selection as selection_law
import bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles.atlas_relation_context as relation_law

from .test_recorded_source_contracts import _contracts

ROOT = next(parent for parent in Path(__file__).parents if (parent / ".git").is_dir())
ORIGINAL_STORAGE = "d029760ddf2f6853d07e9ac14091df8f041ecbb4"
SERVICE = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py"
RENDER = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py"
)
PAYLOAD = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/payload.py"
)
CASES = [
    (SERVICE, "source_view_context_extension", "atlas_context_extension_matches"),
    (
        RENDER,
        "atlas_evidence_selection_extension",
        "atlas_evidence_selection_extension_matches",
    ),
    (
        PAYLOAD,
        "atlas_relation_context_extension",
        "atlas_relation_context_extension_matches",
    ),
]
ORIGINALS = {
    SERVICE: (
        12435,
        "7f44338f73d6efd918f9d82d3e8ba9d686db4cfa92251e3d2446794945a6b6e4",
    ),
    RENDER: (2007, "5d4e6e72c8794e40d6a741d40a74d7c0e3dbe6de9791e0c555f3043da5bf0def"),
    PAYLOAD: (8502, "e131724adacd5471cdc1b236079b5d091b33ed618ed5e1e1c8afab49363a0e57"),
}


def _real_buffers(name: str) -> tuple[bytes, bytes]:
    captured = subprocess.run(
        [
            "git",
            "--no-replace-objects",
            "-C",
            str(ROOT),
            "show",
            f"{ORIGINAL_STORAGE}:{name}",
        ],
        capture_output=True,
        check=True,
        timeout=10,
    ).stdout
    size, digest = ORIGINALS[name]
    assert len(captured) == size and hashlib.sha256(captured).hexdigest() == digest
    path = ROOT / name
    assert path.resolve(strict=True) == path and path.stat().st_nlink == 1
    current = path.read_bytes()
    return captured, current


def _partial_current(name: str, current: bytes) -> bytes:
    if name == SERVICE:
        spans = context_law._SOURCE_CONTEXT_CONTRACTS[name][3]
    elif name == RENDER:
        spans = selection_law._SELECTION_TRANSPORT_CONTRACTS[name][3]
    else:
        assert name == PAYLOAD
        spans = relation_law._RELATION_CONTEXT_CONTRACTS[name][3]
    old, extension = spans[0]
    assert current.count(extension) == 1
    return current.replace(extension, old, 1)


@pytest.mark.parametrize("name,classification,predicate", CASES)
@pytest.mark.parametrize("damage", [None, "unknown_path", "old", "current", "partial"])
def test_real_old_git_and_current_source_laws_refuse_unreviewed_changes(
    name: str, classification: str, predicate: str, damage: str | None
) -> None:
    captured, current = _real_buffers(name)
    assert (
        subject._composed_atlas_source_role(name, captured, current) == classification
    )
    original_current = current
    if damage == "unknown_path":
        name = "packages/own/unknown_source.py"
    elif damage == "old":
        captured += b"# unreviewed original change\n"
    elif damage == "current":
        current += b"# unreviewed current change\n"
    elif damage == "partial":
        current = _partial_current(name, current)
    role = subject._composed_atlas_source_role(name, captured, current)
    assert role == (classification if damage is None else None)
    assert (
        ROOT / next(path for path, _, item in CASES if item == predicate)
    ).read_bytes() == original_current


def _own_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    predicate: str,
) -> tuple[list[dict[str, Any]], Any, dict[str, bytes], bytes, bytes]:
    rows, resolver, bodies = _contracts(tmp_path, monkeypatch)
    initial = subject.validate_recorded_source_contracts(
        tmp_path, rows, cast(SourceCapsule, resolver)
    )
    assert initial["current_default_exact_sources"] == 49
    assert "finite_composed_atlas_source_correspondences" not in initial
    row = rows[0]
    logical = "members/" + row["sha256"]
    captured = bodies[logical]
    current = captured + b"# own runtime layer\n# own context layer\n"
    row["path"] = name
    resolver.descriptor.groups[0]["resolved_paths"][0] = (logical, name)
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(current)

    def own_predicate(path: str, old: bytes, new: bytes) -> bool:
        return path == name and old == captured and new == current

    # This fixture tests the reader's exact dispatch and full member binding.
    # Real fixed byte laws are exercised separately above without source copies.
    monkeypatch.setattr(subject, predicate, own_predicate)
    return rows, resolver, bodies, captured, current


@pytest.mark.parametrize("name,classification,predicate", CASES)
@pytest.mark.parametrize(
    "damage", [None, "unknown_path", "old", "current", "partial", "not_detached"]
)
def test_owned_fifty_one_member_dispatch_preserves_default_refusals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    classification: str,
    predicate: str,
    damage: str | None,
) -> None:
    rows, resolver, bodies, captured, current = _own_case(
        tmp_path, monkeypatch, name, predicate
    )
    before = subject.validate_recorded_source_contracts(
        tmp_path, rows, cast(SourceCapsule, resolver)
    )
    assert before["original_source_contracts_authenticated"] == 51
    assert before["current_default_exact_sources"] == 48
    assert before["current_browser_or_native_equivalence_claimed"] is False
    assert before["finite_composed_atlas_source_correspondences"] == [
        {
            "path": name,
            "classification": classification,
            "whole_original_source_reconstructed": True,
            "current_browser_or_native_equivalence_claimed": False,
        }
    ]
    row = rows[0]
    logical = "members/" + row["sha256"]
    path = tmp_path / name
    if damage == "unknown_path":
        name = "packages/own/unknown_source.py"
        row["path"] = name
        resolver.descriptor.groups[0]["resolved_paths"][0] = (logical, name)
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(current)
    elif damage == "old":
        changed = captured + b"# different bound original\n"
        digest = hashlib.sha256(changed).hexdigest()
        revised = "members/" + digest
        row.update(sha256=digest, bytes=len(changed))
        resolver.descriptor.members.pop(logical)
        resolver.descriptor.members[revised] = {"sha256": digest, "bytes": len(changed)}
        resolver.descriptor.groups[0]["resolved_paths"][0] = (revised, name)
        bodies.pop(logical)
        bodies[revised] = changed
        resolver.detached = frozenset(resolver.descriptor.members)
    elif damage == "current":
        path.write_bytes(current + b"# unreviewed current suffix\n")
    elif damage == "partial":
        path.write_bytes(captured + b"# own runtime layer\n")
    elif damage == "not_detached":
        resolver.detached = frozenset()
    if damage is None:
        assert (
            subject.validate_recorded_source_contracts(
                tmp_path, rows, cast(SourceCapsule, resolver)
            )
            == before
        )
    else:
        with pytest.raises(ValueError, match="without a named role"):
            subject.validate_recorded_source_contracts(
                tmp_path, rows, cast(SourceCapsule, resolver)
            )
