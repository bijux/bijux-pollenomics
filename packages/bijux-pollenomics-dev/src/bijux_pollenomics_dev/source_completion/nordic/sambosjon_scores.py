"""Reproduce Sämbosjön scores using the retained independent prediction freeze."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import sambosjon_execution

FROZEN = Path("docs/report/regions/nordic/sambosjon-direct-pollen/frozen")


def run(repository: Path, output: Path) -> None:
    """Validate retained inputs before the original scorer reads target counts."""
    sambosjon_execution._destination(repository, output)
    prepared, manifest, protocol = sambosjon_execution._prepared(repository)
    frozen = repository / FROZEN
    hashes = sambosjon_execution._complete_stage(frozen, repository, manifest, protocol)
    module = sambosjon_execution._source(repository)
    sambosjon_execution._invoke(
        module,
        repository / sambosjon_execution.SOURCE,
        [
            "score",
            "--repository",
            str(repository),
            "--prepared",
            str(prepared),
            "--frozen",
            str(frozen),
            "--freeze-sha256",
            hashes["freeze.json"],
            "--output",
            str(output),
        ],
    )


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and reproduce Sämbosjön scores using the retained independent prediction freeze."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
