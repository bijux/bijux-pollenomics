"""Publish a qualified retained native account under an absent artifact output."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

from .account import products

SOURCE_IDS = {
    "common-panel": "neotoma/swedish-observed-common-panel-results",
    "lake-panels": "neotoma/swedish-observed-lake-panel-results",
}


def run(
    repository: Path,
    source_root: Path,
    descriptor: Path,
    output: Path,
    scope: str,
    capture_output: Path,
) -> None:
    """Regenerate summaries and verify retained cells; do not rerun native transport."""
    repository = repository.resolve(strict=True)
    if scope not in SOURCE_IDS:
        raise ValueError("unknown scientific retained-account scope")
    output = require_absent_artifact_output(repository, output)
    capture_output = require_absent_artifact_output(repository, capture_output)
    if output.is_relative_to(capture_output) or capture_output.is_relative_to(output):
        raise ValueError("report and current-writer capture outputs overlap")
    descriptor_file = safe_source_file(
        repository, descriptor.as_posix(), "scientific source descriptor"
    )
    if json.loads(descriptor_file.read_bytes())["source_id"] != SOURCE_IDS[scope]:
        raise ValueError("scientific source descriptor belongs to another report scope")
    qualified = validated_external_report_sources(repository, source_root, descriptor)
    before = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in qualified.inputs.items()
    }
    generated = products(qualified.directory, scope)
    after = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in qualified.inputs.items()
    }
    if before != after:
        raise ValueError(
            "scientific source capture changed during account verification"
        )
    stage = Path(tempfile.mkdtemp(prefix=".source-observed-panel-", dir=output.parent))
    try:
        for name, value in generated.items():
            (stage / name).write_text(
                json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                encoding="utf-8",
            )
        capture_output.mkdir()
        controls = {
            str(p.relative_to(repository)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).absolute().parent.glob("*.py"))
            if p.is_relative_to(repository)
        }
        if not controls:
            raise ValueError(
                "maintained publisher must execute inside declared checkout"
            )
        origins = {
            name: str(module.__file__)
            for name, module in sorted(sys.modules.items())
            if name.startswith("bijux_pollenomics_dev")
            and getattr(module, "__file__", None)
        }
        capture = {
            "schema_version": "source-observed-panel-current-writer-capture.v1",
            "scientific_scope": scope,
            "current_writer_scope": "Actual source/result account replay and scalar covariance verification; no physical transport or independent integration rerun, configured route authority or native R claim",
            "source_descriptor_sha256": qualified.descriptor_sha256,
            "qualified_input_sha256": before,
            "actual_publisher_source_controls": controls,
            "current_products": {
                n: hashlib.sha256((stage / n).read_bytes()).hexdigest()
                for n in sorted(generated)
            },
            "actual_loaded_first_party_module_origins": origins,
            "sys_executable": sys.executable,
            "sys_base_prefix": sys.base_prefix,
        }
        (capture_output / "writer-capture.json").write_text(
            json.dumps(capture, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        require_absent_artifact_output(repository, output)
        os.replace(stage, output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main(scope: str, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", "--repository-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-descriptor", type=Path, required=True)
    parser.add_argument("--output", "--output-root", type=Path, required=True)
    parser.add_argument(
        "--capture-output", "--retained-artifacts-root", type=Path, required=True
    )
    args = parser.parse_args(argv)
    run(
        args.repository,
        args.source_root,
        args.source_descriptor,
        args.output,
        scope,
        args.capture_output,
    )
    return 0
