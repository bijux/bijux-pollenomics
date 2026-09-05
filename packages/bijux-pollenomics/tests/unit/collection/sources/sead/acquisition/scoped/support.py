"""PostgREST runtime harness for scoped SEAD acquisition tests."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    acquire_scoped_sead_relations,
)


class _PostgrestFixture:
    def __init__(
        self,
        tables: dict[str, list[dict[str, object]]],
        *,
        ignore_filter_table: str | None = None,
        never_finish_table: str | None = None,
    ) -> None:
        self.tables = tables
        self.ignore_filter_table = ignore_filter_table
        self.never_finish_table = never_finish_table
        self.calls: list[dict[str, object]] = []

    def __call__(
        self,
        endpoint: str,
        *,
        params: list[tuple[str, str]],
        headers: dict[str, str],
        timeout: float,
    ) -> object:
        table = endpoint.rsplit("/", 1)[-1]
        self.calls.append(
            {
                "table": table,
                "params": list(params),
                "headers": dict(headers),
                "timeout": timeout,
            }
        )
        rows = [dict(row) for row in self.tables[table]]
        for field, expression in params:
            if field in {"select", "order"}:
                continue
            if table == self.ignore_filter_table and expression.startswith("in."):
                continue
            rows = [row for row in rows if _postgrest_match(row.get(field), expression)]
        order = next((value for key, value in params if key == "order"), "")
        order_fields = tuple(value for value in order.split(",") if value)
        if order_fields:
            rows.sort(
                key=lambda row: tuple(
                    (row.get(field) is None, row.get(field)) for field in order_fields
                )
            )
        select = next(value for key, value in params if key == "select")
        projected = [
            {field: row.get(field) for field in select.split(",")} for row in rows
        ]
        start_text, end_text = headers["Range"].split("-", 1)
        start = int(start_text)
        end = int(end_text)
        page = projected[start : end + 1]
        if table == self.never_finish_table:
            if not page:
                page = projected[:1]
            while page and len(page) < end - start + 1:
                page.append(dict(page[-1]))
        return page


def _postgrest_match(value: object, expression: str) -> bool:
    if expression.startswith("in.(") and expression.endswith(")"):
        permitted = {
            int(item)
            for item in expression.removeprefix("in.(").removesuffix(")").split(",")
        }
        return value in permitted
    if expression.startswith("gte."):
        return isinstance(value, (int, float)) and float(value) >= float(
            expression.removeprefix("gte.")
        )
    if expression.startswith("lte."):
        return isinstance(value, (int, float)) and float(value) <= float(
            expression.removeprefix("lte.")
        )
    raise AssertionError(f"Unexpected fixture filter: {expression}")


def _fixed_clock() -> datetime:
    return datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


def _run(  # type: ignore[no-untyped-def]
    output_root: Path,
    fetcher: Callable[..., object],
    **overrides: Any,
):
    arguments: dict[str, object] = {
        "bbox": (5.0, 50.0, 30.0, 70.0),
        "governed_country_by_site_id": {
            1: "SE",
            2: "DK",
            3: "NO",
            4: "FI",
            5: "UNASSIGNED",
        },
        "country_assignment_id": "boundaries-fixture-v1",
        "scope_id": "nordic-fixture-v1",
        "run_id": "run-fixture-001",
        "parent_run_id": "parent-fixture-001",
        "build_id": "build-fixture-001",
        "fetch_json_fn": fetcher,
        "clock": _fixed_clock,
        "sleep_fn": lambda _seconds: None,
        "id_batch_size": 2,
        "page_size": 2,
        "max_pages": 10,
    }
    arguments.update(overrides)
    return acquire_scoped_sead_relations(output_root, **arguments)  # type: ignore[arg-type]
