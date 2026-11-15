"""Account for the original capture prefix within recorded and caller limits."""

from __future__ import annotations

import math
from typing import Any

from ...capture.facets.protocol import facet_identity
from ...capture.resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits
from ...resource_catalogue.source_projection import _same

_COUNT_LIMITS = (
    "max_requests",
    "max_attempts",
    "max_response_bytes",
    "max_total_bytes",
)


def _validate_limits(limits: NeotomaResourceLimits) -> None:
    if not isinstance(limits, NeotomaResourceLimits) or any(
        type(getattr(limits, key)) is not int or getattr(limits, key) < 1
        for key in _COUNT_LIMITS
    ):
        raise ValueError("Selected capture limits must use positive native integers")
    for key in ("timeout_seconds", "wall_seconds", "retry_delay_seconds"):
        value = getattr(limits, key)
        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
            or value < 0
            or key != "retry_delay_seconds"
            and value == 0
        ):
            raise ValueError("Selected capture time limit is invalid")


def capture_response_bound(
    capture: dict[str, Any],
    selected: dict[str, Any],
    receipt: dict[str, Any],
    caller_limits: NeotomaResourceLimits,
) -> int:
    """Budget this original capture prefix, not aggregate SDK I/O or later history."""
    recorded = capture["limits"]
    _validate_limits(recorded)
    limits: dict[str, int] = {
        key: min(
            getattr(recorded, key),
            getattr(caller_limits, key),
            getattr(DEFAULT_RESOURCE_LIMITS, key),
        )
        for key in _COUNT_LIMITS
    }
    facet = capture["descriptor"]["kind"] == "facet"
    rows = capture["document"]["facets" if facet else "resources"]
    if facet:
        expected = [
            facet_identity(root, name)
            for root in sorted(
                capture["plan"].resources, key=lambda root: root.dataset_id
            )
            for name in capture["plan"].facets
        ]
        if len(rows) != len(expected) or any(
            not _same({key: row.get(key) for key in owner}, owner)
            for row, owner in zip(rows, expected, strict=True)
        ):
            raise ValueError("Selected capture budget ledger order differs")
    count = total = 0
    for row in rows:
        for ordinal, reference in enumerate(row["attempts"], 1):
            count += 1
            if (
                count > limits["max_requests"]
                or ordinal > limits["max_attempts"]
                or total >= limits["max_total_bytes"]
            ):
                raise ValueError("Selected request exceeds its capture budget")
            bound = min(limits["max_response_bytes"], limits["max_total_bytes"] - total)
            size = (
                capture["descriptor"]["files"][reference["body_file"]]["bytes"]
                if "body_file" in reference
                else 0
            )
            own = row is selected and ordinal == len(selected["attempts"])
            complete = row["terminal_status"] in {
                "received_complete_unqualified_facet",
                "received_complete_unqualified_linked_resource",
                "refused_http_receipt",
                "refused_native_json",
            } and ordinal == len(row["attempts"])
            extra = int(not receipt["body_complete"]) if own else int(not complete)
            if size > bound + extra:
                raise ValueError(
                    "Selected capture body exceeds its remaining byte budget"
                )
            if own:
                return bound
            total += size
    raise ValueError("Selected capture budget attempt is absent")
