"""Route the existing seeded joint-site draw study into owner artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from .writer_execution import replay_to_artifacts

SOURCE = Path("docs/report/method-certification/joint-site-draws/replay.py")


def run(repository: Path, output: Path) -> None:
    replay_to_artifacts(repository, output, SOURCE)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
