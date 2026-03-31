from __future__ import annotations

import argparse
from collections.abc import Callable

from .handlers import run_collect_data, run_publish_reports, run_report_country, run_report_multi_country_map


CommandHandler = Callable[[argparse.Namespace], int]


def run_command(args: argparse.Namespace, *, parser: argparse.ArgumentParser) -> int:
    """Dispatch one parsed command to its handler."""
    handlers: dict[str, CommandHandler] = {
        "report-multi-country-map": run_report_multi_country_map,
        "collect-data": run_collect_data,
        "publish-reports": run_publish_reports,
    }
    if args.command == "report-country":
        return run_report_country(args, parser=parser)
    try:
        handler = handlers[args.command]
    except KeyError as exc:
        parser.error(f"Unsupported command: {args.command}")
        raise AssertionError("parser.error should have exited") from exc
    return handler(args)
