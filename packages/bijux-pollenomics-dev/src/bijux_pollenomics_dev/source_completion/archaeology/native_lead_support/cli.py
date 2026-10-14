"""Write a finite public aggregate and separately retained private native witnesses."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

from .independent import verify
from .producer import build_private
from .report import aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--retained-artifacts-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.repository
    output = require_absent_artifact_output(root, args.output)
    private = require_absent_artifact_output(root, args.retained_artifacts_root)
    if private.is_relative_to(output) or output.is_relative_to(private):
        raise ValueError("public aggregate and private native witness must be separate")
    qualified = validated_external_report_sources(
        root, args.source_root, args.source_descriptor
    )
    build_private(root, qualified.directory, private)
    verify(private, private / "independent-audit.json")
    report = aggregate(private)
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    custody = json.loads(
        (
            root / "reports/science/archaeology-native-lead-support/source-custody.json"
        ).read_bytes()
    )
    custody["public_report_sha256"] = hashlib.sha256(
        (output / "report.json").read_bytes()
    ).hexdigest()
    (output / "source-account.json").write_text(
        json.dumps(custody, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
