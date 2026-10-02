"""Run the retained LegacyAge chronology join with qualified external inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output as _absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.configured_owner import _safe_file
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    validated_external_report_sources,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/legacyage.json")
REPLAY = "docs/report/source-relations/neotoma/legacyage-chronology/replay.py"
REPLAY_SHA256 = "05c9993b32f6ac944a75de905e59a0d5ca63f8a099fdda27792b40cf0847d4ac"
SURFACE = "data/neotoma/relational/surfaces"


def main(argv: list[str] | None = None) -> int:
    """Bind the existing replay's read set and run it into a new artifact path."""
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
    output = _absent_artifact_output(repository, args.output)
    descriptor = json.loads(
        (repository / args.source_descriptor).read_text(encoding="utf-8")
    )
    expected_external = {row["path"]: row["sha256"] for row in descriptor["files"]}
    replay_path = _safe_file(repository, REPLAY, "LegacyAge replay")
    if hashlib.sha256(replay_path.read_bytes()).hexdigest() != REPLAY_SHA256:
        raise ReportRebuildError("LegacyAge replay read set changed")
    replay = runpy.run_path(
        str(replay_path),
        run_name="bijux_legacyage_chronology_replay",
    )
    if replay.get("SOURCES") != expected_external or set(expected_external) != {
        "table-s5-legacyage-chronology.csv",
        "table-s6-chronology-comparison.csv",
    }:
        raise ReportRebuildError("LegacyAge replay source read set differs")
    expected_neotoma = {
        name: hashlib.sha256(
            _safe_file(
                repository,
                f"{SURFACE}/{name}/part-00001.json",
                "Neotoma surface",
            ).read_bytes()
        ).hexdigest()
        for name in ("age_claims", "samples")
    }
    if replay.get("NEOTOMA") != expected_neotoma:
        raise ReportRebuildError("LegacyAge replay repository read set differs")
    expected_inputs = {
        f"external/legacyage/pangaea-933132/{name}" for name in expected_external
    }
    if not expected_inputs <= set(qualified.inputs):
        raise ReportRebuildError("LegacyAge qualified source coverage differs")
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
    validated_external_report_sources(
        repository, args.source_root, args.source_descriptor
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
