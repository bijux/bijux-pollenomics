"""Keep retained native-source transport distinct from current model execution."""

from __future__ import annotations

import copy
from dataclasses import replace
import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.linux_r_reference import (
    CAPTURE,
    FAMILY,
    OWNER,
    _native_references,
    _zero,
    validated_linux_r_reference_capture,
)

Fixture = tuple[Path, dict[str, InventoryEntry], list[dict[str, Any]]]

REPOSITORY = Path(__file__).resolve().parents[5]


@pytest.fixture(scope="module")
def retained_view(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, InventoryEntry], list[dict[str, Any]]]:
    root = tmp_path_factory.mktemp("retained-linux-capture")
    source = REPOSITORY / CAPTURE
    packet = root / CAPTURE
    shutil.copytree(source.parent, packet.parent)
    capture = json.loads(source.read_bytes())
    tracked = {}
    for row in capture["current_report_owner"]["outputs"]:
        name = row["path"]
        actual = root / name
        actual.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(packet.parent / "retained" / name.removeprefix(FAMILY), actual)
        tracked[name] = InventoryEntry(
            name.removeprefix("docs/report/"),
            "file",
            row["bytes"],
            row["sha256"],
            row["sha256"],
        )
    for row in capture["current_scientific_source_projection"]["members"]:
        name = row["relative_path"]
        actual = root / name
        actual.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(packet.parent / "source" / name, actual)
    lock_name = "configs/ci/lra-r-source-lock.v1.json"
    lock = root / lock_name
    lock.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(packet.parent / "source" / lock_name, lock)
    owner = {
        "owner_id": OWNER,
        "role": "retained_source",
        "paths": sorted(tracked),
        "producer_paths": [],
        "producer_inputs": [],
    }
    return root, tracked, [owner]


def test_actual_complete_retained_transport(retained_view: Fixture) -> None:
    root, tracked, owners = retained_view
    entries, evidence = validated_linux_r_reference_capture(root, tracked, owners)
    assert len(entries) == 137
    assert evidence["source_files"] == 2148
    assert evidence["scientific_current_projection"] == 127
    assert evidence["historical_source_gap_retained"] is True


@pytest.mark.parametrize(
    "change", ["role", "producer", "missing", "duplicate", "overlap"]
)
def test_changed_owner_contract_refused(retained_view: Fixture, change: str) -> None:
    root, tracked, original = retained_view
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
        validated_linux_r_reference_capture(root, tracked, owners)


@pytest.mark.parametrize(
    "change",
    ["inventory", "report", "member", "authority", "extra", "link", "science", "lock"],
)
def test_physical_or_inventory_tampering_refused(
    retained_view: Fixture, change: str
) -> None:
    root, original, owners = retained_view
    tracked = dict(original)
    name = sorted(tracked)[0]
    packet = (root / CAPTURE).parent
    capture = json.loads((root / CAPTURE).read_bytes())
    target = root / name
    if change == "inventory":
        tracked[name] = replace(tracked[name], sha256="0" * 64)
        with pytest.raises(ReportRebuildError):
            validated_linux_r_reference_capture(root, tracked, owners)
        return
    if change == "member":
        target = packet / capture["members"][0]["path"]
    elif change == "authority":
        target = root / CAPTURE
    elif change == "science":
        target = (
            root
            / capture["current_scientific_source_projection"]["members"][0][
                "relative_path"
            ]
        )
    elif change == "lock":
        target = root / "configs/ci/lra-r-source-lock.v1.json"
    elif change == "extra":
        target = packet / "unlisted.json"
        target.write_bytes(b"{}")
        try:
            with pytest.raises(ReportRebuildError):
                validated_linux_r_reference_capture(root, tracked, owners)
        finally:
            target.unlink()
        return
    original_bytes = target.read_bytes()
    try:
        if change == "link":
            target.unlink()
            target.symlink_to(packet / "retained" / name.removeprefix(FAMILY))
        else:
            target.write_bytes(original_bytes + b" ")
        with pytest.raises(ReportRebuildError):
            validated_linux_r_reference_capture(root, tracked, owners)
    finally:
        if target.is_symlink():
            target.unlink()
        target.write_bytes(original_bytes)


@pytest.mark.parametrize("value", [False, True, 0.0, None, "0", 1])
def test_native_zero_is_exact_integer(value: object) -> None:
    assert _zero(value) is False
    assert _zero(0) is True


def test_old_epoch_native_reference_cannot_be_relabelled(
    retained_view: Fixture,
) -> None:
    root, _, _ = retained_view
    packet = (root / CAPTURE).parent
    capture = json.loads((root / CAPTURE).read_bytes())
    capture["source_candidate"] = "current"
    with pytest.raises(ReportRebuildError):
        _native_references(packet, capture)
