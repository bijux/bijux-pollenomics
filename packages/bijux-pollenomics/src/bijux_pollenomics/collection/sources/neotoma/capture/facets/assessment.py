"""Authenticate facet HTTP entities without inventing a native response schema."""

from __future__ import annotations

from typing import Any

from ...client import decode_neotoma_json_object
from ..models import _Request
from ..receipts import _validate_receipt


def assess_http(
    record: dict[str, Any], request: _Request, body: bytes, bound: int
) -> dict[str, Any]:
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
            "reason": "Incomplete or bounded HTTP entity",
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
        "terminal_status": "received_complete_unqualified_facet",
        "summary": {
            "schema_qualified": False,
            "payload_owner_status": "not_established",
            "endpoint_owner_status": "authenticated_request_dataset",
            "absence_certified": False,
            "units_interpreted": False,
        },
    }
