from __future__ import annotations

import argparse
from collections.abc import Callable

CommandHandler = Callable[[argparse.Namespace], int]

__all__ = ["CommandHandler", "build_command_handlers", "resolve_handler"]


def build_command_handlers(
    *,
    run_collect_data: CommandHandler,
    run_ownership_map: CommandHandler,
    run_publish_reports: CommandHandler,
    run_report_multi_country_map: CommandHandler,
    run_product_scope: CommandHandler,
    run_source_support: CommandHandler,
    run_surface_map: CommandHandler,
) -> dict[str, CommandHandler]:
    """Build the direct-command handler registry."""
    return {
        "report-multi-country-map": run_report_multi_country_map,
        "collect-data": run_collect_data,
        "ownership-map": run_ownership_map,
        "publish-reports": run_publish_reports,
        "product-scope": run_product_scope,
        "source-support": run_source_support,
        "surface-map": run_surface_map,
    }


def resolve_handler(
    command_name: str, *, handlers: dict[str, CommandHandler]
) -> CommandHandler:
    """Resolve the handler for one parsed command from a provided registry."""
    try:
        return handlers[command_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported command: {command_name}") from exc
