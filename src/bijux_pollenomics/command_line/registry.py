from __future__ import annotations

import argparse
from collections.abc import Callable

CommandHandler = Callable[[argparse.Namespace], int]

def build_command_handlers(
    *,
    run_collect_data: CommandHandler,
    run_publish_reports: CommandHandler,
    run_report_multi_country_map: CommandHandler,
) -> dict[str, CommandHandler]:
    """Build the direct-command handler registry."""
    return {
        "report-multi-country-map": run_report_multi_country_map,
        "collect-data": run_collect_data,
        "publish-reports": run_publish_reports,
    }


def resolve_handler(command_name: str, *, handlers: dict[str, CommandHandler]) -> CommandHandler:
    """Resolve the handler for one parsed command from a provided registry."""
    try:
        return handlers[command_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported command: {command_name}") from exc
