"""Publish aggregate geographic sensitivity while retaining row details privately."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .membership import evaluate
from .report import csv_file, geodesic_metadata
from .source import load


def main() -> int:
    """Publish geographic sensitivity without private feature rows."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = require_absent_artifact_output(args.repository, args.output)
    records, centres, original = load(args.repository)
    summary, _distances, cells, _changes = evaluate(records, centres, original)
    summary["geodesic"] = geodesic_metadata()
    output.mkdir()
    (output / "geodesic-sensitivity.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    csv_file(output / "geodesic-window-cells.csv", cells, [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
