"""Publish a source-bound conditional account to an absent artifact directory."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .reconstruction import reconstruct
from .sources import FAMILY, read_bound, sha256


def publish(repository: Path, source_root: Path, output: Path, candidate: str) -> None:
    """Publish authenticated source products atomically into an absent output directory."""
    repository = repository.absolute()
    source_root = source_root.absolute()
    for root in (repository, source_root):
        if root.resolve() != root or not (root / "pyproject.toml").is_file():
            raise ValueError("repository/source root must be a real product checkout")
    output = require_absent_artifact_output(repository, output)
    stage = Path(tempfile.mkdtemp(prefix=".swedish-static-basin-", dir=output.parent))
    published = False
    try:
        report = reconstruct(source_root, candidate)
        products = stage / "source-products"
        products.mkdir()
        (products / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        for name, identity in report["source_files"].items():
            read_bound(source_root, name, identity)
        if (
            sha256(source_root / FAMILY / "assumptions/protocol.json")
            != report["protocol_sha256"]
            or sha256(source_root / FAMILY / "inputs/source-identities.json")
            != report["source_identity_declaration_sha256"]
            or {path.name: sha256(path) for path in Path(__file__).parent.glob("*.py")}
            != report["producer_source_sha256"]
        ):
            raise ValueError(
                "producer input or source declaration changed before publication"
            )
        require_absent_artifact_output(repository, output)
        os.replace(products, output)
        published = True
        print(
            json.dumps(
                {
                    "cores": len(report["cores"]),
                    "samples": sum(
                        core["included_sample_count"] for core in report["cores"]
                    ),
                    "windows": sum(
                        core["occupied_window_count"] for core in report["cores"]
                    ),
                }
            ),
            flush=True,
        )
    finally:
        if published:
            shutil.rmtree(stage)


def main(argv: list[str] | None = None) -> int:
    """Parse the source-bound publication command and its output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", "--repository-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output", "--output-root", type=Path, required=True)
    parser.add_argument("--candidate")
    args = parser.parse_args(argv)
    source_root = (args.source_root or args.repository).absolute()
    descriptor = source_root / FAMILY / "inputs/source-identities.json"
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
