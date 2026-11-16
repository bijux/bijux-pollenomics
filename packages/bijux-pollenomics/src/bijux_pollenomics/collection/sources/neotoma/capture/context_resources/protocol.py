"""Two fixed official routes and strict syntax without native schema inference."""

from __future__ import annotations

from dataclasses import fields
import math
import re
from typing import Any
from urllib.parse import urlencode

from ...client import decode_neotoma_json_object, positive_native_id
from ..models import _Request
from ..receipts import _request_record, _validate_receipt
from ..resources.models import NeotomaResourceLimits
from ..resources.replay import _same_json
from .models import (
    DEFAULT_CONTEXT_LIMITS,
    RESOURCE_KINDS,
    NeotomaContextResourcePlan,
)


def digest(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("Context source requires an independent SHA256 identity")
    return value


def validate_plan(
    plan: NeotomaContextResourcePlan, limits: NeotomaResourceLimits
) -> None:
    if not isinstance(plan, NeotomaContextResourcePlan):
        raise ValueError("Context resource plan has an invalid type")
    digest(plan.context_manifest_sha256)
    digest(plan.native_archive_manifest_sha256)
    if (
        not isinstance(plan.site_ids, tuple)
        or not 0 < len(plan.site_ids) <= 128
        or any(type(value) is not int or value <= 0 for value in plan.site_ids)
        or len(set(plan.site_ids)) != len(plan.site_ids)
        or not isinstance(plan.resource_kinds, tuple)
        or not plan.resource_kinds
        or any(kind not in RESOURCE_KINDS for kind in plan.resource_kinds)
        or len(set(plan.resource_kinds)) != len(plan.resource_kinds)
        or tuple(kind for kind in RESOURCE_KINDS if kind in plan.resource_kinds)
        != plan.resource_kinds
        or type(plan.lake_buffer_m) is not int
        or plan.lake_buffer_m != 1000
        or type(plan.lake_precision) is not float
        or plan.lake_precision != 0.0001
        or type(plan.lake_projection) is not int
        or plan.lake_projection != 4326
    ):
        raise ValueError(
            "Context resource selection or fixed candidate parameters differ"
        )
    if not isinstance(limits, NeotomaResourceLimits):
        raise ValueError("Context transport limits have an invalid type")
    caps = {
        "max_requests": 128,
        "max_attempts": 1,
        "max_response_bytes": 2 * 1024 * 1024,
        "max_total_bytes": 256 * 1024 * 1024,
    }
    for field, cap in caps.items():
        if positive_native_id(getattr(limits, field)) > cap:
            raise ValueError("Context resource hard transport cap cannot be expanded")
    for field in ("timeout_seconds", "wall_seconds", "retry_delay_seconds"):
        value = getattr(limits, field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            or field != "retry_delay_seconds"
            and value == 0
            or value > getattr(DEFAULT_CONTEXT_LIMITS, field)
        ):
            raise ValueError("Context resource time budget is invalid")


class _DepositionalEnvironmentRequest(_Request):
    """The apps namespace is fixed here, without extending generic data routes."""

    @property
    def url(self) -> str:
        return "https://api.neotomadb.org/v2.0/apps/depenvt?" + urlencode(
            self.parameters
        )


def request_for(kind: str, site_id: int) -> _Request:
    positive_native_id(site_id)
    if kind not in RESOURCE_KINDS:
        raise ValueError("Unsupported context resource kind")
    name = f"site-{site_id}-{kind}-current-attempt-1"
    if kind == "depositional_environment":
        return _DepositionalEnvironmentRequest(
            name, kind, "/depenvt", {"siteid": str(site_id)}, site_id
        )
    return _Request(
        name,
        kind,
        "/spatial/lakes",
        {"siteid": str(site_id), "buffer": "1000", "prec": "0.0001", "proj": "4326"},
        site_id,
    )


def plan_from_json(
    control: dict[str, Any],
) -> tuple[NeotomaContextResourcePlan, NeotomaResourceLimits]:
    try:
        raw = control["plan"]
        if (
            not isinstance(raw, dict)
            or set(raw) != {field.name for field in fields(NeotomaContextResourcePlan)}
            or not isinstance(raw["site_ids"], list)
            or not isinstance(raw["resource_kinds"], list)
            or not isinstance(control["limits"], dict)
            or set(control["limits"])
            != {field.name for field in fields(NeotomaResourceLimits)}
        ):
            raise ValueError("Context plan fields differ")
        plan = NeotomaContextResourcePlan(
            **{
                **raw,
                "site_ids": tuple(raw["site_ids"]),
                "resource_kinds": tuple(raw["resource_kinds"]),
            }
        )
        limits = NeotomaResourceLimits(**control["limits"])
        validate_plan(plan, limits)
        return plan, limits
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Context resource control is malformed") from error


def verify_request_metadata(record: dict[str, Any], request: _Request) -> None:
    expected = _request_record(request, record.get("utc_start", ""))
    if any(not _same_json(record.get(key), value) for key, value in expected.items()):
        raise ValueError("Context resource receipt request owner differs")


def assess_http(
    record: dict[str, Any], request: _Request, body: bytes, bound: int
) -> dict[str, Any]:
    verify_request_metadata(record, request)
    expected = set(_request_record(request, record.get("utc_start", ""))) | {
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
    if set(record) != expected or type(record.get("retained_body_bytes")) is not int:
        raise ValueError("Context resource receipt fields differ")
    _validate_receipt(record, request, body, bound, require_success=False)
    terminal = (
        "complete_http_200"
        if record["http_status"] == 200 and record["body_complete"]
        else "refused_http_response"
    )
    if record["terminal_status"] != terminal:
        raise ValueError("Context resource transport declarations contradict")
    if record["http_status"] != 200:
        return {
            "terminal_status": "unavailable_http",
            "http_status": record["http_status"],
            "absence_certified": False,
        }
    if not record["body_complete"]:
        return {
            "terminal_status": "refused_incomplete_body",
            "reason": "Incomplete or bounded context source entity",
        }
    try:
        _validate_receipt(record, request, body, bound)
    except ValueError as error:
        return {"terminal_status": "refused_http_receipt", "reason": str(error)}
    try:
        # A single wrapper admits arrays/scalars without guessing the source schema.
        # The shared decoder still owns duplicate-member and numeric-loss refusal.
        wrapped = decode_neotoma_json_object(b'{"source":' + body + b"}")
        if set(wrapped) != {"source"}:
            raise ValueError("Context source is not a single JSON value")
    except ValueError as error:
        return {"terminal_status": "refused_native_json", "reason": str(error)}
    return {
        "terminal_status": "received_complete_unqualified_context_resource",
        "summary": {
            "schema_qualified": False,
            "native_payload_owner_verified": False,
            "dated_basin_geometry_admitted": False,
            "absence_certified": False,
            "scientific_admission": "not_asserted",
        },
    }
