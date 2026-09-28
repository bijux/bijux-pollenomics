"""Check archived standard errors against necessary sum-covariance bounds."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import TypedDict
import zipfile

from .pft_crosswalk import (
    ARCHIVE,
    ISTS_OUTPUT_TAXA,
    OBSERVED_MEAN_GROUPS,
    TBS_OUTPUT_TAXA,
    _members,
    _records,
    _sha,
    _verified_sources,
)


GROUPS = {
    **OBSERVED_MEAN_GROUPS,
    "ISTS": ISTS_OUTPUT_TAXA,
    "TBS": TBS_OUTPUT_TAXA,
}
TOLERANCE = 1e-9
FIELDS = (
    "window",
    "group",
    "grid_rows",
    "below_lower_bound_rows",
    "above_upper_bound_rows",
    "nondegenerate_bound_rows",
    "strictly_inside_bound_rows",
    "minimum_lower_bound_margin",
    "minimum_upper_bound_margin",
)


class WindowRow(TypedDict):
    window: int
    group: str
    grid_rows: int
    below_lower_bound_rows: int
    above_upper_bound_rows: int
    nondegenerate_bound_rows: int
    strictly_inside_bound_rows: int
    minimum_lower_bound_margin: float
    minimum_upper_bound_margin: float


def _bound_row(
    row: dict[str, str], group: str, parts: tuple[str, ...]
) -> tuple[float, float]:
    values = [float(row[part]) for part in parts]
    observed = float(row[group])
    if not all(math.isfinite(value) and value >= 0 for value in (*values, observed)):
        raise ValueError("published uncertainty has a negative or nonfinite value")
    upper = sum(values)
    lower = max(0.0, 2 * max(values) - upper)
    return observed - lower, upper - observed


def build(repository: Path, output: Path) -> dict[str, object]:
    """Retain necessary bounds without claiming an archived covariance replay."""
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output destination required")
    _, inputs = _verified_sources(repository)
    windows: list[WindowRow] = []
    with zipfile.ZipFile(repository / ARCHIVE) as archive:
        members = _members(archive)
        header: list[str] | None = None
        for window in range(1, 26):
            header, rows = _records(archive, members["se"][window], header)
            if (
                not set(GROUPS)
                .union(*(set(parts) for parts in GROUPS.values()))
                .issubset(header)
            ):
                raise ValueError("published uncertainty group columns changed")
            for group, parts in GROUPS.items():
                margins = [_bound_row(row, group, parts) for row in rows]
                windows.append(
                    {
                        "window": window,
                        "group": group,
                        "grid_rows": len(rows),
                        "below_lower_bound_rows": sum(
                            lower < -TOLERANCE for lower, _ in margins
                        ),
                        "above_upper_bound_rows": sum(
                            upper < -TOLERANCE for _, upper in margins
                        ),
                        "nondegenerate_bound_rows": sum(
                            lower + upper > TOLERANCE for lower, upper in margins
                        ),
                        "strictly_inside_bound_rows": sum(
                            lower > TOLERANCE and upper > TOLERANCE
                            for lower, upper in margins
                        ),
                        "minimum_lower_bound_margin": min(
                            lower for lower, _ in margins
                        ),
                        "minimum_upper_bound_margin": min(
                            upper for _, upper in margins
                        ),
                    }
                )
    if len(windows) != 125 or any(row["grid_rows"] != 420 for row in windows):
        raise ValueError("published uncertainty grid/window denominator changed")
    output.mkdir(parents=True)
    table = output / "windows.csv"
    with table.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(windows)
    summary = {
        group: {
            "grid_window_rows": sum(
                row["grid_rows"] for row in windows if row["group"] == group
            ),
            "below_lower_bound_rows": sum(
                row["below_lower_bound_rows"]
                for row in windows
                if row["group"] == group
            ),
            "above_upper_bound_rows": sum(
                row["above_upper_bound_rows"]
                for row in windows
                if row["group"] == group
            ),
            "nondegenerate_bound_rows": sum(
                row["nondegenerate_bound_rows"]
                for row in windows
                if row["group"] == group
            ),
            "strictly_inside_bound_rows": sum(
                row["strictly_inside_bound_rows"]
                for row in windows
                if row["group"] == group
            ),
            "minimum_lower_bound_margin": min(
                row["minimum_lower_bound_margin"]
                for row in windows
                if row["group"] == group
            ),
            "minimum_upper_bound_margin": min(
                row["minimum_upper_bound_margin"]
                for row in windows
                if row["group"] == group
            ),
            "addends": GROUPS[group],
        }
        for group in GROUPS
    }
    report: dict[str, object] = {
        "schema_version": "landclim-published-se-sum-bounds.v1",
        "dataset_doi": "10.1594/PANGAEA.937075",
        "inputs": inputs,
        "absolute_tolerance_percentage_points": TOLERANCE,
        "necessary_bounds": "max(0, 2*max(component_SE)-sum(component_SE)) <= aggregate_SE <= sum(component_SE)",
        "summary": summary,
        "window_csv_sha256": _sha(table.read_bytes()),
        "same_draw_covariance_aggregation_verified": False,
        "interpretation": (
            "Archived standard errors satisfy necessary covariance-feasibility "
            "bounds for observed mean-addend groups. This neither identifies "
            "the original covariance nor replays the published delta method."
        ),
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.repository, args.output)


if __name__ == "__main__":
    main()
