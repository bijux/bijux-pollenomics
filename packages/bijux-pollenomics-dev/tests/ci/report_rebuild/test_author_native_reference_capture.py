"""Check author retained-source boundaries using only invented fixture bytes."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.generated import (
    reconstruct,
)
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.index import (
    validated_descriptor,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    author_native_reference as author,
)

ADMIT = author.validated_author_native_reference_capture
SOURCE_COUNT = 69
ADMITTED_COUNT = 1
SCHEMA = "retained-author-native-comparison-source-capture.v1"
Fixture = tuple[Path, dict[str, InventoryEntry], list[dict[str, Any]], dict[str, Any]]


@pytest.fixture
def constructed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Fixture:
    """Separate main-reader policy from the independently checked native and Git layers."""
    body = b'{"invented": true}\n'
    digest = hashlib.sha256(body).hexdigest()
    members: list[dict[str, Any]] = []
    projection: list[dict[str, Any]] = []
    payloads: dict[str, bytes] = {}
    lane = next(iter(author.EXECUTIONS))
    for index in range(SOURCE_COUNT - 1):
        name = f"packages/bijux-pollenomics-lra/src/invented_{index}.py"
        current = tmp_path / name
        current.parent.mkdir(parents=True, exist_ok=True)
        current.write_bytes(body)
        projection.append({"path": name, "bytes": len(body), "sha256": digest})
        member = f"executions/{lane}/first-party-inputs/{name}"
        members.append({"path": member, "bytes": len(body), "sha256": digest})
        payloads[member] = body
    generated: list[dict[str, Any]] = []
    version = {"bytes": author.VERSION_BYTES, "sha256": author.VERSION_SHA256}
    for lane in author.EXECUTIONS:
        member = f"executions/{lane}/first-party-inputs/{author.VERSION_SOURCE}"
        row: dict[str, Any] = {
            "member": member,
            "generator": {
                "provider": "vcs-versioning.default-python",
                "sha256": "dd7ded849d3bacc8e13b0b675ed991904eb896fc79b4607f4f70ee32e47171d9",
                "bytes": 4479,
            },
            "scalars": {
                "version": "0.1.9.dev1462",
                "version_tuple": [0, 1, 9, "dev1462"],
                "short_node": None,
            },
            "original_generator_execution_claimed": False,
            "original_version_derivation_claimed": False,
        }
        generated.append(row)
        members.append({"path": member, **version})
        payloads[member] = reconstruct(row, version)
    projection.append({"path": author.VERSION_SOURCE, **version})
    current = tmp_path / author.VERSION_SOURCE
    current.parent.mkdir(parents=True, exist_ok=True)
    current.write_bytes(b"invented current ignored metadata\n")
    owners: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    tracked: dict[str, InventoryEntry] = {}
    for owner_id, (family, count) in author.OWNERS.items():
        names = [family + f"invented-{index}.json" for index in range(count)]
        owner = {
            "owner_id": owner_id,
            "role": "retained_source",
            "paths": sorted(names),
            "producer_paths": [],
            "producer_inputs": [],
        }
        owners.append(owner)
        for name in names:
            current = tmp_path / name
            current.parent.mkdir(parents=True, exist_ok=True)
            current.write_bytes(body)
            tracked[name] = InventoryEntry(
                name.removeprefix("docs/report/"), "file", len(body), digest, digest
            )
            outputs.append(
                {
                    "owner_id": owner_id,
                    "path": name,
                    "published": {"bytes": len(body), "sha256": digest},
                }
            )
            members.append(
                {"path": "published/" + name, "bytes": len(body), "sha256": digest}
            )
            payloads["published/" + name] = body
    for index in range(author.EXPECTED_MEMBERS - len(members)):
        members.append(
            {"path": f"invented/{index}.txt", "bytes": len(body), "sha256": digest}
        )
    capture = {
        "schema_version": SCHEMA,
        "members": members,
        "member_count": author.EXPECTED_MEMBERS,
        "current_scientific_source_projection": projection,
        "report_outputs": outputs,
    }
    path = tmp_path / author.CAPTURE
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(capture).encode()
    path.write_bytes(encoded)
    monkeypatch.setattr(author, "CAPTURE_SHA256", hashlib.sha256(encoded).hexdigest())
    calls: dict[str, Any] = {
        "generated": generated,
        "payloads": payloads,
        "fresh": 0,
        "native": 0,
    }

    def fresh() -> None:
        calls["fresh"] += 1

    def descriptor(repository: Path, prefix: str, normalized: Any) -> SimpleNamespace:
        assert repository == tmp_path and prefix == str(Path(author.CAPTURE).parent)
        assert len(normalized) == author.EXPECTED_MEMBERS
        return SimpleNamespace(
            descriptor=SimpleNamespace(generated=tuple(generated)),
            read_source=payloads.__getitem__,
            fresh=fresh,
        )

    def native(packet: Path, value: dict[str, Any]) -> None:
        assert (
            packet == path.parent and value["member_count"] == author.EXPECTED_MEMBERS
        )
        calls["native"] += 1

    monkeypatch.setattr(author, validated_descriptor.__name__, descriptor)
    monkeypatch.setattr(author, "_native_references", native)
    calls["descriptor_factory"] = descriptor
    return tmp_path, tracked, owners, calls


def test_complete_owned_outputs_with_separate_historical_version(
    constructed: Fixture,
) -> None:
    """Admit only qualified owners while preserving a distinct historical version role."""
    root, tracked, owners, calls = constructed
    current = (root / author.VERSION_SOURCE).read_bytes()
    entries, facts = ADMIT(root, tracked, owners)
    assert len(entries) == ADMITTED_COUNT
    assert facts["current_scientific_projection"] == SOURCE_COUNT - 1
    assert facts["historical_generated_metadata_members"] == 1
    assert facts["historical_generated_logical_aliases"] == len(author.EXECUTIONS)
    assert calls["native"] == calls["fresh"] == 1
    assert (root / author.VERSION_SOURCE).read_bytes() == current


@pytest.mark.parametrize(
    "change", ["role", "producer", "missing", "duplicate", "overlap"]
)
def test_changed_owner_contract_refuses(constructed: Fixture, change: str) -> None:
    """Reject owner-role, producer, population and overlap changes."""
    root, tracked, original, _ = constructed
    owners = copy.deepcopy(original)
    selected = next(row for row in owners if row["role"] == "retained_source")
    if change == "role":
        selected["role"] = "unresolved"
    elif change == "producer":
        selected["producer_inputs"] = ["unbound.csv"]
    elif change == "missing":
        selected["paths"].pop()
    elif change == "duplicate":
        owners.append(copy.deepcopy(selected))
    else:
        owners.append(
            {
                "owner_id": "other",
                "role": "retained_source",
                "paths": [selected["paths"][0]],
            }
        )
    with pytest.raises(ReportRebuildError):
        ADMIT(root, tracked, owners)


@pytest.mark.parametrize(
    "change", ["inventory", "report", "authority", "current_source"]
)
def test_current_identity_changes_refuse(constructed: Fixture, change: str) -> None:
    """Preserve current report, authority and ordinary scientific source byte checks."""
    root, original, owners, _ = constructed
    tracked = dict(original)
    name = sorted(tracked)[0]
    target = root / name
    if change == "inventory":
        tracked[name] = replace(tracked[name], sha256="0" * 64)
    elif change == "authority":
        target = root / author.CAPTURE
    elif change == "current_source":
        target = root / "packages/bijux-pollenomics-lra/src/invented_0.py"
    if change != "inventory":
        target.write_bytes(target.read_bytes() + b" changed")
    with pytest.raises(ReportRebuildError):
        ADMIT(root, tracked, owners)


@pytest.mark.parametrize("change", ["provider", "member", "duplicate", "body"])
def test_historical_generator_role_is_explicit_and_closed(
    constructed: Fixture, change: str
) -> None:
    """Refuse changed generator, aliases and old metadata body without physical fallback."""
    root, tracked, owners, calls = constructed
    row = calls["generated"][0]
    if change == "provider":
        row["generator"]["provider"] = "unregistered"
    elif change == "member":
        row["member"] = "executions/foreign/first-party-inputs/version.py"
    elif change == "duplicate":
        calls["generated"].append(copy.deepcopy(row))
    else:
        calls["payloads"][row["member"]] += b" changed"
    with pytest.raises(ReportRebuildError):
        ADMIT(root, tracked, owners)


@pytest.mark.parametrize("operation", ["descriptor", "fresh"])
def test_source_capsule_refusals_propagate(
    constructed: Fixture, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    """Keep descriptor and freshness failures terminal instead of falling back."""
    root, tracked, owners, calls = constructed
    original = calls["descriptor_factory"]

    def refuse() -> None:
        raise ReportRebuildError("invented capsule refusal")

    def descriptor(repository: Path, prefix: str, normalized: Any) -> Any:
        if operation == "descriptor":
            refuse()
        value = original(repository, prefix, normalized)
        return SimpleNamespace(
            descriptor=value.descriptor, read_source=value.read_source, fresh=refuse
        )

    monkeypatch.setattr(author, validated_descriptor.__name__, descriptor)
    with pytest.raises(ReportRebuildError, match="invented capsule refusal"):
        ADMIT(root, tracked, owners)


@pytest.mark.parametrize("value", [False, True, 0.0, None, "0", 1])
def test_native_zero_keeps_its_exact_integer_type(value: object) -> None:
    """Distinguish native integer completion from booleans and coerced zeros."""
    assert author._zero(value) is False
    assert author._zero(0) is True


def test_native_execution_membership_remains_strict(tmp_path: Path) -> None:
    """Reject an unbound native history before attempting any retained file read."""
    with pytest.raises(ReportRebuildError):
        author._native_references(
            tmp_path, {"original_execution_custody": {"foreign": {}}}
        )


def test_unrelated_inactive_repository_does_not_invent_evidence(tmp_path: Path) -> None:
    """Return no retained evidence before this capture and its owners are active."""
    assert ADMIT(tmp_path, {}, []) == ((), {})
