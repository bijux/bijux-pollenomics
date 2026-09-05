"""Command-line contract for release-evidence publication."""

from __future__ import annotations

import argparse


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bijux-pollenomics-release-evidence")
    subparsers = parser.add_subparsers(dest="command", required=True)
    request = subparsers.add_parser(
        "request", help="derive the exact release-evidence request"
    )
    request.add_argument("--repository-root", default=".")
    request.add_argument("--output", required=True)
    write = subparsers.add_parser("write", help="build and atomically write evidence")
    write.add_argument("--repository-root", required=True)
    write.add_argument(
        "--request", required=True, help="repository-relative request JSON"
    )
    write.add_argument("--output", required=True, help="path below artifacts/")
    validate = subparsers.add_parser("validate", help="validate existing evidence")
    validate.add_argument("--repository-root", required=True)
    validate.add_argument("--manifest", required=True, help="path below artifacts/")
    return parser
