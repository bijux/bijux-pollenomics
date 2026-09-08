"""Command-line materialization for the governed SEAD review packet."""

from __future__ import annotations

import argparse
from pathlib import Path

from .publication import materialize_sead_scientific_classification_review


def main() -> int:
    """Materialize the packet below an explicit repository data root."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    paths = materialize_sead_scientific_classification_review(args.data_root)
    for key, path in sorted(paths.items()):
        print(f"{key}={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
