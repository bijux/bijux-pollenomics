"""Describe coordinate, identity, and source-position uncertainty."""

from __future__ import annotations

import re
from collections.abc import Sequence

from ..models import (
    _COORDINATE_SPREAD_FLAG_KM,
    _POSITION_NOTE_PATTERNS,
    _LakeSourcePoint,
)

__all__ = []


def _base_ambiguity_flags(
    points: Sequence[_LakeSourcePoint], coordinate_spread_km: float
) -> tuple[str, ...]:
    flags: set[str] = set()
    if len({source_point.cleaned_name for source_point in points}) > 1:
        flags.add("source_name_variants")
    if coordinate_spread_km >= _COORDINATE_SPREAD_FLAG_KM:
        flags.add("source_coordinate_spread")
    if any(source_point.position_note for source_point in points):
        flags.add("source_position_note")
    return tuple(sorted(flags))


def _build_lake_label(
    lake_name: str,
    *,
    latitude: float,
    longitude: float,
    duplicate_name_count: int,
    ambiguity_flags: tuple[str, ...],
) -> str:
    if duplicate_name_count > 1 or ambiguity_flags:
        return f"{lake_name} ({latitude:.6f}, {longitude:.6f})"
    return lake_name


def _build_ambiguity_note(
    *,
    duplicate_name_count: int,
    coordinate_spread_km: float,
    ambiguity_flags: tuple[str, ...],
    position_notes: tuple[str, ...],
    lake_name_status: str = "",
) -> str:
    parts: list[str] = []
    if "duplicate_sweden_name" in ambiguity_flags:
        parts.append(
            f"{duplicate_name_count} Sweden candidates share this cleaned lake name."
        )
    if "source_coordinate_spread" in ambiguity_flags:
        parts.append(
            f"Source coordinates span {coordinate_spread_km:.2f} km inside this candidate."
        )
    if "source_name_variants" in ambiguity_flags:
        parts.append(
            "Source records use more than one lake name form for this candidate."
        )
    if "non_official_registry_name" in ambiguity_flags and lake_name_status:
        parts.append(
            "Lake naming falls back to a non-register registry label "
            f"({lake_name_status})."
        )
    if "source_position_note" in ambiguity_flags and position_notes:
        parts.append(position_notes[0])
    return " ".join(parts)


def _normalize_note_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\r", " ").replace("\n", " ")).strip()


def _note_signals_position_uncertainty(note: str) -> bool:
    return any(pattern.search(note) for pattern in _POSITION_NOTE_PATTERNS)
