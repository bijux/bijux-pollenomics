"""Write finite privately retained distance and context-membership sensitivity products."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import pyproj

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .membership import evaluate
from .source import load


def csv_file(path: Path, rows: list[dict[str, Any]], empty_fields: list[str]) -> None:
    """Write ordered tabular rows with declared empty-output columns."""
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(rows[0]) if rows else empty_fields
        )
        writer.writeheader()
        writer.writerows(rows)


def geodesic_metadata() -> dict[str, object]:
    """Declare the actual backend and unchanged distance/membership contract."""
    return {
        "library": "pyproj",
        "version": pyproj.__version__,
        "PROJ": pyproj.proj_version_str,
        "ellipsoid": "WGS84",
        "semi_major_axis_metres": 6378137.0,
        "inverse_flattening": 298.257223563,
        "coordinate_order": "longitude, latitude",
        "units_returned": "metres",
        "retained_sphere_radius_km": 6371.0088,
        "eligibility": "full returned distance<=radius; no rounding or tolerance changes membership",
    }


def main() -> int:
    """Write source-bound distance and membership comparison artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = require_absent_artifact_output(args.repository, args.output)
    records, centres, original = load(args.repository)
    summary, distances, cells, changes = evaluate(records, centres, original)
    summary["geodesic"] = geodesic_metadata()
    output.mkdir()
    (output / "report.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    csv_file(output / "feature-distances.csv", distances, [])
    csv_file(output / "window-cells.csv", cells, [])
    csv_file(
        output / "membership-changes.csv",
        changes,
        [
            "centre",
            "radius_km",
            "record_id",
            "site_uuid",
            "chronology_status",
            "sphere_inside",
            "wgs84_inside",
            "sphere_km",
            "wgs84_km",
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
