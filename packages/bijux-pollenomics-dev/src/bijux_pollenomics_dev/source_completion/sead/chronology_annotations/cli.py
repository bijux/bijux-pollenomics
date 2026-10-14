"""Write governed aggregate reports and separately retained native annotation witnesses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .report import build


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--retained-artifacts-root", type=Path)
    args = parser.parse_args()
    root = args.repository
    output = require_absent_artifact_output(root, args.output)
    private = output
    if args.retained_artifacts_root is not None:
        private = require_absent_artifact_output(root, args.retained_artifacts_root)
        if private.is_relative_to(output) or output.is_relative_to(private):
            raise ValueError(
                "Native witness output must be separate from public output"
            )
    report, records = build(root)
    output.mkdir(parents=True)
    if private != output:
        private.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    (private / "claim-annotation-witness.json").write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
