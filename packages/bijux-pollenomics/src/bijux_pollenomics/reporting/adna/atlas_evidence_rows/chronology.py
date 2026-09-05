"""Chronology parsing and atlas-public precision policy."""

from __future__ import annotations

from typing import cast

from ....adna import AdnaChronology


def _parse_chronology(payload: object) -> AdnaChronology:
    if not isinstance(payload, dict):
        raise TypeError("Chronology payload must be a dict")
    return AdnaChronology(
        original_text=str(payload.get("original_text", "")),
        time_start_bp=_optional_int(payload.get("time_start_bp")),
        time_end_bp=_optional_int(payload.get("time_end_bp")),
        time_mean_bp=_optional_int(payload.get("time_mean_bp")),
        date_stddev_bp=str(payload.get("date_stddev_bp", "")),
        dating_basis=str(payload.get("dating_basis", "unknown")),
        evidence_class=str(payload.get("evidence_class", "unresolved")),
        precision_posture=str(payload.get("precision_posture", "unresolved")),
    )


def _atlas_public_chronology(chronology: AdnaChronology) -> AdnaChronology:
    temporal_semantics = chronology.as_temporal_semantics(source_family="animal_adna")
    if temporal_semantics["comparability_posture"] in {
        "numeric_interval",
        "numeric_interval_with_caveat",
    }:
        return chronology
    return AdnaChronology(
        original_text=chronology.original_text,
        time_start_bp=None,
        time_end_bp=None,
        time_mean_bp=None,
        date_stddev_bp=chronology.date_stddev_bp,
        dating_basis=chronology.dating_basis,
        evidence_class=chronology.evidence_class,
        precision_posture=chronology.precision_posture,
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(cast(str, value))


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(cast(str, value))
