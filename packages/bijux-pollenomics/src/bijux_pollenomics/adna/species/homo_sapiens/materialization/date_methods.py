"""Syntax-only classification of source-native AADR dating methods."""

from __future__ import annotations

import re

from .chronology import AadrDateMethodEvidence, DateMethodFamily

_METHOD_FAMILIES: tuple[tuple[re.Pattern[str], DateMethodFamily], ...] = (
    (re.compile(r"^direct(?:$|[\s:(])"), "direct"),
    (re.compile(r"^context(?:$|[\s:(])"), "contextual"),
    (re.compile(r"^modern(?:$|[\s:(])"), "modern"),
    (re.compile(r"^(?:known|historical)(?:$|[\s:(])"), "known_historical"),
    (re.compile(r"^(?:method|genetic)(?:$|[\s:(])"), "modeled_relational"),
)


def classify_aadr_date_method(raw_value: str) -> AadrDateMethodEvidence:
    """Classify a dating token without deciding chronology admissibility."""
    normalized_value = " ".join(raw_value.split()).casefold()
    family: DateMethodFamily = "unclassified"
    for pattern, candidate in _METHOD_FAMILIES:
        if pattern.match(normalized_value):
            family = candidate
            break
    return AadrDateMethodEvidence(
        raw_value=raw_value,
        normalized_value=normalized_value,
        family=family,
    )


__all__ = ["classify_aadr_date_method"]
