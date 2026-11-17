"""Native unresolved identities and non-expanding acquisition budgets."""

from __future__ import annotations

from dataclasses import dataclass, fields
import math
from uuid import UUID


@dataclass(frozen=True)
class SeadContextSite:
    """A retained native identity with explicitly unresolved membership."""

    site_id: int
    site_uuid: str
    membership_status: str

    def __post_init__(self) -> None:
        """Reject invented country assignments and ambiguous source identities."""
        if type(self.site_id) is not int or self.site_id <= 0:
            raise ValueError("Context site ID must be a positive native integer")
        if (
            not isinstance(self.site_uuid, str)
            or str(UUID(self.site_uuid)) != self.site_uuid
        ):
            raise ValueError("Context site UUID must be canonical source text")
        if self.membership_status not in {"review", "unassigned"}:
            raise ValueError("Context membership must remain review or unassigned")


@dataclass(frozen=True)
class SeadContextLimits:
    """Callers may narrow, but never expand, the reviewed context profile."""

    max_requests: int = 256
    max_bytes: int = 16 * 1024 * 1024
    max_rows: int = 20_000
    response_bytes: int = 1024 * 1024
    max_seconds: float = 900.0
    timeout_seconds: float = 30.0
    page_size: int = 100
    max_pages: int = 11
    batch_size: int = 100
    max_dependency_ids: int = 1000

    def __post_init__(self) -> None:
        """Require positive native finite limits within fixed reviewed ceilings."""
        for field in fields(self):
            value = getattr(self, field.name)
            valid_type = (
                type(value) in {int, float}
                if field.name.endswith("seconds")
                else type(value) is int
            )
            if (
                not valid_type
                or not math.isfinite(value)
                or not 0 < value <= field.default
            ):
                raise ValueError(
                    f"Context budget is outside the reviewed profile: {field.name}"
                )


DEFAULT_CONTEXT_LIMITS = SeadContextLimits()
