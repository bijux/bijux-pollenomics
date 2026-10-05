"""Require exact scientific capture membership and immutable actual source bytes."""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.nordic_static_basin import (
    CAPTURE_PINS,
    OWNER,
    CAPTURE_AUTHORITY,
    validated_nordic_static_basin_captures,
)


@pytest.fixture
def capture_repository(tmp_path: Path):
    repository = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages/bijux-pollenomics-dev/pyproject.toml").is_file()
    )
    tracked = {}
    for name, expected in CAPTURE_PINS.items():
        source = repository / name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        tracked[name] = InventoryEntry(
            path=name.removeprefix("docs/report/"),
            kind="file",
            size=source.stat().st_size,
            sha256=expected,
            canonical_sha256=expected,
        )
    owners = [
        {
            "owner_id": OWNER,
            "role": "retained_source",
            "paths": sorted(CAPTURE_PINS),
            "producer_paths": [],
            "producer_inputs": [],
        }
    ]
    return tmp_path, tracked, owners


def test_exact_scientific_captures_preserve_original_authority(capture_repository):
    root, tracked, owners = capture_repository
    entries, evidence = validated_nordic_static_basin_captures(root, tracked, owners)
    assert len(entries) == 22
    assert evidence["reviewed_capture_sha256"] == CAPTURE_PINS
    assert evidence["original_capture_authority"] == CAPTURE_AUTHORITY
    assert (
        evidence["native_publication_capture_authority"]["acquisition"]["candidate"]
        != CAPTURE_AUTHORITY["original_scientific_candidate"]
    )


def test_modified_source_capture_refuses_even_with_original_inventory(
    capture_repository,
):
    root, tracked, owners = capture_repository
    path = root / sorted(CAPTURE_PINS)[0]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ReportRebuildError, match="bytes changed"):
        validated_nordic_static_basin_captures(root, tracked, owners)


def test_missing_source_capture_refuses(capture_repository):
    root, tracked, owners = capture_repository
    (root / sorted(CAPTURE_PINS)[0]).unlink()
    with pytest.raises(ReportRebuildError, match="input refused"):
        validated_nordic_static_basin_captures(root, tracked, owners)


def test_capture_symlink_cannot_bypass_source_custody(capture_repository):
    root, tracked, owners = capture_repository
    path = root / sorted(CAPTURE_PINS)[0]
    sibling = path.with_suffix(".protected.json")
    path.rename(sibling)
    path.symlink_to(sibling.name)
    with pytest.raises(ReportRebuildError, match="input refused"):
        validated_nordic_static_basin_captures(root, tracked, owners)


def test_extra_retained_owner_cannot_extend_capture_admission(capture_repository):
    root, tracked, owners = capture_repository
    owners.append({**owners[0], "owner_id": OWNER + "/extra"})
    with pytest.raises(ReportRebuildError, match="owner differs"):
        validated_nordic_static_basin_captures(root, tracked, owners)


def test_configuration_role_cannot_replace_retained_capture(capture_repository):
    root, tracked, owners = capture_repository
    owners[0]["role"] = "maintained_configuration"
    with pytest.raises(ReportRebuildError, match="owner differs"):
        validated_nordic_static_basin_captures(root, tracked, owners)


def test_partial_capture_family_cannot_be_admitted(capture_repository):
    root, tracked, owners = capture_repository
    del tracked[sorted(CAPTURE_PINS)[0]]
    with pytest.raises(ReportRebuildError, match="bytes changed"):
        validated_nordic_static_basin_captures(root, tracked, owners)


def test_unrelated_candidate_without_capture_family_has_no_admission(tmp_path):
    assert validated_nordic_static_basin_captures(tmp_path, {}, []) == ((), {})
