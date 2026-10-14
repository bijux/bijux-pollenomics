"""Retained author evaluations keep native epochs, report bytes, and source ownership exact."""

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
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_site_evaluations import (
    CAPTURE,
    OWNERS,
    _native_references,
    _zero,
    validated_author_site_evaluation_captures,
)

Fixture = tuple[Path, dict[str, InventoryEntry], list[dict[str, Any]]]
REPOSITORY = Path(__file__).resolve().parents[5]


@pytest.fixture(scope="module")
def retained_view(tmp_path_factory: pytest.TempPathFactory) -> Fixture:
    root = tmp_path_factory.mktemp("retained-author-evaluations")
    source = REPOSITORY / CAPTURE
    packet = root / CAPTURE
    shutil.copytree(source.parent, packet.parent)
    capture = json.loads(source.read_bytes())
    tracked: dict[str, InventoryEntry] = {}
    for row in capture["report_outputs"]:
        name = row["path"]
        actual = root / name
        actual.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(packet.parent / row["retained_path"], actual)
        tracked[name] = InventoryEntry(
            name.removeprefix("docs/report/"),
            "file",
            row["published"]["bytes"],
            row["published"]["sha256"],
            row["published"]["sha256"],
        )
    for row in capture["current_scientific_source_projection"]:
        name = row["path"]
        actual = root / name
        actual.parent.mkdir(parents=True, exist_ok=True)
        candidates = [
            packet.parent / "executions" / lane / "first-party-inputs" / name
            for lane in ["uncertainty", "profile", "holdout"]
        ]
        owned = next(path for path in candidates if path.is_file())
        shutil.copyfile(owned, actual)
    owners = [
        {
            "owner_id": owner,
            "role": "retained_source",
            "paths": sorted(name for name in tracked if name.startswith(prefix)),
            "producer_paths": [],
            "producer_inputs": [],
        }
        for owner, (prefix, _) in OWNERS.items()
    ]
    return root, tracked, owners


def test_actual_three_execution_eight_report_transport(retained_view: Fixture) -> None:
    entries, evidence = validated_author_site_evaluation_captures(*retained_view)
    assert len(entries) == 8
    owner_ids = evidence["owner_ids"]
    assert isinstance(owner_ids, list) and len(owner_ids) == 3
    assert evidence["current_scientific_projection"] == 178
    candidates = evidence["executed_source_candidates"]
    assert isinstance(candidates, dict) and len(set(candidates.values())) == 3


@pytest.mark.parametrize(
    "change", ["role", "producer", "input", "missing", "duplicate", "paths", "overlap"]
)
def test_changed_owner_contract_refused(retained_view: Fixture, change: str) -> None:
    root, tracked, original = retained_view
    owners = copy.deepcopy(original)
    if change == "role":
        owners[0]["role"] = "unresolved"
    elif change == "producer":
        owners[0]["producer_paths"] = ["not-owned.py"]
    elif change == "input":
        owners[0]["producer_inputs"] = ["not-owned.json"]
    elif change == "missing":
        owners.pop()
    elif change == "duplicate":
        owners.append(copy.deepcopy(owners[0]))
    elif change == "paths":
        owners[0]["paths"] = []
    else:
        owners.append(
            {
                "owner_id": "unrelated",
                "role": "retained_source",
                "paths": owners[0]["paths"],
            }
        )
    with pytest.raises(ReportRebuildError):
        validated_author_site_evaluation_captures(root, tracked, owners)


@pytest.mark.parametrize("change", ["missing", "kind", "hash", "size"])
def test_current_inventory_is_not_replaced_by_retained_guess(
    retained_view: Fixture, change: str
) -> None:
    root, old, owners = retained_view
    tracked = dict(old)
    key = next(iter(tracked))
    if change == "missing":
        tracked.pop(key)
    elif change == "kind":
        tracked[key] = replace(tracked[key], kind="symlink")
    elif change == "hash":
        tracked[key] = replace(tracked[key], sha256="0" * 64)
    else:
        tracked[key] = replace(tracked[key], size=tracked[key].size + 1)
    with pytest.raises(ReportRebuildError):
        validated_author_site_evaluation_captures(root, tracked, owners)


@pytest.mark.parametrize("change", ["source", "report", "packet", "extra", "link"])
def test_changed_physical_source_or_report_refused(
    retained_view: Fixture, change: str
) -> None:
    root, tracked, owners = retained_view
    capture_path = root / CAPTURE
    capture = json.loads(capture_path.read_bytes())
    if change == "source":
        path = root / capture["current_scientific_source_projection"][0]["path"]
    elif change == "report":
        path = root / next(iter(tracked))
    elif change == "packet":
        path = capture_path
    elif change == "extra":
        path = capture_path.parent / "unlisted.py"
    else:
        path = capture_path.parent / "unexpected-link"
    before = path.read_bytes() if path.exists() else None
    try:
        if change == "link":
            path.symlink_to(capture_path)
        else:
            path.write_bytes((before or b"") + b"changed")
        with pytest.raises(ReportRebuildError):
            validated_author_site_evaluation_captures(root, tracked, owners)
    finally:
        if before is None:
            path.unlink()
        else:
            path.write_bytes(before)


def test_native_stage_cannot_be_relabelled_without_authority(
    retained_view: Fixture,
) -> None:
    root, _, _ = retained_view
    capture = json.loads((root / CAPTURE).read_bytes())
    packet = (root / CAPTURE).parent
    path = packet / "executions/holdout/terminal.json"
    before = path.read_bytes()
    changed = json.loads(before)
    changed["stages"][0]["actual_exit"] = False
    try:
        path.write_text(json.dumps(changed))
        with pytest.raises(ReportRebuildError):
            _native_references(packet, capture)
    finally:
        path.write_bytes(before)


@pytest.mark.parametrize("value", [False, None, "0", 0.0, 1])
def test_native_zero_is_an_exact_integer(value: object) -> None:
    assert _zero(value) is False


def test_inactive_unrelated_repository_has_no_invented_capture(tmp_path: Path) -> None:
    assert validated_author_site_evaluation_captures(tmp_path, {}, []) == ((), {})
