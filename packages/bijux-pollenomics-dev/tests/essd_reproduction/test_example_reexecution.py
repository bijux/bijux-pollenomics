"""Bounded original-R/native LandClim example receipt regressions."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from bijux_pollenomics_dev.essd_reproduction.example_reexecution import (
    GRID_IDS,
    TOLERANCES,
    _native_output_closure,
    _source_hashes,
    _verify_comparison,
    execute,
    verify_report,
)

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = (
    REPOSITORY
    / "docs/report/publication-replay/landclim-example-reexecution/report.json"
)


def _comparison() -> dict[str, object]:
    def check(kind: str) -> dict[str, object]:
        return {
            "passed": True,
            "undefined_masks_equal": True,
            **TOLERANCES[kind],
        }

    return {
        "profile": "landclimii-2016-release-source-v1",
        "coverage": "two_author_example_grids_only_not_full_1128_record_study",
        "grids": [
            {
                "grid_id": grid,
                "sites": sites,
                "bins": 25,
                "taxa": 31,
                "passed": True,
                "checks": {
                    "regional_cover": check("cover"),
                    "regional_se": check("se"),
                    "site_counts_equal": True,
                    "sites": [
                        {"cover": check("cover"), "se": check("se")}
                        for _ in range(sites)
                    ],
                },
            }
            for grid, sites in zip(GRID_IDS, (9, 8), strict=True)
        ],
    }


def test_current_native_and_oracle_source_closure_is_explicit() -> None:
    hashes = _source_hashes(REPOSITORY)
    assert len(hashes) >= 40
    assert all(len(digest) == 64 for digest in hashes.values())
    assert any(name.endswith("run_author_replay.R") for name in hashes)
    assert any(name.endswith("compare_author_examples.py") for name in hashes)


def test_exact_two_grid_comparison_is_accepted() -> None:
    _verify_comparison(_comparison())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("grid", "999", "two declared author grids"),
        ("sites", 7, "site denominator"),
        ("mask", False, "Numerical parity"),
        ("tolerance", 1e-5, "Numerical parity"),
    ],
)
def test_changed_scope_or_numerical_claim_is_refused(
    field: str, value: object, message: str
) -> None:
    comparison = deepcopy(_comparison())
    grids = comparison["grids"]
    assert isinstance(grids, list)
    first = grids[0]
    if field == "grid":
        first["grid_id"] = value
    elif field == "sites":
        first["sites"] = value
    elif field == "mask":
        first["checks"]["regional_se"]["undefined_masks_equal"] = value
    else:
        first["checks"]["regional_cover"]["atol"] = value
    with pytest.raises(ValueError, match=message):
        _verify_comparison(comparison)


def test_existing_output_destination_is_refused_before_execution(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "existing"
    destination.mkdir()
    with pytest.raises(ValueError, match="Absent run and governed report"):
        execute(REPOSITORY, tmp_path, destination, tmp_path / "report.json")


def test_governed_fresh_run_retains_two_grid_numerical_checks() -> None:
    result = verify_report(GOVERNED)
    assert result == {
        "passed": True,
        "grids": ["512", "562"],
        "raw_bytes_verified": False,
    }
    report = json.loads(GOVERNED.read_text())
    assert report["repository_head_at_execution"]
    assert len(report["native_source_files"]) >= 40
    assert report["admission"]["full_study_reproduction"] is False
    assert [
        grid["available_site_bins"] for grid in report["native_comparison"]["grids"]
    ] == [97, 87]
    assert [report["native_output_checksums"][grid]["files"] for grid in GRID_IDS] == [
        53,
        52,
    ]


def test_changed_governed_tolerance_is_refused(tmp_path: Path) -> None:
    report = json.loads(GOVERNED.read_text())
    report["tolerances"]["se"]["atol"] = 1e-3
    altered = tmp_path / "report.json"
    altered.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Prospective numerical tolerances"):
        verify_report(altered)


def test_raw_output_hashes_can_be_rechecked_when_retained() -> None:
    configured = os.environ.get("BIJUX_LANDCLIM_EXAMPLE_RUN")
    if configured is None:
        pytest.skip("Fresh local R/native output was not supplied")
    result = verify_report(GOVERNED, Path(configured))
    assert result["raw_bytes_verified"] is True


def test_native_output_byte_drift_is_refused(tmp_path: Path) -> None:
    for grid in GRID_IDS:
        directory = tmp_path / "comparison" / grid
        directory.mkdir(parents=True)
        content = b"source output\n"
        (directory / "regional-cover.csv").write_bytes(content)
        (directory / "checksums.json").write_text(
            json.dumps(
                {
                    "regional-cover.csv": {
                        "bytes": len(content),
                        "sha256": sha256(content).hexdigest(),
                    }
                }
            )
        )
    assert _native_output_closure(tmp_path)["512"]["files"] == 1
    (tmp_path / "comparison/562/regional-cover.csv").write_bytes(b"changed\n")
    with pytest.raises(ValueError, match="Native output bytes changed"):
        _native_output_closure(tmp_path)
