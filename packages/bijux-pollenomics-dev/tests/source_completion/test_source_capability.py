"""A captured source never silently becomes an admitted country value."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.source_capability import derive

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module")
def ledgers() -> tuple[dict[str, object], dict[str, object]]:
    stage = json.loads(
        (ROOT / "data/source_family_evidence_stage_matrix.json").read_text()
    )
    coverage = json.loads((ROOT / "data/country_dimension_coverage.json").read_text())
    return stage, coverage


def test_complete_cube_preserves_country_dimensions_and_null_counts(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = ledgers
    report = derive(stage, coverage)
    assert report["source_families"] == 11
    assert report["country_entries"] and len(report["country_entries"]) == 66
    assert report["country_cells"] == 198
    entries = {
        (row["source_family"], row["country_code"]): row
        for row in report["country_entries"]
    }
    hyde = entries["hyde", "SE"]["dimensions"]
    assert {value["availability_status"] for value in hyde.values()} == {"blocked"}
    assert all(
        all(number is None for number in value["counts"].values())
        for value in hyde.values()
    )
    sead = entries["sead", "SE"]["dimensions"]
    assert sead["source_reported"]["counts"]["sites"] == 0
    assert sead["publication"]["counts"]["sites"] == 1925
    assert sead["source_reported"]["availability_status"] == "zero_observations"


def test_duplicate_country_cell_refuses(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = deepcopy(ledgers)
    cells = coverage["cells"]
    assert isinstance(cells, list)
    cells[-1] = cells[0]
    with pytest.raises(ValueError, match="Cartesian"):
        derive(stage, coverage)


def test_negative_count_refuses(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = deepcopy(ledgers)
    cells = coverage["cells"]
    assert isinstance(cells, list)
    cells[0]["counts"]["sites"] = -1
    with pytest.raises(ValueError, match="counts invalid"):
        derive(stage, coverage)


def test_missing_source_stage_refuses(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = deepcopy(ledgers)
    rows = stage["rows"]
    assert isinstance(rows, list)
    rows.pop()
    with pytest.raises(ValueError, match="denominator"):
        derive(stage, coverage)
