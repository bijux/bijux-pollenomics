"""A captured source never silently becomes an admitted country value."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.source_capability import (
    _validate_status_counts,
    derive,
)

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


def test_country_consumer_rejects_numeric_zero_in_blocked_cell(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = deepcopy(ledgers)
    cells = coverage["cells"]
    assert isinstance(cells, list)
    blocked = next(cell for cell in cells if cell["availability_status"] == "blocked")
    blocked["counts"]["sites"] = 0
    with pytest.raises(ValueError, match="blocked country coverage"):
        derive(stage, coverage)


@pytest.mark.parametrize(
    ("status", "counts", "reason"),
    [
        ("zero_observations", {"sites": None}, "requires only observed zeros"),
        ("zero_observations", {"sites": 1}, "requires only observed zeros"),
        ("blocked", {"sites": 0}, "must not carry numeric counts"),
        ("not_available_from_source", {"sites": 0}, "must not carry numeric counts"),
        ("not_applicable", {"sites": 0}, "must not carry numeric counts"),
        ("available_not_collected", {"sites": 0}, "must not carry numeric counts"),
        ("unresolved", {"sites": None}, "requires source counts"),
        ("unknown", {"sites": None}, "Unknown country coverage"),
    ],
)
def test_availability_status_refuses_false_numeric_claims(
    status: str, counts: dict[str, int | None], reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        _validate_status_counts(status, counts)


@pytest.mark.parametrize(
    ("status", "counts"),
    [
        ("zero_observations", {"sites": 0, "observations": None}),
        ("blocked", {"sites": None}),
        ("available_not_collected", {"sites": None}),
        ("unresolved", {"sites": 7, "accepted_records": 0}),
    ],
)
def test_availability_status_preserves_distinct_valid_states(
    status: str, counts: dict[str, int | None]
) -> None:
    _validate_status_counts(status, counts)
