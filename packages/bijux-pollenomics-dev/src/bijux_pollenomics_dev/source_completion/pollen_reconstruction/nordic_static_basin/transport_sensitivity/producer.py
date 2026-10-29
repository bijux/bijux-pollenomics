"""Publish one separately named Nordic conditional wind-sensitivity result."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, cast

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file

from ..sources import load_inputs
from .calculation import calculate
from .inputs import REPORT, REPORT_SHA256, prepare

PROTOCOL = "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/assumptions/transport-sensitivity.json"
PROTOCOL_SHA256 = "e83196a9af9953a2580fc956c1b79dc63760f0f27b6bc7c6a856a4ef0b8b78cc"


def load(repository: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reuse the maintained complete retained Nordic authority, without a kernel call."""
    inputs = load_inputs(repository)
    path = safe_source_file(
        repository, PROTOCOL, "Nordic conditional transport protocol"
    )
    if path.stat().st_size > 16384:
        raise ValueError("Bounded transport protocol required")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROTOCOL_SHA256:
        raise ValueError("Frozen transport protocol changed")
    report = cast(dict[str, Any], inputs["report.json"])
    protocol = cast(dict[str, Any], json.loads(raw))
    if hashlib.sha256((repository / REPORT).read_bytes()).hexdigest() != REPORT_SHA256:
        raise ValueError("Original baseline changed")
    prepare(report, protocol)
    return report, protocol


def publish(repository: Path, output: Path, *, execution_epoch: str) -> dict[str, Any]:
    """Run only the frozen alternative profiles; retain original products literally."""
    if re.fullmatch(r"[0-9a-f]{40}", execution_epoch) is None:
        raise ValueError("Actual execution epoch must be an exact Git SHA")
    repository = repository.absolute()
    destination = require_absent_artifact_output(repository, output)
    before = load(repository)
    result = calculate(*before)
    result["baseline_report"] = {"path": REPORT, "sha256": REPORT_SHA256}
    result["protocol_sha256"] = PROTOCOL_SHA256
    result["execution_epoch"] = execution_epoch
    raw = (
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    if len(raw) > 8 * 1024**2:
        raise ValueError("Conditional sensitivity result exceeds8MiB")
    if load(repository) != before:
        raise ValueError("Original retained input or protocol changed")
    stage = Path(tempfile.mkdtemp(prefix="nordic-wind-", dir=destination.parent))
    try:
        (stage / "report.json").write_bytes(raw)
        require_absent_artifact_output(repository, destination)
        os.rename(stage, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return result


def main(argv: list[str] | None = None) -> int:
    """Publish declared wind sensitivity and report refused windows."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execution-epoch", required=True)
    args = parser.parse_args(argv)
    result = publish(args.repository, args.output, execution_epoch=args.execution_epoch)
    return 1 if result["refused_windows"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
