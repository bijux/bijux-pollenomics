"""Canonical event collection and manifest encoding."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

from .errors import EventValidationError
from .models import PhenomenonEvent


def _deduplicate_events(
    events: Sequence[PhenomenonEvent],
) -> tuple[tuple[PhenomenonEvent, ...], int]:
    by_id: dict[str, PhenomenonEvent] = {}
    duplicate_count = 0
    for event in events:
        existing = by_id.get(event.event_id)
        if existing is None:
            by_id[event.event_id] = event
        elif existing == event:
            duplicate_count += 1
        else:
            raise EventValidationError(
                "invalid_event_schema",
                f"conflicting records share event_id {event.event_id}",
            )
    return tuple(by_id[key] for key in sorted(by_id)), duplicate_count


def _event_manifest_digest(events: Sequence[PhenomenonEvent]) -> str:
    payload = [
        event._identity_dict() for event in sorted(events, key=lambda row: row.event_id)
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
