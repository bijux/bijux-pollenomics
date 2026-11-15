"""Keep optimizer presentation custody scoped to six original detached members."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule, index
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    author_optimizer_diagnostics as module,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.presentation_source_roles import (
    PAYLOAD,
    WORKFLOW,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    atlas_relation_context as relation,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    atlas_runtime_transport as runtime,
)
from tests.ci.report_rebuild.scientific_captures.source_roles.test_atlas_extensions import (
    own_sources as own_sources,
)
from tests.ci.report_rebuild.source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)

NAMES = tuple(module._OPTIMIZER_ATLAS_SOURCES)


def _world(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    sources: dict[str, tuple[bytes, bytes]],
) -> tuple[dict[str, dict[str, Any]], SourceCapsule, dict[str, bytes]]:
    """Authenticate six inert source examples through their actual Git/capture epoch."""
    assert len(NAMES) == 6
    _git(
        root,
        "init",
        "--quiet",
        "--template=",
        "--initial-branch=main",
        "--object-format=sha1",
    )
    authority = {}
    members = {}
    rows = {}
    bodies = {}
    current = {}
    prefix = Path(module.CAPTURE).parent.as_posix()
    anchor = b"from __future__ import annotations\n"
    extended = anchor + b"\n# Source-owned fixture context.\n"
    for ordinal, name in enumerate(NAMES):
        role = module._OPTIMIZER_ATLAS_SOURCES[name][2]
        old, new = sources.get(
            name, (f"ORIGINAL_{ordinal} = 1\n".encode(), b"CURRENT_AUDIT_ONLY = 9\n")
        )
        checksum = hashlib.sha256(old).hexdigest()
        logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
        authority[name] = (checksum, len(old), role)
        members[logical] = {"sha256": checksum, "bytes": len(old)}
        rows[name] = {"path": name, **members[logical]}
        bodies[logical] = old
        _write(root / name, old)
        current[name] = (
            new.replace(anchor, extended, 1) if name in {PAYLOAD, WORKFLOW} else new
        )
    _git(root, "add", "--", *NAMES)
    _git(
        root,
        "-c",
        "user.name=Bijux fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--quiet",
        "--no-gpg-sign",
        "-m",
        "test(atlas): bind inert optimizer source custody",
    )
    revision = _git(root, "rev-parse", "HEAD").decode().strip()
    bindings = [
        ["executions/optimizer-diagnostics/first-party-inputs/" + name, name]
        for name in NAMES
    ]
    git_entries = [
        [name, _git(root, "rev-parse", "HEAD:" + name).decode().strip()]
        for name in sorted(NAMES)
    ]
    capture = _encoded({"members": members})
    capture_identity = _identity(capture)
    _write(root / prefix / "capture.json", capture)
    descriptor = {
        "schema_version": "git-retained-source.v1",
        "capture": {"name": "capture.json", **capture_identity},
        "historical_native_epochs": [revision],
        "source_revision_correspondence": [
            {"historical_source_commit": revision, "source_revision": revision}
        ],
        "git_groups": [
            {
                "historical_source_commit": revision,
                "source_revision": revision,
                "member_count": len(NAMES),
                "git_entries_sha256": hashlib.sha256(
                    json.dumps(git_entries, separators=(",", ":")).encode()
                ).hexdigest(),
                "paths": bindings,
            }
        ],
        "generated_members": [],
        "rewritten_source_epoch_executed": False,
    }
    consumer = Consumer(
        "qualification",
        root,
        prefix,
        members,
        frozenset(members),
        bodies,
        descriptor,
        [],
    )
    consumer.repin(monkeypatch)
    monkeypatch.setattr(module, "_OPTIMIZER_ATLAS_SOURCES", authority)
    monkeypatch.setattr(module, "CAPTURE_SHA256", capture_identity["sha256"])
    for owner, field, source, composition in (
        (
            relation,
            "_RELATION_CONTEXT_CONTRACTS",
            PAYLOAD,
            "existing_named_native_asset_binding",
        ),
        (
            runtime,
            "_RUNTIME_TRANSPORT_CONTRACTS",
            WORKFLOW,
            "existing_atlas_workflow_export",
        ),
    ):
        contracts = dict(getattr(owner, field))
        old = sources[source][0]
        contracts[source] = (
            len(old),
            _identity(old)["sha256"],
            composition,
            ((anchor, extended),),
        )
        monkeypatch.setattr(owner, field, contracts)
        contexts = dict(owner._CAPTURE_CONTEXTS)
        contexts[prefix] = (
            capture_identity["sha256"],
            "executions/optimizer-diagnostics/first-party-inputs/",
        )
        monkeypatch.setattr(owner, "_CAPTURE_CONTEXTS", contexts)
    resolver = index.validated_descriptor(root, prefix, members)
    for logical, old in bodies.items():
        assert resolver.read_source(logical) == old
    for name, body in current.items():
        (root / name).write_bytes(body)
    return rows, resolver, bodies


@pytest.mark.parametrize("name", NAMES)
def test_each_of_six_roles_retains_old_source_without_current_equivalence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    own_sources: dict[str, tuple[bytes, bytes]],
    name: str,
) -> None:
    rows, resolver, bodies = _world(tmp_path, monkeypatch, own_sources)
    logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
    facts = module._optimizer_source_input_correspondence(
        tmp_path, rows[name], logical, resolver
    )
    assert facts is not None
    expected = {
        PAYLOAD: "atlas_relation_context_extension",
        WORKFLOW: "runtime_transport_extension",
    }.get(name, "optimizer_atlas_source_custody")
    assert facts["classification"] == expected
    assert facts["original_member"] == logical
    assert facts["original_sha256"] == rows[name]["sha256"]
    if name in {PAYLOAD, WORKFLOW}:
        assert facts["current_regular_single_link_and_stable"] is True
        assert facts["historical_native_equal_current_output_claimed"] is False
        assert facts["historical_browser_equal_current_browser_claimed"] is False
    else:
        assert facts["current_regular_single_link"] is True
        assert (
            facts["current_browser_native_or_mathematical_equivalence_claimed"] is False
        )
        assert facts["finite_old_byte_law_required"] is (name in own_sources)
    assert resolver.read_source(logical) == bodies[logical]


@pytest.mark.parametrize("name", NAMES)
def test_byte_equal_default_stays_unclassified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    own_sources: dict[str, tuple[bytes, bytes]],
    name: str,
) -> None:
    rows, resolver, bodies = _world(tmp_path, monkeypatch, own_sources)
    logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
    (tmp_path / name).write_bytes(bodies[logical])
    assert (
        module._optimizer_source_input_correspondence(
            tmp_path, rows[name], logical, resolver
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
        "changed_capture_after_positive",
        "changed_git_ref_after_positive",
    ],
)
def test_lane_custody_and_finite_math_refusals_remain_strict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    own_sources: dict[str, tuple[bytes, bytes]],
    damage: str,
) -> None:
    rows, resolver, bodies = _world(tmp_path, monkeypatch, own_sources)
    name = PAYLOAD
    row = rows[name]
    logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
    path = tmp_path / name
    baseline = module._optimizer_source_input_correspondence(
        tmp_path, row, logical, resolver
    )
    assert (
        baseline is not None
        and baseline["classification"] == "atlas_relation_context_extension"
    )
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
        resolver.descriptor = replace(resolver.descriptor, detached=frozenset())
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
        resolver._payloads[logical] = bodies[logical] + b"\n# altered original\n"
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
    elif damage == "finite_guard":
        path.write_bytes(
            path.read_bytes().replace(
                b"and static_assets is None", b"or static_assets is None"
            )
        )
    elif damage == "changed_capture_after_positive":
        capture = tmp_path / resolver.prefix / "capture.json"
        capture.write_bytes(capture.read_bytes() + b" ")
    else:
        reference = tmp_path / ".git/refs/heads/main"
        reference.write_text("0" * 40 + "\n", encoding="ascii")
    with pytest.raises((ReportRebuildError, OSError)):
        module._optimizer_source_input_correspondence(tmp_path, row, logical, resolver)


def test_six_role_facts_have_truthful_current_historical_and_exact_partitions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    own_sources: dict[str, tuple[bytes, bytes]],
) -> None:
    rows, resolver, _ = _world(tmp_path, monkeypatch, own_sources)
    correspondences = []
    for name in NAMES:
        logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
        facts = module._optimizer_source_input_correspondence(
            tmp_path, rows[name], logical, resolver
        )
        assert facts is not None
        correspondences.append(facts)
    actual = module._optimizer_projection_accounting(correspondences, [])
    historical = [
        value
        for value in correspondences
        if value.get("role")
        in {"historical_browser_orchestration", "historical_capture_admission"}
    ]
    finite = [
        value
        for value in correspondences
        if value.get("role") == "finite_atlas_extension"
        or value["classification"]
        in {"atlas_relation_context_extension", "runtime_transport_extension"}
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
