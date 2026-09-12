"""Canonical local source acquisition, build, provisioning and actual-R commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from .contracts import ReferenceRefusal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in ("fetch", "build-r", "provision", "certify"):
        child = subparsers.add_parser(operation)
        child.add_argument("--lock", type=Path, required=True)
        child.add_argument("--repository", type=Path, required=True)
        child.add_argument("--output", type=Path, required=True)
        if operation != "certify":
            child.add_argument("--source-cache", type=Path, required=True)
        if operation == "build-r":
            child.add_argument("--prefix", type=Path, required=True)
        if operation in {"provision", "certify"}:
            child.add_argument("--library", type=Path, required=True)
            child.add_argument("--rscript", type=Path, required=True)
        if operation == "provision":
            child.add_argument("--r", type=Path, required=True)
            child.add_argument("--pkg-config-path", type=Path)
            child.add_argument("--makevars", type=Path)
            child.add_argument("--runtime-receipt", type=Path)
        if operation == "certify":
            child.add_argument("--provision-receipt", type=Path, required=True)
    args = parser.parse_args()
    common = {
        "lock_path": args.lock,
        "repository": args.repository,
        "output": args.output,
    }
    try:
        if args.operation == "fetch":
            from .environment.acquisition import acquire

            acquire(**common, source_cache=args.source_cache)
        elif args.operation == "build-r":
            from .environment.build import build_runtime

            build_runtime(**common, source_cache=args.source_cache, prefix=args.prefix)
        elif args.operation == "provision":
            from .environment.provision import provision

            provision(
                **common,
                source_cache=args.source_cache,
                library=args.library,
                r=args.r,
                rscript=args.rscript,
                pkg_config_path=args.pkg_config_path,
                makevars=args.makevars,
                runtime_receipt=args.runtime_receipt,
            )
        else:
            from .certification import certify

            certify(
                **common,
                library=args.library,
                rscript=args.rscript,
                provision_receipt=args.provision_receipt,
            )
    except (ReferenceRefusal, OSError, ValueError) as error:
        parser.exit(2, "Reference certification refused: " + str(error) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
