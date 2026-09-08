"""Chronology parsing and atlas-public precision policy."""

from __future__ import annotations

from typing import cast

from ...domain.models.chronology import AdnaChronology
from ...domain.models.vocabularies import (
    ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
    ADNA_CHRONOLOGY_PRECISION_POSTURES,
    ADNA_DATING_BASES,
)


def _parse_chronology(payload: object) -> AdnaChronology:
    if not isinstance(payload, dict):
        raise TypeError("Chronology payload must be a dict")
    return AdnaChronology(
        original_text=_optional_str(payload.get("original_text")) or "",
        time_start_bp=_optional_int(payload.get("time_start_bp")),
        time_end_bp=_optional_int(payload.get("time_end_bp")),
        time_mean_bp=_optional_int(payload.get("time_mean_bp")),
        date_stddev_bp=_optional_str(payload.get("date_stddev_bp")) or "",
        dating_basis=_optional_str(payload.get("dating_basis")) or "unknown",
        evidence_class=_optional_str(payload.get("evidence_class")) or "unresolved",
        precision_posture=(
            _optional_str(payload.get("precision_posture")) or "unresolved"
        ),
    )


def _atlas_public_chronology(chronology: AdnaChronology) -> AdnaChronology:
    temporal_semantics = chronology.as_temporal_semantics(source_family="animal_adna")
    if temporal_semantics["comparability_posture"] in {
        "numeric_interval",
        "numeric_interval_with_caveat",
    } and _atlas_chronology_supports_publication(chronology):
        time_start_bp = cast(int, temporal_semantics["time_start_bp"])
        time_end_bp = cast(int, temporal_semantics["time_end_bp"])
        time_mean_bp = chronology.time_mean_bp
        if time_mean_bp is not None and not (
            time_start_bp <= time_mean_bp <= time_end_bp
        ):
            time_mean_bp = None
        return AdnaChronology(
            original_text=chronology.original_text,
            time_start_bp=time_start_bp,
            time_end_bp=time_end_bp,
            time_mean_bp=time_mean_bp,
            date_stddev_bp=chronology.date_stddev_bp,
            dating_basis=chronology.dating_basis,
            evidence_class=chronology.evidence_class,
            precision_posture=chronology.precision_posture,
        )
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


def _atlas_chronology_supports_publication(chronology: AdnaChronology) -> bool:
    """Return whether chronology has enough source support for an atlas row."""
    if (
        not chronology.original_text.strip()
        or chronology.dating_basis not in ADNA_DATING_BASES
        or chronology.dating_basis in {"not_yet_curated", "unknown"}
        or chronology.evidence_class not in ADNA_CHRONOLOGY_EVIDENCE_CLASSES
        or chronology.evidence_class == "unresolved"
        or chronology.precision_posture not in ADNA_CHRONOLOGY_PRECISION_POSTURES
        or chronology.precision_posture == "unresolved"
    ):
        return False
    temporal_semantics = chronology.as_temporal_semantics(source_family="animal_adna")
    comparability_posture = temporal_semantics["comparability_posture"]
    if chronology.precision_posture in {
        "sample_precise_point",
        "sample_precise_interval",
    }:
        return comparability_posture == "numeric_interval"
    return comparability_posture in {
        "numeric_interval",
        "numeric_interval_with_caveat",
        "contextual_label_only",
    }


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
