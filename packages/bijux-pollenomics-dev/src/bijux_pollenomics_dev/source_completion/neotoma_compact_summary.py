"""Write the compact Neotoma sample account from its retained replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import runpy

REPLAY = Path("docs/report/source-relations/neotoma/compact-summary/replay.py")


def publish(repository: Path, output: Path) -> None:
    """Call the pinned replay and preserve its existing JSON serialization."""
    repository = repository.resolve(strict=True)
    script = (repository / REPLAY).resolve(strict=True)
    if output.is_symlink():
        raise ValueError("Artifact output may not be a symlink")
    output = output.resolve()
    if not script.is_relative_to(repository) or not script.is_file():
        raise ValueError("Neotoma compact replay is outside the repository")
    if (
        output == repository / "artifacts"
        or output.exists()
        or not output.is_relative_to(repository / "artifacts")
    ):
        raise ValueError("Absent repository artifact output required")
    replay = runpy.run_path(str(script))
    report = replay["build_report"]()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    publish(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
