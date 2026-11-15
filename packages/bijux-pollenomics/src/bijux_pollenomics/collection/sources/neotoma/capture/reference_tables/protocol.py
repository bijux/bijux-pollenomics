"""Fixed metadata routes and source framing, without arbitrary database access."""

from __future__ import annotations

from dataclasses import fields
import math
from typing import Any

from ...client import decode_neotoma_json_object, positive_native_id
from ..models import _Request
from ..receipts import _request_record, _validate_receipt
from ..resources.models import NeotomaResourceLimits
from .models import (
    DEFAULT_REFERENCE_LIMITS,
    REFERENCE_TABLES,
    NeotomaReferenceTablePlan,
)


def validate_plan(
    plan: NeotomaReferenceTablePlan, limits: NeotomaResourceLimits
) -> None:
    if (
        not isinstance(plan, NeotomaReferenceTablePlan)
        or not isinstance(plan.tables, tuple)
        or not plan.tables
        or any(
            not isinstance(table, str) or table not in REFERENCE_TABLES
            for table in plan.tables
        )
        or len(set(plan.tables)) != len(plan.tables)
    ):
        raise ValueError("Neotoma reference table selection is unsupported")
    for field in (
        "max_requests",
        "max_attempts",
        "max_response_bytes",
        "max_total_bytes",
    ):
        value = positive_native_id(getattr(limits, field))
        if value > getattr(DEFAULT_REFERENCE_LIMITS, field):
            raise ValueError("Neotoma reference hard transport cap cannot be expanded")
    for field in ("timeout_seconds", "wall_seconds", "retry_delay_seconds"):
        value = getattr(limits, field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            or field != "retry_delay_seconds"
            and value == 0
            or value > getattr(DEFAULT_REFERENCE_LIMITS, field)
        ):
            raise ValueError("Neotoma reference time budget is invalid")


def request_for(table: str) -> _Request:
    if table not in REFERENCE_TABLES:
        raise ValueError("Neotoma reference table is unsupported")
    return _Request(
        f"reference-table-{table}-current-attempt-1",
        f"reference_table_{table}",
        f"/dbtables/{table}",
        {"limit": "10000", "offset": "0"},
    )


def plan_from_json(
    control: dict[str, Any],
) -> tuple[NeotomaReferenceTablePlan, NeotomaResourceLimits]:
    try:
        raw = control["plan"]
        if (
            not isinstance(raw, dict)
            or set(raw) != {"tables"}
            or not isinstance(raw["tables"], list)
            or not isinstance(control["limits"], dict)
            or set(control["limits"])
            != {field.name for field in fields(NeotomaResourceLimits)}
        ):
            raise ValueError("Neotoma reference control fields differ")
        plan = NeotomaReferenceTablePlan(tuple(raw["tables"]))
        limits = NeotomaResourceLimits(**control["limits"])
        validate_plan(plan, limits)
        return plan, limits
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Neotoma reference plan is malformed") from error


def assess_http(
    record: dict[str, Any], request: _Request, body: bytes, bound: int
) -> dict[str, Any]:
    if (
        set(record)
        != set(_request_record(request, record.get("utc_start", "")))
        | {
            "utc_end",
            "final_url",
            "http_status",
            "response_headers",
            "body_file",
            "body_complete",
            "retained_body_bytes",
            "retained_body_sha256",
            "terminal_status",
        }
        or type(record.get("retained_body_bytes")) is not int
    ):
        raise ValueError("Neotoma reference HTTP receipt fields differ")
    _validate_receipt(record, request, body, bound, require_success=False)
    if record["http_status"] != 200:
        return {
            "terminal_status": "unavailable_http",
            "http_status": record["http_status"],
            "absence_certified": False,
        }
    if not record["body_complete"]:
        return {
            "terminal_status": "refused_incomplete_body",
            "reason": "Incomplete or bounded reference entity",
        }
    try:
        _validate_receipt(record, request, body, bound)
    except ValueError as error:
        return {"terminal_status": "refused_http_receipt", "reason": str(error)}
    try:
        decode_neotoma_json_object(body)
    except ValueError as error:
        return {"terminal_status": "refused_native_json", "reason": str(error)}
    return {
        "terminal_status": "received_complete_unqualified_reference_table",
        "summary": {
            "schema_qualified": False,
            "prefix_limit": 10000,
            "prefix_offset": 0,
            "table_population_complete": False,
            "absence_certified": False,
            "units_interpreted": False,
        },
    }
