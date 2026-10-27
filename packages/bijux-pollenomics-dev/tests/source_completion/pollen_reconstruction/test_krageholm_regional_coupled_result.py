"""Observe one closed fixed-KRAG regional coupled study without producer imports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .krageholm_regional_coupled.scalar import require
from .krageholm_regional_coupled.verification import verify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--result-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    output = args.output.absolute()
    require(
        ".." not in args.output.parts
        and output.resolve().is_relative_to(repository / "artifacts")
        and not output.exists()
        and not any(parent.is_symlink() for parent in output.parents),
        "fresh artifacts output with regular ancestry required",
    )
    result = verify(repository, args.result.absolute(), args.result_sha256)
    body = json.dumps(result, indent=2, allow_nan=False) + "\n"
    require(
        len(body.encode()) <= 5 * 1024**2,
        "independent check exceeds prospective output budget",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body)
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
