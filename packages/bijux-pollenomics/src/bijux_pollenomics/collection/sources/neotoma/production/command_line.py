from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any


def parse_alias(value: str) -> tuple[str, str]:
    key, separator, country = value.partition("=")
    if not separator or not key.strip() or not country.strip():
        raise argparse.ArgumentTypeError(
            "aliases must use non-empty RAW=COUNTRY values"
        )
    return key.strip(), country.strip()


def parser(
    *, alias_parser: Callable[[str], tuple[str, str]], producer_version: str
) -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Validate and materialize the pinned Neotoma relational snapshot."
    )
    result.add_argument("--raw-archive", required=True, type=Path)
    result.add_argument("--boundary-root", required=True, type=Path)
    result.add_argument("--output", required=True, type=Path)
    result.add_argument("--approved-output-parent", required=True, type=Path)
    result.add_argument("--producer-version", default=producer_version)
    result.add_argument("--rows-per-part", type=int, default=50_000)
    result.add_argument("--proximity-tolerance", type=float, default=0.15)
    result.add_argument(
        "--raw-country-alias", action="append", default=[], type=alias_parser
    )
    return result


def run_cli(
    argv: Sequence[str] | None,
    *,
    build_parser: Callable[[], argparse.ArgumentParser],
    config_type: Any,
    run_production: Any,
    json_module: Any,
    error_stream: Any,
) -> int:
    args = build_parser().parse_args(argv)
    config = config_type(
        producer_version=args.producer_version,
        rows_per_part=args.rows_per_part,
        proximity_tolerance=args.proximity_tolerance,
        raw_country_aliases=tuple(args.raw_country_alias),
    )
    try:
        report = run_production(
            raw_archive_root=args.raw_archive,
            boundary_root=args.boundary_root,
            output_root=args.output,
            approved_output_parent=args.approved_output_parent,
            config=config,
        )
    except (OSError, ValueError) as error:
        print(
            json_module.dumps(
                {"error": str(error), "status": "failed"}, sort_keys=True
            ),
            file=error_stream,
        )
        return 1
    print(json_module.dumps({"status": "ok", **report.to_dict()}, sort_keys=True))
    return 0
