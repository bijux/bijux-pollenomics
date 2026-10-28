"""Exercise Linux retained-reader owner and output contracts with invented bytes."""

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
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    linux_r_reference as linux,
)

Fixture = tuple[Path, dict[str, InventoryEntry], list[dict[str, Any]], dict[str, Any]]


@pytest.fixture
def constructed_reader(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Fixture:
    """Isolate owner/output policy; generic capsule and native guards have own tests."""
    body = b"invented source bytes\n"
    digest = hashlib.sha256(body).hexdigest()
    members: list[dict[str, Any]] = []
    scientific: list[dict[str, Any]] = []
    payloads: dict[str, bytes] = {}
    for index in range(127):
        name = (
            "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
            f"reader_fixture_{index}.py"
        )
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        scientific.append({"relative_path": name, "sha256": digest, "bytes": len(body)})
        members.append({"path": "source/" + name, "sha256": digest, "bytes": len(body)})
        payloads["source/" + name] = body
    lock_name = "configs/ci/lra-r-source-lock.v1.json"
    lock = tmp_path / lock_name
    lock.parent.mkdir(parents=True)
    lock.write_bytes(body)
    members.append(
        {"path": "source/" + lock_name, "sha256": digest, "bytes": len(body)}
    )
    payloads["source/" + lock_name] = body
    tracked: dict[str, InventoryEntry] = {}
    outputs: list[dict[str, Any]] = []
    for index in range(137):
        name = linux.FAMILY + f"invented-output-{index}.json"
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        tracked[name] = InventoryEntry(
            name.removeprefix("docs/report/"), "file", len(body), digest, digest
        )
        outputs.append({"path": name, "sha256": digest, "bytes": len(body)})
        members.append(
            {
                "path": "retained/" + name.removeprefix(linux.FAMILY),
                "sha256": digest,
                "bytes": len(body),
            }
        )
    for index in range(2311 - len(members)):
        members.append(
            {
                "path": f"invented-metadata/{index}.txt",
                "sha256": digest,
                "bytes": len(body),
            }
        )
    capture: dict[str, Any] = {
        "members": members,
        "member_count": 2311,
        "current_scientific_source_projection": {"members": scientific},
        "current_report_owner": {"owner_id": linux.OWNER, "outputs": outputs},
    }
    capture_path = tmp_path / linux.CAPTURE
    capture_path.parent.mkdir(parents=True)
    encoded = json.dumps(capture).encode()
    capture_path.write_bytes(encoded)
    monkeypatch.setattr(linux, "CAPTURE_SHA256", hashlib.sha256(encoded).hexdigest())
    calls: dict[str, Any] = {"descriptor": [], "native": [], "fresh": 0}

    def descriptor(repository: Path, prefix: str, normalized: Any) -> SimpleNamespace:
        calls["descriptor"].append((repository, prefix, normalized))

        def fresh() -> None:
            calls["fresh"] += 1

        return SimpleNamespace(read_source=payloads.__getitem__, fresh=fresh)

    def native(packet: Path, authority: dict[str, Any], read_member: Any) -> None:
        calls["native"].append(
            (packet, authority["member_count"] == 2311, callable(read_member))
        )

    monkeypatch.setattr(linux, "validated_descriptor", descriptor)
    monkeypatch.setattr(linux, "_native_references", native)
    owners: list[dict[str, Any]] = [
        {
            "owner_id": linux.OWNER,
            "role": "retained_source",
            "paths": sorted(tracked),
            "producer_paths": [],
            "producer_inputs": [],
        }
    ]
    return tmp_path, tracked, owners, calls


def test_owner_output_contract_with_constructed_member_reader(
    constructed_reader: Fixture,
) -> None:
    """Require complete output ownership and fresh retained-reader verification."""
    root, tracked, owners, calls = constructed_reader
    entries, evidence = linux.validated_linux_r_reference_capture(root, tracked, owners)
    assert len(entries) == 137
    assert evidence["scientific_current_projection"] == 127
    assert len(calls["descriptor"]) == len(calls["native"]) == calls["fresh"] == 1
    repository, prefix, normalized = calls["descriptor"][0]
    assert repository == root and prefix == str(Path(linux.CAPTURE).parent)
    assert len(normalized) == 2311
    assert calls["native"][0][2] is True


@pytest.mark.parametrize(
    "change", ["role", "producer", "missing", "duplicate", "overlap"]
)
def test_changed_owner_contract_refused(
    constructed_reader: Fixture,
    change: str,
) -> None:
    """Reject altered roles, producer claims, memberships and overlapping owners."""
    root, tracked, original, _ = constructed_reader
    owners = copy.deepcopy(original)
    if change == "role":
        owners[0]["role"] = "unresolved"
    elif change == "producer":
        owners[0]["producer_paths"] = ["arbitrary.py"]
    elif change == "missing":
        owners[0]["paths"].pop()
    elif change == "duplicate":
        owners.append(copy.deepcopy(owners[0]))
    else:
        owners.append(
            {
                "owner_id": "other",
                "role": "retained_source",
                "paths": [owners[0]["paths"][0]],
            }
        )
    with pytest.raises(ReportRebuildError):
        linux.validated_linux_r_reference_capture(root, tracked, owners)


@pytest.mark.parametrize(
    "change", ["inventory", "report", "authority", "science", "lock", "link"]
)
def test_current_output_or_source_identity_tamper_refused(
    constructed_reader: Fixture,
    change: str,
) -> None:
    """Refuse changed current outputs, authority, source, lock and symlink states."""
    root, original, owners, _ = constructed_reader
    tracked = dict(original)
    name = sorted(tracked)[0]
    target = root / name
    if change == "inventory":
        tracked[name] = replace(tracked[name], sha256="0" * 64)
    elif change == "authority":
        target = root / linux.CAPTURE
    elif change == "science":
        target = (
            root
            / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reader_fixture_0.py"
        )
    elif change == "lock":
        target = root / "configs/ci/lra-r-source-lock.v1.json"
    if change == "link":
        sibling = root / sorted(tracked)[1]
        target.unlink()
        target.symlink_to(sibling)
    elif change != "inventory":
        target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ReportRebuildError):
        linux.validated_linux_r_reference_capture(root, tracked, owners)


@pytest.mark.parametrize("operation", ["descriptor", "fresh"])
def test_capsule_refusal_propagates_without_fallback(
    constructed_reader: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    """Propagate descriptor and final freshness refusals without a fallback."""
    root, tracked, owners, _ = constructed_reader
    original = linux.validated_descriptor

    def refuse() -> None:
        raise ReportRebuildError("invented capsule refusal")

    def descriptor(repository: Path, prefix: str, normalized: Any) -> Any:
        if operation == "descriptor":
            refuse()
        capsule = original(repository, prefix, normalized)
        return SimpleNamespace(read_source=capsule.read_source, fresh=refuse)

    monkeypatch.setattr(linux, "validated_descriptor", descriptor)
    with pytest.raises(ReportRebuildError, match="invented capsule refusal"):
        linux.validated_linux_r_reference_capture(root, tracked, owners)


@pytest.mark.parametrize("value", [False, True, 0.0, None, "0", 1])
def test_native_zero_is_exact_integer(value: object) -> None:
    """Keep boolean and coerced zero values distinct from native integer success."""
    assert linux._zero(value) is False
    assert linux._zero(0) is True


def test_inactive_unrelated_repository_has_no_invented_capture(tmp_path: Path) -> None:
    """Return no invented retained evidence for an inactive unrelated repository."""
    assert linux.validated_linux_r_reference_capture(tmp_path, {}, []) == ((), {})
