"""Publish a compact retained Norwegian forward account through an atomic directory."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .account import products
from .authority import DESCRIPTOR
from .sources import load_inputs


def publish(
    repository: Path, source_root: Path, output: Path
) -> dict[str, dict[str, Any]]:
    """Publish authenticated source products atomically into an absent output directory."""
    repository = repository.absolute()
    source_root = source_root.absolute()
    output = require_absent_artifact_output(repository, output)
    if output.is_relative_to(source_root) or source_root.is_relative_to(output):
        raise ValueError("Norwegian forward output and private source overlap")
    values = load_inputs(repository, source_root)
    rendered = products(values)
    stage = Path(tempfile.mkdtemp(prefix="norwegian-forward-", dir=output.parent))
    promoted = False
    try:
        for name, value in rendered.items():
            (stage / name).write_text(
                json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
            )
        load_inputs(repository, source_root)
        require_absent_artifact_output(repository, output)
        os.rename(stage, output)
        promoted = True
        load_inputs(repository, source_root)
    except BaseException:
        if promoted:
            shutil.rmtree(output)
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return rendered


def main(argv: list[str] | None = None) -> int:
    """Parse the source-bound publication command and its output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-descriptor", type=Path, default=DESCRIPTOR)
    args = parser.parse_args(argv)
    if (
        args.source_descriptor.is_absolute()
        or ".." in args.source_descriptor.parts
        or args.source_descriptor != DESCRIPTOR
    ):
        parser.error(
            "Norwegian forward source descriptor must equal the pinned repository path"
        )
    publish(args.repository, args.source_root, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
