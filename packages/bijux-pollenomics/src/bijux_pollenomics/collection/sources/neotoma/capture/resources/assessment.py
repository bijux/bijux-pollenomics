"""Derive the terminal assessment from one authenticated retained attempt."""

from __future__ import annotations

from typing import Any

from ..models import _Request
from ..receipts import _validate_receipt
from .models import NeotomaResourceSpec
from .profiles import classify_body

ASSESSMENT_FIELDS = (
    "terminal_status",
    "summary",
    "reason",
    "http_status",
    "absence_certified",
)
QUALIFIED_STATUSES = {"parsed_native", "reused_qualified_native"}


def assess_http(
    resource: NeotomaResourceSpec,
    version: str,
    record: dict[str, Any],
    request: _Request,
    body: bytes,
    bound: int,
) -> dict[str, Any]:
    """Authenticate custody before assessing availability or native content."""
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
            "reason": "Bounded or incomplete HTTP entity",
        }
    try:
        _validate_receipt(record, request, body, bound)
    except ValueError as error:
        return {"terminal_status": "refused_http_receipt", "reason": str(error)}
    status, summary = classify_body(resource, version, body)
    return {"terminal_status": status, "summary": summary}
