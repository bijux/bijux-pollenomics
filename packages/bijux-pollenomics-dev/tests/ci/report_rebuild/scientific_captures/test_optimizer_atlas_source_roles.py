"""Keep optimizer presentation custody scoped to six original detached members."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    author_optimizer_diagnostics as module,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.presentation_source_roles import (
    PAYLOAD,
)
from tests.ci.report_rebuild.scientific_captures.source_roles.test_atlas_extensions import (
    own_sources as own_sources,
)

NAMES = tuple(module._OPTIMIZER_ATLAS_SOURCES)


def _world(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    sources: dict[str, tuple[bytes, bytes]],
) -> tuple[dict[str, dict[str, Any]], SimpleNamespace]:
    """Construct six own strings with source metadata, never a retained source packet."""
    assert len(NAMES) == 6
    authority = {}
    members = {}
    rows = {}
    bodies = {}
    bindings = []
    for index, name in enumerate(NAMES):
        role = module._OPTIMIZER_ATLAS_SOURCES[name][2]
        old, new = sources.get(
            name, (f"ORIGINAL_{index} = 1\n".encode(), b"CURRENT_AUDIT_ONLY = 9\n")
        )
        checksum = hashlib.sha256(old).hexdigest()
        logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
        authority[name] = (checksum, len(old), role)
        members[logical] = {"sha256": checksum, "bytes": len(old)}
        rows[name] = {"path": name, **members[logical]}
        bodies[logical] = old
        bindings.append((logical, name))
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(new)
    monkeypatch.setattr(module, "_OPTIMIZER_ATLAS_SOURCES", authority)
    fresh_calls: list[bool] = []
    resolver = SimpleNamespace(
        repository=root,
        prefix=Path(module.CAPTURE).parent.as_posix(),
        descriptor=SimpleNamespace(
            capture={"sha256": module.CAPTURE_SHA256},
            members=members,
            groups=[{"resolved_paths": bindings}],
        ),
        detached=frozenset(members),
        read_source=bodies.__getitem__,
        fresh=lambda: fresh_calls.append(True),
        fresh_calls=fresh_calls,
        owned_bodies=bodies,
    )
    return rows, resolver


@pytest.mark.parametrize("name", NAMES)
def test_each_of_six_roles_retains_old_source_without_current_equivalence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    own_sources: dict[str, tuple[bytes, bytes]],
    name: str,
) -> None:
    rows, resolver = _world(tmp_path, monkeypatch, own_sources)
    logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
    facts = module._optimizer_source_input_correspondence(
        tmp_path, rows[name], logical, cast(SourceCapsule, resolver)
    )
    assert facts is not None
    assert facts["classification"] == "optimizer_atlas_source_custody"
    assert facts["original_member"] == logical
    assert facts["original_sha256"] == rows[name]["sha256"]
    assert facts["current_regular_single_link"] is True
    assert facts["current_browser_native_or_mathematical_equivalence_claimed"] is False
    assert facts["finite_old_byte_law_required"] is (name in own_sources)
    assert resolver.fresh_calls == [True, True]


@pytest.mark.parametrize("name", NAMES)
def test_byte_equal_default_stays_unclassified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    own_sources: dict[str, tuple[bytes, bytes]],
    name: str,
) -> None:
    rows, resolver = _world(tmp_path, monkeypatch, own_sources)
    logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
    (tmp_path / name).write_bytes(resolver.owned_bodies[logical])
    assert (
        module._optimizer_source_input_correspondence(
            tmp_path, rows[name], logical, cast(SourceCapsule, resolver)
        )
        is None
    )


@pytest.mark.parametrize(
    "damage",
    [
        "unknown_math_role",
        "escaped_path",
        "wrong_repository",
        "wrong_capture_prefix",
        "wrong_capture_sha",
        "wrong_lane",
        "wrong_logical_path",
        "not_detached",
        "missing_member",
        "wrong_member_hash",
        "wrong_member_size",
        "wrong_resolved_path",
        "duplicate_resolved_path",
        "unlisted_row_field",
        "wrong_row_hash",
        "wrong_row_size",
        "bool_row_size",
        "old_body_tamper",
        "missing_current",
        "symlink",
        "hardlink",
        "finite_unrelated_math",
        "finite_guard",
    ],
)
def test_lane_custody_and_finite_math_refusals_remain_strict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    own_sources: dict[str, tuple[bytes, bytes]],
    damage: str,
) -> None:
    rows, resolver = _world(tmp_path, monkeypatch, own_sources)
    name = PAYLOAD
    row = rows[name]
    logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
    path = tmp_path / name
    if damage == "unknown_math_role":
        row = {**row, "path": "packages/own/development.py"}
    elif damage == "escaped_path":
        row = {**row, "path": "../development.py"}
    elif damage == "wrong_repository":
        resolver.repository = tmp_path / "another"
    elif damage == "wrong_capture_prefix":
        resolver.prefix = "data/atlas/another-source-capture"
    elif damage == "wrong_capture_sha":
        resolver.descriptor.capture["sha256"] = "0" * 64
    elif damage == "wrong_lane":
        logical = logical.replace("optimizer-diagnostics", "another-lane")
    elif damage == "wrong_logical_path":
        logical += ".another"
    elif damage == "not_detached":
        resolver.detached = frozenset()
    elif damage == "missing_member":
        resolver.descriptor.members.pop(logical)
    elif damage == "wrong_member_hash":
        resolver.descriptor.members[logical]["sha256"] = "0" * 64
    elif damage == "wrong_member_size":
        resolver.descriptor.members[logical]["bytes"] += 1
    elif damage in {"wrong_resolved_path", "duplicate_resolved_path"}:
        values = resolver.descriptor.groups[0]["resolved_paths"]
        if damage == "wrong_resolved_path":
            values[:] = [
                (member, "packages/own/another.py" if member == logical else canonical)
                for member, canonical in values
            ]
        else:
            values.append((logical, name))
    elif damage == "unlisted_row_field":
        row["extra"] = "unknown"
    elif damage == "wrong_row_hash":
        row["sha256"] = "0" * 64
    elif damage == "wrong_row_size":
        row["bytes"] += 1
    elif damage == "bool_row_size":
        row["bytes"] = True
    elif damage == "old_body_tamper":
        resolver.owned_bodies[logical] += b"\n# altered original\n"
    elif damage == "missing_current":
        path.unlink()
    elif damage in {"symlink", "hardlink"}:
        target = tmp_path / "own-link-target"
        target.write_bytes(path.read_bytes())
        path.unlink()
        if damage == "symlink":
            path.symlink_to(target)
        else:
            path.hardlink_to(target)
    elif damage == "finite_unrelated_math":
        path.write_bytes(path.read_bytes().replace(b'"own": 7', b'"own": 9'))
    else:
        path.write_bytes(
            path.read_bytes().replace(
                b"and static_assets is None", b"or static_assets is None"
            )
        )
    with pytest.raises((ReportRebuildError, OSError)):
        module._optimizer_source_input_correspondence(
            tmp_path, row, logical, cast(SourceCapsule, resolver)
        )


def test_six_role_facts_have_truthful_current_historical_and_exact_partitions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    own_sources: dict[str, tuple[bytes, bytes]],
) -> None:
    rows, resolver = _world(tmp_path, monkeypatch, own_sources)
    correspondences = []
    for name in NAMES:
        logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
        facts = module._optimizer_source_input_correspondence(
            tmp_path, rows[name], logical, cast(SourceCapsule, resolver)
        )
        assert facts is not None
        correspondences.append(facts)
    actual = module._optimizer_projection_accounting(correspondences, [])
    historical = [
        value
        for value in correspondences
        if value["role"]
        in {"historical_browser_orchestration", "historical_capture_admission"}
    ]
    finite = [
        value for value in correspondences if value["role"] == "finite_atlas_extension"
    ]
    assert len(historical) == len(finite) == 3
    assert actual["logical_scientific_projection"] == 2072
    assert actual["current_scientific_projection"] == 2069
    assert actual["current_projection_byteequal_members"] == 2066
    assert actual["historical_only_projection_roles"] == historical
    assert not any(
        value in actual["historical_only_projection_roles"] for value in finite
    )


def test_existing_historical_policy_and_unknown_roles_do_not_change_partitions() -> (
    None
):
    assert module._optimizer_projection_accounting([], []) == {
        "logical_scientific_projection": 2072,
        "current_scientific_projection": 2072,
        "historical_only_projection_roles": [],
        "current_projection_byteequal_members": 2072,
    }
    historical: list[dict[str, object]] = [
        {"classification": "historical_private_control_current_absence"},
        {"classification": "historical_generated_version_metadata"},
        {
            "classification": "optimizer_atlas_source_custody",
            "role": "historical_browser_orchestration",
        },
        {
            "classification": "optimizer_atlas_source_custody",
            "role": "historical_capture_admission",
        },
    ]
    current: list[dict[str, object]] = [
        {
            "classification": "optimizer_atlas_source_custody",
            "role": "finite_atlas_extension",
        },
        {"classification": "unknown_current", "role": "historical_capture_admission"},
        {
            "classification": "optimizer_atlas_source_custody",
            "role": "historical_unreviewed",
        },
        {"classification": "other_current_correspondence"},
    ]
    actual = module._optimizer_projection_accounting(
        historical + current, [{"path": "own"}]
    )
    assert actual["logical_scientific_projection"] == 2072
    assert actual["current_scientific_projection"] == 2068
    assert actual["historical_only_projection_roles"] == historical
    assert actual["current_projection_byteequal_members"] == 2063
