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
    COUNTRY_NAMES,
    DEFAULT_COUNTRY_LIMITS,
    NeotomaCountryAuthorityPlan,
)


def validate_plan(
    plan: NeotomaCountryAuthorityPlan, limits: NeotomaResourceLimits
) -> None:
    if (
        not isinstance(plan, NeotomaCountryAuthorityPlan)
        or not isinstance(plan.countries, tuple)
        or not plan.countries
        or any(
            type(country) is not str or country not in COUNTRY_NAMES
            for country in plan.countries
        )
        or len(set(plan.countries)) != len(plan.countries)
    ):
        raise ValueError("Neotoma country authority country selection is unsupported")
    for field in (
        "max_requests",
        "max_attempts",
        "max_response_bytes",
        "max_total_bytes",
    ):
        value = positive_native_id(getattr(limits, field))
        if value > getattr(DEFAULT_COUNTRY_LIMITS, field):
            raise ValueError(
                "Neotoma country authority hard transport cap cannot be expanded"
            )
    for field in ("timeout_seconds", "wall_seconds", "retry_delay_seconds"):
        value = getattr(limits, field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            or field != "retry_delay_seconds"
            and value == 0
            or value > getattr(DEFAULT_COUNTRY_LIMITS, field)
        ):
            raise ValueError("Neotoma country authority time budget is invalid")


def request_for(country: str) -> _Request:
    if type(country) is not str or country not in COUNTRY_NAMES:
        raise ValueError("Neotoma country authority country is unsupported")
    return _Request(
        f"country-authority-{country}-current-attempt-1",
        f"country_authority_{country}",
        "/geopoliticalunits",
        {"gpname": country, "rank": "1", "lower": "false"},
    )


def plan_from_json(
    control: dict[str, Any],
) -> tuple[NeotomaCountryAuthorityPlan, NeotomaResourceLimits]:
    try:
        raw = control["plan"]
        if (
            not isinstance(raw, dict)
            or set(raw) != {"countries"}
            or not isinstance(raw["countries"], list)
            or not isinstance(control["limits"], dict)
            or set(control["limits"])
            != {field.name for field in fields(NeotomaResourceLimits)}
        ):
            raise ValueError("Neotoma country authority control fields differ")
        plan = NeotomaCountryAuthorityPlan(tuple(raw["countries"]))
        limits = NeotomaResourceLimits(**control["limits"])
        validate_plan(plan, limits)
        return plan, limits
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Neotoma country authority plan is malformed") from error


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
        raise ValueError("Neotoma country authority HTTP receipt fields differ")
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
            "reason": "Incomplete or bounded country metadata entity",
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
        "terminal_status": "received_complete_unqualified_country_metadata",
        "summary": {
            "schema_qualified": False,
            "lower_units_included": False,
            "dictionary_complete": False,
            "absence_certified": False,
            "geometry_interpreted": False,
        },
    }


class _UnavailableCountryAuthority(ValueError):
    """The complete source returned no identified country record."""


def qualify_native_country(country: str, native: dict[str, Any]) -> int:
    """Validate only a unique literal country identity, retaining unknown fields."""
    if country not in COUNTRY_NAMES or native.get("status") != "success":
        raise ValueError("Country authority selector or native source status differs")
    rows = native.get("data")
    if not isinstance(rows, list):
        raise ValueError("Country authority native data is not an array")
    if not rows or (
        len(rows) == 1
        and isinstance(rows[0], dict)
        and {"geopoliticalid", "geopoliticalname", "rank"} <= set(rows[0])
        and all(value is None for value in rows[0].values())
    ):
        raise _UnavailableCountryAuthority(
            "No identified native country record returned"
        )
    if len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("Country authority requires exactly one native source record")
    row = rows[0]
    native_id = positive_native_id(row.get("geopoliticalid"))
    if (
        row.get("geopoliticalname") != country
        or type(row.get("rank")) is not int
        or row["rank"] != 1
        or type(row.get("highergeopoliticalid")) is not int
        or "geopoliticalunit" not in row
        or row["geopoliticalunit"] is not None
        and not isinstance(row["geopoliticalunit"], str)
    ):
        raise ValueError("Country authority native name, rank, parent or unit differs")
    return native_id
