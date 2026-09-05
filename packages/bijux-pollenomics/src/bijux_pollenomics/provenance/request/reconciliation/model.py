"""Internal count posture shared by reconciliation adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DerivedCount:
    """Account for every candidate across terminal reconciliation postures."""

    candidate: int
    eligible: int
    accepted: int
    unresolved: int
    excluded: int
    refused: int
    reason_codes: tuple[str, ...] = ()
