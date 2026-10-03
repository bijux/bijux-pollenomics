"""Route Swedish 31-target source inputs to an isolated artifact directory."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import runpy
import sys

CORE = "bijux_pollenomics_dev.source_completion.swedish_author_target_pollen"
CORE_PATH = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    "source_completion/swedish_author_target_pollen.py"
)


def run(repository: Path, output: Path) -> None:
    """Invoke only the existing prepare stage, with an absent output directory."""
    repository = repository.resolve(strict=True)
    if output.is_symlink():
        raise ValueError("Swedish author input output may not be a symlink")
    destination = output.resolve()
    artifacts = repository / "artifacts"
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("Absent repository artifact destination required")
    expected = repository / CORE_PATH
    spec = importlib.util.find_spec(CORE)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != expected:
        raise ValueError("Swedish author input writer origin differs from repository")
    original = sys.argv
    try:
        sys.argv = [
            CORE,
            "prepare",
            "--repository",
            str(repository),
            "--output",
            str(destination),
        ]
        runpy.run_module(CORE, run_name="__main__")
    finally:
        sys.argv = original


def main(argv: list[str] | None = None) -> int:
    """Route Swedish 31-target source inputs to an isolated artifact directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
