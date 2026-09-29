"""Published standard errors and necessary covariance-bound replay."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics_dev.essd_reproduction.pft_uncertainty_bounds import (
    _bound_row,
    build,
)

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = (
    REPOSITORY
    / "docs/report/publication-replay/landclim-pft-crosswalk/uncertainty-bounds"
)


def test_impossible_sum_standard_errors_cross_a_necessary_bound() -> None:
    row = {"A": "3", "B": "1", "sum": "0.5"}
    lower_margin, _ = _bound_row(row, "sum", ("A", "B"))
    assert lower_margin == -1.5
    row["sum"] = "5"
    _, upper_margin = _bound_row(row, "sum", ("A", "B"))
    assert upper_margin == -1


def test_all_published_uncertainty_rows_replay_within_bounds(tmp_path: Path) -> None:
    output = tmp_path / "bounds"
    report = build(REPOSITORY, output)
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert set(summary) == {"ET", "ST", "OL", "ISTS", "TBS"}
    for group in summary.values():
        assert isinstance(group, dict)
        assert group["grid_window_rows"] == 10_500
        assert group["below_lower_bound_rows"] == 0
        assert group["above_upper_bound_rows"] == 0
        assert group["nondegenerate_bound_rows"] == group["strictly_inside_bound_rows"]
    assert report["same_draw_covariance_aggregation_verified"] is False
    for name in ("windows.csv", "report.json"):
        assert (output / name).read_bytes() == (GOVERNED / name).read_bytes()
    assert (
        json.loads((output / "report.json").read_text())["inputs"] == report["inputs"]
    )
