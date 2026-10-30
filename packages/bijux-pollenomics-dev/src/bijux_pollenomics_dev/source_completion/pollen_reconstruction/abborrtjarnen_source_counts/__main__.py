"""Compare the retained original ABBO five-taxon measurements without imputation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .comparison import run


def main() -> None:
    """Parse retained-source comparison arguments and print its result status."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "source-root", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.repository, args.source_root, args.output.absolute())
    print(json.dumps({"status": result["status"], "model_fits": 0}))


if __name__ == "__main__":
    main()
