from __future__ import annotations

import argparse

from .runtime.handlers import run_collect_data, run_publish_reports, run_report_country, run_report_multi_country_map
from .runtime.registry import build_command_handlers, resolve_handler

__all__ = [
    "run_collect_data",
    "run_publish_reports",
    "run_report_country",
    "run_report_multi_country_map",
    "run_command",
]


def run_command(args: argparse.Namespace, *, parser: argparse.ArgumentParser) -> int:
    """Dispatch one parsed command to its handler."""
    if args.command == "report-country":
        return run_report_country(args, parser=parser)
    handlers = build_command_handlers(
        run_collect_data=run_collect_data,
        run_publish_reports=run_publish_reports,
        run_report_multi_country_map=run_report_multi_country_map,
    )
    try:
        handler = resolve_handler(args.command, handlers=handlers)
    except ValueError:
        parser.error(f"Unsupported command: {args.command}")
        raise AssertionError("parser.error should have exited") from None
    return handler(args)
