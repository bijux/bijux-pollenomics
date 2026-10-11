"""Publish a source-bound conditional account to an absent artifact directory."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..swedish_static_basin.sources import NativeSourceRecord, read_bound, sha256
from .reconstruction import reconstruct
from .sources import DECLARATION, PROTOCOL


def serialize_report(report: NativeSourceRecord) -> str:
    """Encode the complete account independently of unordered mapping insertion."""
    return (
        json.dumps(
            report, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False
        )
        + "\n"
    )


def publish(repository: Path, source_root: Path, output: Path, candidate: str) -> None:
    """Publish the source-bound account and retain its private support evidence."""
    repository = repository.absolute()
    source_root = source_root.absolute()
    for root in (repository, source_root):
        if root.resolve() != root or not (root / "pyproject.toml").is_file():
            raise ValueError("repository/source root must be a real product checkout")
    output = require_absent_artifact_output(repository, output)
    stage = Path(
        tempfile.mkdtemp(
            prefix=".swedish-parameter-transfer-evidence-", dir=output.parent
        )
    )
    report, actual_support = reconstruct(source_root, candidate)
    audit = stage / "local-source-support.json"
    audit.write_text(
        json.dumps(
            actual_support,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    report["local_actual_source_support_file_sha256"] = sha256(audit)
    report["local_actual_source_support_role"] = (
        "Actual per-sample masks retained in the private local artifact evidence capsule; no raw rows promoted into the portable product account."
    )
    products = stage / "source-products"
    products.mkdir()
    (products / "report.json").write_text(
        serialize_report(report),
        encoding="utf-8",
    )
    for name, identity in report["source_files"].items():
        read_bound(source_root, name, identity)
    if (
        sha256(source_root / PROTOCOL) != report["scenario_protocol_sha256"]
        or sha256(source_root / DECLARATION) != report["source_declaration_sha256"]
        or {path.name: sha256(path) for path in Path(__file__).parent.glob("*.py")}
        != report["producer_source_sha256"]
    ):
        raise ValueError(
            "producer input or source declaration changed before publication"
        )
    if sha256(audit) != report["local_actual_source_support_file_sha256"]:
        raise ValueError("actual source-support capsule changed before publication")
    require_absent_artifact_output(repository, output)
    os.replace(products, output)
    print(
        json.dumps(
            {
                "cores": len({case["core"] for case in report["cases"]}),
                "samples": sum(
                    core["included_native_samples"]
                    for core in report["cases"]
                    if core["scenario"]
                    == report["scenario_protocol"]["profiles"][0]["id"]
                ),
                "windows": sum(
                    core["occupied_windows"]
                    for core in report["cases"]
                    if core["scenario"]
                    == report["scenario_protocol"]["profiles"][0]["id"]
                ),
            }
        ),
        flush=True,
    )


def main(argv: list[str] | None = None) -> int:
    """Parse the conditional parameter-transfer publication command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", "--repository-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output", "--output-root", type=Path, required=True)
    parser.add_argument("--candidate")
    args = parser.parse_args(argv)
    source_root = (args.source_root or args.repository).absolute()
    descriptor = source_root / DECLARATION
    if descriptor.resolve() != descriptor or not descriptor.is_file():
        raise ValueError("source descriptor must be a contained regular file")
    declared_candidate = json.loads(descriptor.read_bytes())[
        "producer_source_candidate"
    ]
    if args.candidate is not None and args.candidate != declared_candidate:
        raise ValueError("candidate differs from the source declaration")
    publish(args.repository, source_root, args.output, declared_candidate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
