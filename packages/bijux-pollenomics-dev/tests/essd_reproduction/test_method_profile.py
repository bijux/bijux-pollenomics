"""Content-bound author method and native example identity regressions."""

from __future__ import annotations

from copy import deepcopy
import csv
import json
import os
from pathlib import Path

import pytest

from bijux_pollenomics_dev.essd_reproduction.method_profile import (
    PARITY,
    _checked_private,
    _example_inputs,
    _pft_evidence,
    build,
)

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = REPOSITORY / "docs/report/publication-replay/landclim-method-profile"


@pytest.fixture(scope="module")
def private_root() -> Path:
    configured = os.environ.get("BIJUX_LANDCLIM_AUTHOR_REFERENCE")
    if configured is None:
        pytest.skip("Private LandClim author snapshot was not supplied")
    return Path(configured).expanduser()


def test_pft_source_versions_are_kept_separate() -> None:
    evidence = _pft_evidence(REPOSITORY)
    assert evidence["paper_prose_claim"] == 12
    assert evidence["dataset_description_claim"] == 11
    assert evidence["parameter_table_nonblank_codes"] == 12
    assert evidence["mean_se_output_pft_position_columns"] == 13
    assert evidence["mean_se_output_files_checked"] == 50
    assert evidence["output_code_missing_from_parameter_table"] == ["ISTS"]
    assert str(evidence["classification_admission"]).startswith("blocked")


def test_private_examples_bind_all_seventeen_sites_and_native_axes(
    private_root: Path,
) -> None:
    hashes = _checked_private(private_root)
    retained = json.loads((REPOSITORY / PARITY / "report.json").read_text())
    grids = {row["grid_id"]: row for row in retained["grids"]}
    rows = _example_inputs(private_root, hashes, grids)
    assert len(rows) == 17
    assert {row["grid_id"] for row in rows} == {"512", "562"}
    assert sum(row["grid_id"] == "512" for row in rows) == 9
    assert sum(row["grid_id"] == "562" for row in rows) == 8
    assert all(row["source_model_code"] == "2" for row in rows)
    assert all(row["native_grid_taxa"] == 31 for row in rows)
    assert all(row["raw_input_sha256"] != row["prepared_input_sha256"] for row in rows)


def test_native_grid_coverage_drift_is_refused(private_root: Path) -> None:
    hashes = _checked_private(private_root)
    retained = json.loads((REPOSITORY / PARITY / "report.json").read_text())
    grids = deepcopy({row["grid_id"]: row for row in retained["grids"]})
    grids["512"]["sites"] = 8
    with pytest.raises(ValueError, match="native example coverage"):
        _example_inputs(private_root, hashes, grids)


def test_private_snapshot_identity_drift_is_refused(tmp_path: Path) -> None:
    (tmp_path / "snapshot-manifest.json").write_text("{}\n")
    with pytest.raises(ValueError, match="snapshot manifest identity"):
        _checked_private(tmp_path)


def test_governed_method_report_replays_byte_identically(
    tmp_path: Path, private_root: Path
) -> None:
    output = tmp_path / "profile"
    build(REPOSITORY, private_root, output)
    for name in ("method_crosswalk.csv", "example_inputs.csv", "report.json"):
        assert (output / name).read_bytes() == (GOVERNED / name).read_bytes()
    with (GOVERNED / "example_inputs.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 17
    assert all(
        row["identity_status"] == "source_members_verified_native_grid_axes_matched"
        for row in rows
    )
