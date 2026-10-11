"""Run the retained Namibian publisher-row join from qualified TSV inputs."""

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
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import (
    safe_source_file as _safe_file,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

DESCRIPTOR = Path(
    "configs/ci/qualified-report-sources/namibia-modern-pollen-vegetation.json"
)
REPLAY = "docs/report/vegetation-reference/namibia-pollen-vegetation/replay.py"
REPLAY_SHA256 = "43750c78ca1aafc5426f784c664a5e1163150d7392f56257bf06421ece96e71c"
SOURCE_ID = "vegetation/namibia-modern-pollen-vegetation"
FILES = frozenset({"PANGAEA.931033.tab", "PANGAEA.931035.tab"})


def main(argv: list[str] | None = None) -> int:
    """Bind the exact publisher packet, retained producer, and two owned files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", type=Path, default=DESCRIPTOR)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    repository = args.repository.resolve(strict=True)
    qualified = validated_external_report_sources(
        repository, args.source_root, args.source_descriptor
    )
    output = require_absent_artifact_output(repository, args.output)
    descriptor_file = qualified.inputs[args.source_descriptor.as_posix()]
    descriptor = json.loads(descriptor_file.read_text(encoding="utf-8"))
    expected = {row["path"]: row["sha256"] for row in descriptor["files"]}
    if descriptor["source_id"] != SOURCE_ID or frozenset(expected) != FILES:
        raise ReportRebuildError("Namibia publisher source declaration differs")
    if set(qualified.inputs) != {
        args.source_descriptor.as_posix(),
        f"external/{SOURCE_ID}/source_manifest.json",
        *(f"external/{SOURCE_ID}/{name}" for name in FILES),
    }:
        raise ReportRebuildError("Namibia qualified input coverage differs")
    replay_path = _safe_file(repository, REPLAY, "Namibia source join replay")
    if hashlib.sha256(replay_path.read_bytes()).hexdigest() != REPLAY_SHA256:
        raise ReportRebuildError("Namibia source join replay read set changed")
    replay = runpy.run_path(str(replay_path), run_name="bijux_namibia_source_join")
    if replay.get("SOURCES") != expected:
        raise ReportRebuildError("Namibia replay source read set differs")
    columns = {row["path"]: tuple(row["columns"]) for row in descriptor["files"]}
    if (
        replay.get("POLLEN_COLUMNS") != columns["PANGAEA.931033.tab"]
        or replay.get("VEGETATION_COLUMNS") != columns["PANGAEA.931035.tab"]
    ):
        raise ReportRebuildError("Namibia replay publisher columns differ")
    old_argv = sys.argv
    try:
        sys.argv = [
            REPLAY,
            "--source-dir",
            str(qualified.directory),
            "--output-dir",
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
        raise ReportRebuildError("Namibia publisher source identity changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
