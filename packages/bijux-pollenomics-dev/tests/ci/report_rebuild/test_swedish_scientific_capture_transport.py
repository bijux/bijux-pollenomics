"""Require exact scientific capture membership and immutable actual source bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.swedish_static_basin import (
    CAPTURE_PINS,
    OWNER,
    OWNER_PATHS,
    validated_swedish_static_basin_captures,
)

_CaptureFixture = tuple[Path, dict[str, InventoryEntry], list[dict[str, object]]]


@pytest.fixture
def capture_repository(tmp_path: Path) -> _CaptureFixture:
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
    owners: list[dict[str, object]] = [
        {
            "owner_id": owner,
            "role": "retained_source",
            "paths": paths,
            "producer_paths": [],
            "producer_inputs": [],
        }
        for owner, paths in OWNER_PATHS.items()
    ]
    return tmp_path, tracked, owners


def test_exact_scientific_captures_preserve_original_authority(
    capture_repository: _CaptureFixture,
) -> None:
    root, tracked, owners = capture_repository
    entries, evidence = validated_swedish_static_basin_captures(root, tracked, owners)
    assert len(entries) == 10
    assert evidence["reviewed_capture_sha256"] == CAPTURE_PINS
    assert evidence["owner_paths"] == OWNER_PATHS


def test_modified_source_capture_refuses_even_with_original_inventory(
    capture_repository: _CaptureFixture,
) -> None:
    root, tracked, owners = capture_repository
    path = root / sorted(CAPTURE_PINS)[0]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ReportRebuildError, match="bytes changed"):
        validated_swedish_static_basin_captures(root, tracked, owners)


def test_missing_source_capture_refuses(capture_repository: _CaptureFixture) -> None:
    root, tracked, owners = capture_repository
    (root / sorted(CAPTURE_PINS)[0]).unlink()
    with pytest.raises(ReportRebuildError, match="input refused"):
        validated_swedish_static_basin_captures(root, tracked, owners)


def test_capture_symlink_cannot_bypass_source_custody(
    capture_repository: _CaptureFixture,
) -> None:
    root, tracked, owners = capture_repository
    path = root / sorted(CAPTURE_PINS)[0]
    sibling = path.with_suffix(".protected.json")
    path.rename(sibling)
    path.symlink_to(sibling.name)
    with pytest.raises(ReportRebuildError, match="input refused"):
        validated_swedish_static_basin_captures(root, tracked, owners)


def test_extra_retained_owner_cannot_extend_capture_admission(
    capture_repository: _CaptureFixture,
) -> None:
    root, tracked, owners = capture_repository
    owners.append({**owners[0], "owner_id": OWNER + "/extra"})
    with pytest.raises(ReportRebuildError, match="owner differs"):
        validated_swedish_static_basin_captures(root, tracked, owners)


def test_configuration_role_cannot_replace_retained_capture(
    capture_repository: _CaptureFixture,
) -> None:
    root, tracked, owners = capture_repository
    owners[0]["role"] = "maintained_configuration"
    with pytest.raises(ReportRebuildError, match="owner differs"):
        validated_swedish_static_basin_captures(root, tracked, owners)


def test_partial_capture_family_cannot_be_admitted(
    capture_repository: _CaptureFixture,
) -> None:
    root, tracked, owners = capture_repository
    del tracked[sorted(CAPTURE_PINS)[0]]
    with pytest.raises(ReportRebuildError, match="bytes changed"):
        validated_swedish_static_basin_captures(root, tracked, owners)


def test_unrelated_candidate_without_capture_family_has_no_admission(
    tmp_path: Path,
) -> None:
    assert validated_swedish_static_basin_captures(tmp_path, {}, []) == ((), {})


@pytest.mark.parametrize("invalid_paths", ["captured/member.json", [7]])
def test_malformed_retained_owner_paths_refuse_capture_admission(
    capture_repository: _CaptureFixture, invalid_paths: object
) -> None:
    """Refuse malformed owner paths before comparing captured source membership."""
    root, tracked, owners = capture_repository
    owners[0]["paths"] = invalid_paths
    with pytest.raises(ReportRebuildError, match="paths must be a string list"):
        validated_swedish_static_basin_captures(root, tracked, owners)


REFERENCE_OWNER = (
    "pollen-reconstruction/swedish-static-basin-scenarios/native-r-reference-account"
)
REFERENCE_PATH = "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/independent-r-reference.json"


def test_independent_reference_retains_distinct_original_epochs(
    capture_repository: _CaptureFixture,
) -> None:
    root, tracked, owners = capture_repository
    before = json.dumps(owners, sort_keys=True)
    entries, evidence = validated_swedish_static_basin_captures(root, tracked, owners)
    assert len(entries) == 10 and before == json.dumps(owners, sort_keys=True)
    assert REFERENCE_PATH.removeprefix("docs/report/") in [
        entry.path for entry in entries
    ]
    value = json.loads((root / REFERENCE_PATH).read_bytes())
    assert (
        value["epochs"]["saved_report_source"]
        == "1988f522002e8bb5362083b9e8b46bd4fa17685e"
    )
    assert (
        value["epochs"]["actual_reference_and_comparison_execution"]
        == "6763e5574b56863089bcaba45bdc307bfca1d71b"
    )
    assert value["population"]["actual_saved_comparisons_total"] == 16868
    assert value["population"]["R_only_zero_PPE_control_cells_total"] == 2572
    assert "publication transport is a later epoch" in str(evidence["source_scope"])


@pytest.mark.parametrize(
    "mutation", ["missing-owner", "extra-path", "role", "producer", "overlap"]
)
def test_reference_declaration_cannot_expand_old_capture_family(
    capture_repository: _CaptureFixture, mutation: str
) -> None:
    root, tracked, owners = capture_repository
    row = next(row for row in owners if row["owner_id"] == REFERENCE_OWNER)
    if mutation == "missing-owner":
        owners.remove(row)
    elif mutation == "extra-path":
        row["paths"] = [REFERENCE_PATH, REFERENCE_PATH + ".extra"]
    elif mutation == "role":
        row["role"] = "maintained_configuration"
    elif mutation == "producer":
        row["producer_paths"] = ["run.py"]
    else:
        owners.append({**row, "owner_id": REFERENCE_OWNER + "/unreviewed"})
    with pytest.raises(ReportRebuildError, match="owner differs|declaration differs"):
        validated_swedish_static_basin_captures(root, tracked, owners)


@pytest.mark.parametrize("mutation", ["relabel", "refused"])
def test_changed_reference_refuses_even_with_resealed_inventory(
    capture_repository: _CaptureFixture, mutation: str
) -> None:
    root, tracked, owners = capture_repository
    target = root / REFERENCE_PATH
    value = json.loads(target.read_bytes())
    if mutation == "relabel":
        value["epochs"]["actual_reference_and_comparison_execution"] = "f" * 40
    else:
        value["outcomes"]["collector_exit"] = 1
    raw = (json.dumps(value, indent=2) + "\n").encode()
    target.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    tracked[REFERENCE_PATH] = InventoryEntry(
        path=REFERENCE_PATH.removeprefix("docs/report/"),
        kind="file",
        size=len(raw),
        sha256=digest,
        canonical_sha256=digest,
    )
    with pytest.raises(ReportRebuildError, match="bytes changed"):
        validated_swedish_static_basin_captures(root, tracked, owners)
