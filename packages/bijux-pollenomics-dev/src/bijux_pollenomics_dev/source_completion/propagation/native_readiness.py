"""Reproduce native first-observed readiness without promoting refused events."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import runpy
import stat
import sys

SOURCE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/neotoma_first_observed.py"
)
MODULE = "bijux_pollenomics_dev.lra_validation.neotoma_first_observed"


def _regular(path: Path, repository: Path) -> None:
    if not path.is_relative_to(repository):
        raise ValueError("native readiness source is outside repository")
    if (
        any(
            p.is_symlink()
            for p in (path, *path.parents)
            if p.is_relative_to(repository)
        )
        or path.resolve() != path
        or not stat.S_ISREG(path.lstat().st_mode)
    ):
        raise ValueError("native readiness source must be a real regular file")


def run(repository: Path, output: Path) -> None:
    """Invoke only the original two-site readiness CLI at an absent artifact file."""
    if (
        not repository.is_absolute()
        or repository.is_symlink()
        or repository.resolve(strict=True) != repository
    ):
        raise ValueError("repository must be a real absolute path")
    artifacts = repository / "artifacts"
    if (
        artifacts.is_symlink()
        or not artifacts.is_dir()
        or artifacts.resolve() != artifacts
    ):
        raise ValueError("repository artifacts must be a real directory")
    if (
        not output.is_absolute()
        or output.exists()
        or output.is_symlink()
        or output.resolve() == artifacts
        or not output.resolve().is_relative_to(artifacts)
        or any(p.is_symlink() for p in output.parents if p.is_relative_to(repository))
    ):
        raise ValueError("absent real repository artifact file required")
    source = repository / SOURCE
    _regular(source, repository)
    spec = importlib.util.find_spec(MODULE)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != source:
        raise ValueError("native readiness source module origin differs")
    original = sys.argv
    try:
        sys.argv = [
            str(source),
            "--repository",
            str(repository),
            "--output",
            str(output),
        ]
        try:
            runpy.run_module(MODULE, run_name="__main__")
        except SystemExit as error:
            if error.code not in (None, 0):
                raise
    finally:
        sys.argv = original
    _regular(output, repository)
    report = json.loads(output.read_bytes())
    if (
        report.get("schema_version") != "neotoma-source-first-observed-readiness.v1"
        or any(
            report.get("denominators", {}).get(k) != v
            for k, v in {
                "sites": 2,
                "attempts": 256,
                "refused": 256,
                "events": 0,
                "estimator_invocations": 0,
            }.items()
        )
        or report.get("claims", {}).get("first_observed_events_admitted") is not False
        or report.get("claims", {}).get("scientific_accuracy_or_route_claim")
        is not False
    ):
        raise ValueError("native readiness refusal or nonpromotion contract differs")


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and reproduce native first-observed readiness without promoting refused events."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
