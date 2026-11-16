"""Finite operational limits for explicitly selected ancestry frontier requests."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from ..models import MAX_ENTITY_BYTES

MAX_REQUESTS = 16
MAX_RESPONSE_BYTES = MAX_REQUESTS * (MAX_ENTITY_BYTES + 1)
MAX_CONTROL_BYTES = 1024 * 1024


@dataclass(frozen=True)
class NeotomaTaxonFrontierCaptureLimits:
    """Bound one explicit batch without changing the ancestry wire or graph limits."""

    max_requests: int = MAX_REQUESTS
    max_total_response_bytes: int = MAX_RESPONSE_BYTES
    timeout_seconds: float = 60
    wall_seconds: float = 900

    def validate(self, target_count: int) -> None:
        """Reserve enough bytes for every selected response including its sentinel."""
        for name, maximum in (
            ("max_requests", MAX_REQUESTS),
            ("max_total_response_bytes", MAX_RESPONSE_BYTES),
        ):
            value = getattr(self, name)
            if type(value) is not int or not 0 < value <= maximum:
                raise ValueError("Frontier capture requires native finite budgets")
        for name, maximum in (("timeout_seconds", 60), ("wall_seconds", 900)):
            value = getattr(self, name)
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not 0 < value <= maximum
            ):
                raise ValueError(
                    "Frontier capture requires finite positive time limits"
                )
        if (
            target_count > self.max_requests
            or target_count * (MAX_ENTITY_BYTES + 1) > self.max_total_response_bytes
        ):
            raise ValueError(
                "Frontier capture cannot cover the complete selected batch"
            )


@dataclass(frozen=True)
class NeotomaTaxonFrontierCapture:
    """Identify the closed retained receipt tree, without claiming scientific admission."""

    directory: Path
    manifest_sha256: str
    request_count: int
    response_bytes: int
    target_keys: tuple[str, ...]


DEFAULT_CAPTURE_LIMITS = NeotomaTaxonFrontierCaptureLimits()
