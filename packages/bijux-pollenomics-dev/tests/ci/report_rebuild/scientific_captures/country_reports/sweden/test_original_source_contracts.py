"""Original execution source custody is distinct from current-code reuse."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.ownership import (
    DEFAULT_INVENTORY,
    _load_inventory,
)
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.country_reports.sweden import (
    transport as subject,
)

from .test_capture import MemoryResolver


def original_sources(
    tmp_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], MemoryResolver]:
    body = b"# original controlled source\n"
    pin: dict[str, Any] = {
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
    }
    member = "members/" + str(pin["sha256"])
    sources: list[dict[str, Any]] = [
        {"path": f"packages/example/source_{i}.py", **pin} for i in range(51)
    ]
    resolver = MemoryResolver(tmp_path / "packet", {member: body})
    capture = {
        "members": deepcopy(resolver.descriptor.members),
        "public_roles": [
            {
                "logical_name": "source/" + row["path"],
                "source_identity": {"path": "/original/" + row["path"], **pin},
                "role": "complete-original-owned-public-source-resource",
                "member": member,
            }
            for row in sources
        ],
    }
    return {"maintained_source_contracts": sources}, capture, resolver


@pytest.mark.parametrize("current_state", ["absent", "changed"])
def test_current_file_drift_does_not_replace_original_source_authority(
    tmp_path: Path, current_state: str
) -> None:
    declaration, capture, resolver = original_sources(tmp_path)
    current = tmp_path / declaration["maintained_source_contracts"][0]["path"]
    if current_state == "changed":
        current.parent.mkdir(parents=True)
        current.write_bytes(b"# different current orchestration\n")
    subject._original_source_contracts(
        declaration, capture, cast(SourceCapsule, resolver)
    )
    assert resolver.refreshes == 2 and resolver.reads == []
    if current_state == "changed":
        assert current.read_bytes() == b"# different current orchestration\n"
    else:
        assert not current.exists()


@pytest.mark.parametrize(
    "change",
    ["missing", "duplicate", "path", "traversal", "sha", "size", "bool_size", "extra"],
)
def test_original_declaration_must_keep_every_exact_source_identity(
    tmp_path: Path, change: str
) -> None:
    declaration, capture, resolver = original_sources(tmp_path)
    rows = declaration["maintained_source_contracts"]
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows[-1] = deepcopy(rows[0])
    elif change == "path":
        rows[0]["path"] = "packages/foreign.py"
    elif change == "traversal":
        rows[0]["path"] = "../packages/example/source_0.py"
    elif change == "sha":
        rows[0]["sha256"] = "a" * 64
    elif change == "size":
        rows[0]["bytes"] += 1
    elif change == "bool_size":
        rows[0]["bytes"] = True
    else:
        rows[0]["extra"] = "unreviewed"
    with pytest.raises(ValueError):
        subject._original_source_contracts(
            declaration, capture, cast(SourceCapsule, resolver)
        )


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "logical_path",
        "role",
        "original_path",
        "sha",
        "size",
        "member",
        "descriptor",
    ],
)
def test_original_source_role_and_authenticated_member_cannot_be_substituted(
    tmp_path: Path, change: str
) -> None:
    declaration, capture, resolver = original_sources(tmp_path)
    roles = capture["public_roles"]
    role = roles[0]
    if change == "missing":
        roles.pop(0)
    elif change == "duplicate":
        roles.append(deepcopy(role))
    elif change == "logical_path":
        role["logical_name"] = "source/packages/foreign.py"
    elif change == "role":
        role["role"] = "actual-original-normally-returned-country-product"
    elif change == "original_path":
        role["source_identity"]["path"] = "/original/packages/foreign.py"
    elif change == "sha":
        role["source_identity"]["sha256"] = "a" * 64
    elif change == "size":
        role["source_identity"]["bytes"] += 1
    elif change == "member":
        role["member"] = "members/" + "a" * 64
    else:
        resolver.descriptor.members[role["member"]]["bytes"] += 1
    with pytest.raises(ValueError):
        subject._original_source_contracts(
            declaration, capture, cast(SourceCapsule, resolver)
        )


def test_original_source_metadata_must_stay_fresh_through_the_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    declaration, capture, resolver = original_sources(tmp_path)
    checks: list[None] = []

    def fresh() -> None:
        checks.append(None)
        if len(checks) == 2:
            raise ValueError("changed original metadata/ref context")

    monkeypatch.setattr(resolver, "fresh", fresh)
    with pytest.raises(ValueError, match="changed original"):
        subject._original_source_contracts(
            declaration, capture, cast(SourceCapsule, resolver)
        )


def test_actual_saved_owner_authenticates_history_without_admitting_current_reuse() -> (
    None
):
    root = next(
        parent for parent in Path(__file__).parents if (parent / ".git").is_dir()
    )
    raw = (root / subject.REPORT).read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    entry = InventoryEntry(
        subject.REPORT.removeprefix("docs/report/"),
        "file",
        len(raw),
        checksum,
        checksum,
    )
    owners = _load_inventory(root, DEFAULT_INVENTORY)["owners"]
    before = deepcopy(owners)
    entries, evidence = subject.validated_sweden_country_capture(
        root, {subject.REPORT: entry}, owners
    )
    assert entries == () and evidence is not None
    assert evidence["admitted_inventory_entries"] == 0
    assert evidence["original_owner_role"] == "unresolved"
    assert evidence["original_owner_acceptance_established"] is False
    assert evidence["source_authentication_role"] == "original_execution_only"
    assert evidence["current_source_or_numerical_reuse_claimed"] is False
    assert (
        evidence["original_controller_actual_exit"]
        == evidence["original_whole_actual_exit"]
        == 1
    )
    assert (
        evidence["saved_observer_actual_exit"]
        == evidence["saved_whole_actual_exit"]
        == 0
    )
    assert evidence["vegetation_rights_human_biology_or_LRA_acceptance"] is False
    assert owners == before and (root / subject.REPORT).read_bytes() == raw
