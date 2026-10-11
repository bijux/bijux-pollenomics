"""Publish a sole source-bound chronology summary through an atomic directory."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile

from .authority import CAPTURE_PINS
from .sources import load_inputs
from .summary import summarize


def _output_path(repository: Path, output: Path) -> Path:
    if ".." in output.parts:
        raise ValueError("summary output path must be canonical")
    output = output.absolute()
    for parent in output.parents:
        if (parent.exists() or parent.is_symlink()) and not stat.S_ISDIR(
            parent.lstat().st_mode
        ):
            raise ValueError("summary output ancestor is not a real directory")
    artifact_root = repository / "artifacts"
    if (
        output == artifact_root
        or not output.is_relative_to(artifact_root)
        or not output.resolve().is_relative_to(artifact_root)
    ):
        raise ValueError("summary output must be below repository artifacts")
    if output.exists() or output.is_symlink():
        raise ValueError("existing summary output refused")
    for relative in CAPTURE_PINS:
        source = repository / relative
        if output.is_relative_to(source) or source.is_relative_to(output):
            raise ValueError("summary output and source overlap")
    return output


def publish(repository: Path, output: Path) -> dict[str, object]:
    """Publish retained chronology summaries without rerunning their numerical producer."""
    repository = repository.resolve(strict=True)
    output = _output_path(repository, output)
    inputs = load_inputs(repository)
    summary = summarize(
        inputs["report.json"], inputs["execution/read-only-diagnostic.json"]
    )
    summary["retained_source_sha256"] = dict(CAPTURE_PINS)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="chronology-summary-", dir=output.parent))
    promoted = False
    try:
        body = json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
        (staging / "summary.json").write_text(body)
        load_inputs(repository)
        _output_path(repository, output)
        os.rename(staging, output)
        promoted = True
        load_inputs(repository)
    except BaseException:
        if promoted:
            shutil.rmtree(output)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return summary


def main(argv: list[str] | None = None) -> int:
    """Parse the retained chronology publication command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    publish(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
