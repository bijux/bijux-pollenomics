"""Confine private source evidence separately from the generated report tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from .. import producer as scientific_producer


def _regular_file(path: Path) -> bytes:
    if path.resolve() != path or not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("publication evidence must be a contained regular file")
    return path.read_bytes()


def _digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _source_controls(source_root: Path) -> dict[str, str]:
    directory = Path(__file__).absolute().parent
    if not directory.is_relative_to(source_root):
        raise ValueError("publication adapter source is outside the declared checkout")
    return {
        str(path.relative_to(source_root)): _digest(_regular_file(path))
        for path in sorted(directory.glob("*.py"))
    }


def publish(
    repository: Path,
    source_root: Path,
    output: Path,
    retained_artifacts_root: Path,
) -> None:
    """Run the qualified science into retained evidence and publish only report.json."""
    repository, source_root = repository.absolute(), source_root.absolute()
    for root in (repository, source_root):
        if root.resolve() != root or not (root / "pyproject.toml").is_file():
            raise ValueError("repository/source root must be a real product checkout")
    output, retained = output.absolute(), retained_artifacts_root.absolute()
    if retained.is_relative_to(output) or output.is_relative_to(retained):
        raise ValueError("report and retained evidence roots must not overlap")
    output = require_absent_artifact_output(repository, output)
    retained = require_absent_artifact_output(repository, retained)
    controls_before = _source_controls(source_root)
    retained.mkdir()
    science_output = retained / "scientific-account"
    code = scientific_producer.main(
        [
            "--repository", str(repository),
            "--source-root", str(source_root),
            "--output", str(science_output),
        ]
    )
    if type(code) is not int or code != 0:
        raise ValueError("scientific producer did not return native success")
    if sorted(path.name for path in science_output.iterdir()) != ["report.json"]:
        raise ValueError("scientific aggregate output coverage is not exact")
    report_path = science_output / "report.json"
    report_bytes = _regular_file(report_path)
    report = json.loads(report_bytes)
    support_hash = report["local_actual_source_support_file_sha256"]
    if not isinstance(support_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", support_hash):
        raise ValueError("scientific source-support digest is not valid")
    capsules = list(retained.glob(".swedish-parameter-transfer-evidence-*/local-source-support.json"))
    if len(capsules) != 1 or _digest(_regular_file(capsules[0])) != support_hash:
        raise ValueError("actual retained source-support capsule does not match report")
    aggregate = Path(tempfile.mkdtemp(prefix=".swedish-aggregate-products-", dir=retained))
    shutil.copy2(report_path, aggregate / "report.json")
    if _regular_file(aggregate / "report.json") != report_bytes or _regular_file(report_path) != report_bytes:
        raise ValueError("scientific aggregate bytes changed before publication")
    if _source_controls(source_root) != controls_before:
        raise ValueError("publication adapter source changed during execution")
    if _digest(_regular_file(capsules[0])) != support_hash:
        raise ValueError("actual retained source-support capsule changed before publication")
    capture = {
        "scope": "Qualified unchanged scientific producer runs under a separately retained artifact root. Sole aggregate report bytes are prepared for atomic publication; source masks remain outside the report inventory.",
        "scientific_producer_module": scientific_producer.__name__,
        "scientific_producer_main_return": code,
        "scientific_source_candidate": report["producer_source_candidate"],
        "publication_adapter_source_sha256": controls_before,
        "aggregate_report_sha256": _digest(report_bytes),
        "retained_source_support_sha256": support_hash,
        "retained_source_support_relative_path": str(capsules[0].relative_to(retained)),
        "raw_source_redistribution_authorized": False,
    }
    (retained / "publication-capture.json").write_text(
        json.dumps(capture, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    require_absent_artifact_output(repository, output)
    os.replace(aggregate, output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", "--repository-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output", "--output-root", type=Path, required=True)
    parser.add_argument("--retained-artifacts-root", type=Path, required=True)
    args = parser.parse_args(argv)
    publish(args.repository, args.source_root or args.repository, args.output, args.retained_artifacts_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
