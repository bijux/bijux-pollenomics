"""Local retained-reference commands; no provider, source replay or model dispatch."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path
import sys
from typing import Any

from bijux_pollenomics.core.filesystem import read_regular_file

from .contracts import (
    MAX_BYTES,
    MAX_METADATA,
    POSTURE,
    NeotomaTaxonomyReferenceFile,
    NeotomaTaxonomyReferenceSource,
    decode,
    digest,
)
from .contrast import plain, write_neotoma_taxonomy_reference_contrast
from .publication import write_neotoma_taxonomy_reference_archive
from .reading import read_neotoma_taxonomy_reference_taxa


def _source(path: Path, expected: str) -> NeotomaTaxonomyReferenceSource:
    if not digest(expected):
        raise ValueError("Independent retained-source plan SHA256 required")
    raw = read_regular_file(path, max_bytes=MAX_METADATA)
    if sha256(raw).hexdigest() != expected:
        raise ValueError("Retained-source plan identity differs")
    value = decode(raw)
    if not isinstance(value, dict) or set(value) != {
        "revision",
        "files",
        "git_metadata",
        "transport",
        "intake_intervals",
        "attribution",
    }:
        raise ValueError("Retained-source plan fields differ")

    def pins(name: str) -> dict[str, NeotomaTaxonomyReferenceFile]:
        items = value[name]
        if not isinstance(items, dict):
            raise ValueError("Retained-source plan needs explicit file bindings")
        result = {}
        for key, row in items.items():
            if (
                not isinstance(row, dict)
                or set(row) != {"path", "bytes", "sha256"}
                or type(row["path"]) is not str
            ):
                raise ValueError("Retained-source plan file fields differ")
            result[key] = NeotomaTaxonomyReferenceFile(
                Path(row["path"]), row["bytes"], row["sha256"]
            )
        return result

    if not isinstance(value["intake_intervals"], dict):
        raise ValueError("Retained-source plan needs explicit intake intervals")
    return NeotomaTaxonomyReferenceSource(
        value["revision"],
        pins("files"),
        pins("git_metadata"),
        pins("transport"),
        value["intake_intervals"],
        value["attribution"],
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Retain or query dated global Neotoma taxonomy references without network access."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    retain = commands.add_parser(
        "retain",
        help="Publish the exact three independently pinned retained Git projections.",
    )
    retain.add_argument("--source-plan", required=True, type=Path)
    retain.add_argument("--source-plan-sha256", required=True)
    retain.add_argument("--output", required=True, type=Path)
    lookup = commands.add_parser(
        "lookup",
        help="Read explicit dated native-ID records; database dates are not sample ages.",
    )
    comparison = commands.add_parser(
        "contrast-frontier",
        help="Contrast explicitly stored frontier parts; do not reconstruct a delta or source graph.",
    )
    for target in (lookup, comparison):
        target.add_argument("--archive", required=True, type=Path)
        target.add_argument("--manifest-sha256", required=True)
    lookup.add_argument("--taxon-id", required=True, action="append", type=int)
    comparison.add_argument("--chain", required=True, type=Path)
    comparison.add_argument("--chain-manifest-sha256", required=True)
    comparison.add_argument("--output", required=True, type=Path)
    return parser


def _emit(value: Any, *, error: bool = False) -> None:
    from ...resource_catalogue.archive.files import encoded_json

    raw = encoded_json(plain(value))
    if len(raw) > MAX_BYTES:
        raise ValueError("Taxonomy reference command result exceeds its byte bound")
    print(raw.decode(), end="", file=sys.stderr if error else sys.stdout)


def main(argv: Sequence[str] | None = None) -> int:
    """Use the maintained owners and report ordinary failures without false success."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "retain":
            result = write_neotoma_taxonomy_reference_archive(
                args.output,
                source_provenance=_source(args.source_plan, args.source_plan_sha256),
            )
            _emit(
                {
                    "status": "published_dated_reference_archive",
                    "manifest_sha256": result.manifest_sha256,
                    **POSTURE,
                }
            )
        elif args.command == "lookup":
            records = read_neotoma_taxonomy_reference_taxa(
                args.archive,
                expected_manifest_sha256=args.manifest_sha256,
                taxon_ids=tuple(args.taxon_id),
            )
            _emit(
                {
                    "status": "dated_reference_lookup",
                    "reference_manifest_sha256": args.manifest_sha256,
                    "records": records,
                    **POSTURE,
                }
            )
        else:
            comparison = write_neotoma_taxonomy_reference_contrast(
                args.output,
                reference_directory=args.archive,
                expected_manifest_sha256=args.manifest_sha256,
                chain_directory=args.chain,
                expected_chain_manifest_sha256=args.chain_manifest_sha256,
            )
            _emit(
                {
                    "status": "published_recorded_reference_contrast",
                    "report_file": "frontier-contrast.json",
                    "summary": comparison.summary,
                    **POSTURE,
                }
            )
    except (OSError, ValueError) as error:
        _emit({"status": "refused", "error": str(error), **POSTURE}, error=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
