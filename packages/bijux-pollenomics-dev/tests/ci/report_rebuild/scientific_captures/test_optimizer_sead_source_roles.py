"""Keep four unconsumed collector inputs in exact historical optimizer custody."""

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

NAMES = tuple(module._OPTIMIZER_SEAD_SOURCES)


def _world(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    sources: dict[str, tuple[bytes, bytes]],
) -> tuple[dict[str, dict[str, Any]], SimpleNamespace]:
    """Construct four own strings with source metadata, never a retained source packet."""
    assert len(NAMES) == 4
    authority = {}
    members = {}
    rows = {}
    bodies = {}
    bindings = []
    for index, name in enumerate(NAMES):
        role = module._OPTIMIZER_SEAD_SOURCES[name][2]
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
    monkeypatch.setattr(module, "_OPTIMIZER_SEAD_SOURCES", authority)
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
def test_named_collector_keeps_historical_custody_without_current_equivalence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """Retain the exact old collector input and classify its changed body historically."""
    rows, resolver = _world(tmp_path, monkeypatch, {})
    logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
    facts = module._optimizer_source_input_correspondence(
        tmp_path, rows[name], logical, cast(SourceCapsule, resolver)
    )
    assert facts is not None
    assert facts["classification"] == "optimizer_sead_source_custody"
    assert facts["role"] == "historical_source_collector_input"
    assert facts["original_member"] == logical
    assert facts["original_sha256"] == rows[name]["sha256"]
    assert facts["original_bytes"] == rows[name]["bytes"]
    assert facts["current_regular_single_link"] is True
    assert facts["finite_old_byte_law_required"] is False
    assert facts["current_browser_native_or_mathematical_equivalence_claimed"] is False
    assert resolver.fresh_calls == [True, True]
    actual = module._optimizer_projection_accounting([facts], [])
    assert actual["historical_only_projection_roles"] == [facts]
    assert actual["current_scientific_projection"] == 2071
    assert actual["current_projection_byteequal_members"] == 2071


@pytest.mark.parametrize("name", NAMES)
def test_original_byte_equality_keeps_the_default_partition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """Leave an unchanged input in the exact current partition."""
    rows, resolver = _world(tmp_path, monkeypatch, {})
    logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
    (tmp_path / name).write_bytes(resolver.owned_bodies[logical])
    assert (
        module._optimizer_source_input_correspondence(
            tmp_path, rows[name], logical, cast(SourceCapsule, resolver)
        )
        is None
    )


@pytest.mark.parametrize("name", NAMES)
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
    ],
)
def test_original_collector_binding_and_current_confinement_refusals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    damage: str,
) -> None:
    """Reject broken old authority or unsafe current source counterparts."""
    rows, resolver = _world(tmp_path, monkeypatch, {})
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
    else:
        raise AssertionError(damage)
    with pytest.raises((ReportRebuildError, OSError)):
        module._optimizer_source_input_correspondence(
            tmp_path, row, logical, cast(SourceCapsule, resolver)
        )


def test_all_ten_roles_preserve_truthful_current_and_historical_counts() -> None:
    """Keep finite Atlas extensions separate from seven historical-only inputs."""
    historical: list[dict[str, object]] = [
        {"classification": "optimizer_atlas_source_custody", "role": role}
        for role in (
            "historical_browser_orchestration",
            "historical_capture_admission",
            "historical_capture_admission",
        )
    ] + [
        {
            "classification": "optimizer_sead_source_custody",
            "role": "historical_source_collector_input",
        }
        for _ in range(4)
    ]
    finite: list[dict[str, object]] = [
        {
            "classification": "optimizer_atlas_source_custody",
            "role": "finite_atlas_extension",
        }
        for _ in range(3)
    ]
    actual = module._optimizer_projection_accounting(historical + finite, [])
    assert actual["logical_scientific_projection"] == 2072
    assert actual["current_scientific_projection"] == 2065
    assert actual["current_projection_byteequal_members"] == 2062
    assert actual["historical_only_projection_roles"] == historical
    assert not any(item in historical for item in finite)
    unknown: list[dict[str, object]] = [
        {
            "classification": "optimizer_sead_source_custody",
            "role": "historical_unreviewed",
        },
        {
            "classification": "unknown_current",
            "role": "historical_source_collector_input",
        },
    ]
    facts = module._optimizer_projection_accounting(unknown, [])
    assert facts["historical_only_projection_roles"] == []
    assert facts["current_scientific_projection"] == 2072
    assert facts["current_projection_byteequal_members"] == 2070
