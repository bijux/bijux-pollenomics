"""Command-line entry point for governed boundary review publication."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import asdict
import json
from pathlib import Path

from .publication import materialize_boundary_country_review


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bijux-pollenomics-boundary-country-review")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Materialize the governed boundary and country-decision review bundle."""
    args = _parser().parse_args(argv)
    report = materialize_boundary_country_review(
        args.repository_root, output_root=args.output_root
    )
    print(json.dumps(asdict(report), default=str, sort_keys=True))
    return 0
