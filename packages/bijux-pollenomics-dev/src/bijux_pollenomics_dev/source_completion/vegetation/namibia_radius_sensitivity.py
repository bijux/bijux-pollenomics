"""Run the retained Namibian radius description from qualified publisher rows."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.configured_owner import _safe_file
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

DESCRIPTOR = Path(
    "configs/ci/qualified-report-sources/namibia-modern-pollen-vegetation.json"
)
RADIUS_REPLAY = (
    "docs/report/vegetation-reference/namibia-pollen-vegetation/radius_sensitivity.py"
)
RADIUS_REPLAY_SHA256 = (
    "b93ba1f47a06fb607fa17f3700bbd60179765e4409e73c7c036811f5a5cf32ea"
)
SOURCE_REPLAY = "docs/report/vegetation-reference/namibia-pollen-vegetation/replay.py"
SOURCE_REPLAY_SHA256 = (
    "43750c78ca1aafc5426f784c664a5e1163150d7392f56257bf06421ece96e71c"
)
SOURCE_ID = "vegetation/namibia-modern-pollen-vegetation"
FILES = frozenset({"PANGAEA.931033.tab", "PANGAEA.931035.tab"})


def main(argv: list[str] | None = None) -> int:
    """Bind both reviewed scripts and the original TSV pair before reproduction."""
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
        raise ReportRebuildError("Namibia radius publisher source declaration differs")
    if set(qualified.inputs) != {
        args.source_descriptor.as_posix(),
        f"external/{SOURCE_ID}/source_manifest.json",
        *(f"external/{SOURCE_ID}/{name}" for name in FILES),
    }:
        raise ReportRebuildError("Namibia radius qualified input coverage differs")
    source_path = _safe_file(repository, SOURCE_REPLAY, "Namibia source replay")
    radius_path = _safe_file(repository, RADIUS_REPLAY, "Namibia radius replay")
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != SOURCE_REPLAY_SHA256:
        raise ReportRebuildError("Namibia source replay read set changed")
    if hashlib.sha256(radius_path.read_bytes()).hexdigest() != RADIUS_REPLAY_SHA256:
        raise ReportRebuildError("Namibia radius replay read set changed")

    # The retained radius script imports `replay` by its local script name.
    # Supply only the pinned repository module during this invocation.
    spec = importlib.util.spec_from_file_location("replay", source_path)
    if spec is None or spec.loader is None:
        raise ReportRebuildError("Namibia source replay cannot be loaded")
    source_replay = importlib.util.module_from_spec(spec)
    previous = sys.modules.get("replay")
    old_argv = sys.argv
    sys.modules["replay"] = source_replay
    try:
        spec.loader.exec_module(source_replay)
        if expected != source_replay.SOURCES:
            raise ReportRebuildError("Namibia radius source read set differs")
        columns = {row["path"]: tuple(row["columns"]) for row in descriptor["files"]}
        if (
            columns["PANGAEA.931033.tab"] != source_replay.POLLEN_COLUMNS
            or columns["PANGAEA.931035.tab"] != source_replay.VEGETATION_COLUMNS
        ):
            raise ReportRebuildError("Namibia radius publisher columns differ")
        radius_replay = runpy.run_path(
            str(radius_path), run_name="bijux_namibia_radius_sensitivity"
        )
        if radius_replay.get("replay") is not source_replay:
            raise ReportRebuildError("Namibia radius local replay origin differs")
        sys.argv = [
            RADIUS_REPLAY,
            "--source-dir",
            str(qualified.directory),
            "--output-dir",
            str(output),
        ]
        radius_replay["main"]()
    finally:
        sys.argv = old_argv
        if previous is None:
            sys.modules.pop("replay", None)
        else:
            sys.modules["replay"] = previous
    after = validated_external_report_sources(
        repository, args.source_root, args.source_descriptor
    )
    if (
        after.inputs != qualified.inputs
        or after.descriptor_sha256 != qualified.descriptor_sha256
    ):
        raise ReportRebuildError("Namibia radius publisher source identity changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
