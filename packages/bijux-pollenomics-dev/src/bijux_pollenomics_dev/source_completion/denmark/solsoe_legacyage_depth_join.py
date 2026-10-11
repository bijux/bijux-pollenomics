"""Run the retained Solsø depth join against qualified LegacyAge inputs."""

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

DESCRIPTOR = Path("configs/ci/qualified-report-sources/legacyage.json")
REPLAY = (
    "docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology/replay.py"
)
REPLAY_SHA256 = "3476ea97c084096d92eea4eda3127ff5c2c10f8dc2eec7951788fe0cf1349820"
SURFACE = "data/neotoma/relational/surfaces"


def main(argv: list[str] | None = None) -> int:
    """Run the reviewed replay and preserve its exact source read set."""
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
    replay_path = _safe_file(repository, REPLAY, "Solsø LegacyAge replay")
    if hashlib.sha256(replay_path.read_bytes()).hexdigest() != REPLAY_SHA256:
        raise ReportRebuildError("Solsø LegacyAge replay read set changed")
    replay = runpy.run_path(str(replay_path), run_name="bijux_solsoe_legacyage_replay")
    if replay.get("SOURCE_SHA") != expected_external or set(expected_external) != {
        "table-s5-legacyage-chronology.csv",
        "table-s6-chronology-comparison.csv",
    }:
        raise ReportRebuildError("Solsø LegacyAge source read set differs")
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
    if replay.get("NEOTOMA_SHA") != expected_neotoma:
        raise ReportRebuildError("Solsø Neotoma read set differs")
    source_id = descriptor["source_id"]
    expected_inputs = {f"external/{source_id}/{name}" for name in expected_external}
    if not expected_inputs <= set(qualified.inputs):
        raise ReportRebuildError("Solsø qualified source coverage differs")
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
        raise ReportRebuildError("Solsø qualified source declaration changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
