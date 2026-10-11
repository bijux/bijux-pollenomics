"""Run DALMUT's retained depth-summary allocation with qualified S4/S5."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import (
    safe_source_file as _safe_file,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/legacyage-depth-allocation.json")
REPLAY = "docs/report/source-relations/neotoma/legacyage-chronology/depth-allocation/replay.py"
REPLAY_SHA256 = "c4ca3ea949fb5a5da7c00581d799f93d34e77809c7d2a36d3835bf89a6ee03bf"
SAMPLES = "data/neotoma/relational/surfaces/samples/part-00001.json"


def main(argv: list[str] | None = None) -> int:
    """Bind the reviewed replay to its exact packet and repository read set."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-descriptor", type=Path, default=DESCRIPTOR)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    repository = args.repository.resolve(strict=True)
    qualified = validated_external_report_sources(
        repository, args.source_root, args.source_descriptor
    )
    output = require_absent_artifact_output(repository, args.output)
    descriptor_file = qualified.inputs[args.source_descriptor.as_posix()]
    descriptor = json.loads(descriptor_file.read_text(encoding="utf-8"))
    expected_external = {row["path"]: row["sha256"] for row in descriptor["files"]}
    replay_path = _safe_file(repository, REPLAY, "DALMUT depth allocation replay")
    if hashlib.sha256(replay_path.read_bytes()).hexdigest() != REPLAY_SHA256:
        raise ReportRebuildError("DALMUT depth allocation replay read set changed")
    replay = runpy.run_path(str(replay_path), run_name="bijux_dalmut_depth_allocation")
    if replay.get("SOURCE_SHA256") != expected_external or set(expected_external) != {
        "table-s4-original-chronology.csv",
        "table-s5-legacyage-chronology.csv",
    }:
        raise ReportRebuildError("DALMUT S4/S5 read set differs")
    sample_sha256 = hashlib.sha256(
        _safe_file(repository, SAMPLES, "Neotoma samples").read_bytes()
    ).hexdigest()
    if replay.get("SAMPLES_SHA256") != sample_sha256:
        raise ReportRebuildError("DALMUT Neotoma sample read set differs")
    source_id = descriptor["source_id"]
    expected_inputs = {f"external/{source_id}/{name}" for name in expected_external}
    if not expected_inputs <= set(qualified.inputs):
        raise ReportRebuildError("DALMUT qualified source coverage differs")
    old_argv = sys.argv
    try:
        sys.argv = [
            REPLAY,
            "--repository",
            str(repository),
            "--source-dir",
            str(qualified.directory),
            "--output",
            str(output),
        ]
        replay["main"]()
    finally:
        sys.argv = old_argv
    after = validated_external_report_sources(
        repository, args.source_root, args.source_descriptor
    )
    if (
        after.inputs != qualified.inputs
        or after.descriptor_sha256 != qualified.descriptor_sha256
    ):
        raise ReportRebuildError("DALMUT qualified source declaration changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
