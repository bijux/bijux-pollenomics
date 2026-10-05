"""Publish compact saved development losses through an atomic directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any
import shutil
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .authority import CAPTURE_PINS, DESCRIPTOR, SOURCE_ID, WRITER_SOURCE_BASE
from .sources import load_inputs
from .summary import summarize


def publish(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> dict[str, Any]:
    repository = repository.resolve(strict=True)
    destination = require_absent_artifact_output(repository, output)
    values, before = load_inputs(repository, source_root, source_descriptor)
    report = summarize(values)
    modules = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(Path(__file__).parent.glob("*.py"))
    }
    proof = {
        "schema_version": "swedish-grouped-forward-source-proof.v1",
        "source_id": SOURCE_ID,
        "qualified_snapshot_schema": "qualified-author-snapshot.v1",
        "snapshot_manifest_files_contract": "dict of sorted relative filename to SHA256; descriptor.files sorted distinct complete specs",
        "original_capture_sha256": dict(CAPTURE_PINS),
        "qualified_descriptor_sha256": hashlib.sha256(
            (repository / source_descriptor).read_bytes()
        ).hexdigest(),
        "actual_scientific_plan_sha256": report["actual_scientific_plan_sha256"],
        "actual_scientific_candidate": report["actual_scientific_candidate"],
        "writer_source_base": WRITER_SOURCE_BASE,
        "actual_writer_module_sha256": modules,
        "operation": "New saved-loss projection, not transport attributed to the original model run",
        "original_complete_ledgers_remain_external": True,
        "raw_count_or_native_sample_redistribution": False,
        "qualified_source_identity_is_not_rights_admission": True,
    }
    stage = Path(tempfile.mkdtemp(prefix="grouped-forward-", dir=destination.parent))
    promoted = False
    try:
        for name, value in [("report.json", report), ("source-proof.json", proof)]:
            (stage / name).write_text(
                json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
            )
        _, after = load_inputs(repository, source_root, source_descriptor)
        if after != before:
            raise ValueError("Grouped-forward source changed before publication")
        require_absent_artifact_output(repository, destination)
        os.rename(stage, destination)
        promoted = True
        _, after = load_inputs(repository, source_root, source_descriptor)
        if after != before:
            raise ValueError("Grouped-forward source changed during publication")
    except BaseException:
        if promoted:
            shutil.rmtree(destination)
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", type=Path, default=Path(DESCRIPTOR))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    publish(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
