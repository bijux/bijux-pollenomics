"""Repository developer entry point for private review bundles."""

import argparse
import json
from pathlib import Path

from . import build_review, read_review, validate_decisions, write_review
from .decisions import load_review_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--root", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--rootsi-inventory")
    check = commands.add_parser("validate-return")
    check.add_argument("--bundle", required=True, type=Path)
    check.add_argument("--decisions", required=True, type=Path)
    check.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "build":
        payload = build_review(args.root, rootsi_inventory=args.rootsi_inventory)
        write_review(payload, args.output)
        print(
            json.dumps(
                {
                    "row_count": payload["row_count"],
                    "bundle_sha256": payload["bundle_sha256"],
                    "source_row_counts": payload["source_row_counts"],
                },
                sort_keys=True,
            )
        )
    else:
        if args.bundle.name != "taxa-review.json":
            raise ValueError("--bundle must name the completed taxa-review.json")
        result = validate_decisions(
            read_review(args.bundle.parent),
            load_review_json(args.decisions.read_bytes()),
        )
        with args.output.open("x") as stream:
            stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
