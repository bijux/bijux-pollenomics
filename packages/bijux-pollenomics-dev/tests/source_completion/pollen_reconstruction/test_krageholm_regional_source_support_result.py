"""Observe one committed KRAG source-support result without importing its producer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .krageholm_regional_source_support.native_rows import require
from .krageholm_regional_source_support.verification import verify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
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
    result = verify(repository, args.result.resolve(strict=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
