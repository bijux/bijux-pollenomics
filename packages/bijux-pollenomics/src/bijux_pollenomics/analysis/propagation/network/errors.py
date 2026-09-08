"""Propagation event contract failures."""

from __future__ import annotations

from typing import Never


class EventValidationError(ValueError):
    """Refuse a source event that cannot satisfy the phenomenon-event contract."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        super().__init__(detail)


def _invalid(detail: str) -> Never:
    raise EventValidationError("invalid_event_schema", detail)
