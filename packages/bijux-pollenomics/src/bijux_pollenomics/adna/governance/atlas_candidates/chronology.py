"""Chronology parsing and atlas-public precision policy."""

from __future__ import annotations

from typing import cast

from ....core.temporal_semantics import InvalidBpIntervalError, canonical_bp_interval
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


def _atlas_public_locality_chronology(payload: object) -> AdnaChronology:
    """Preserve valid display coverage without presenting it as a specimen date."""
    if not isinstance(payload, dict):
        raise TypeError("Locality chronology payload must be a dict")

    def text(key: str) -> str:
        value = payload.get(key, "")
        if value is None:
            return ""
        if not isinstance(value, str):
            raise TypeError(f"Locality chronology {key} must be text")
        return value

    def endpoint(key: str) -> int | None:
        value = payload.get(key)
        if value is None or value == "":
            return None
        if type(value) is not int:
            raise TypeError(f"Locality chronology {key} must be integer BP or null")
        return value

    start, end = endpoint("time_start_bp"), endpoint("time_end_bp")
    mean = endpoint("time_mean_bp")
    try:
        interval = canonical_bp_interval(start, end)
    except InvalidBpIntervalError:
        interval = None
    if interval is None:
        start = end = mean = None
    elif mean is not None and not (cast(int, start) <= mean <= cast(int, end)):
        mean = None
    return AdnaChronology(
        original_text=text("original_text"),
        time_start_bp=start,
        time_end_bp=end,
        time_mean_bp=mean,
        date_stddev_bp=text("date_stddev_bp"),
        source_mean_bp_text=text("source_mean_bp_text"),
        dating_basis="locality_sample_coverage",
        evidence_class="locality_sample_coverage_hull",
        precision_posture="display_coverage_only",
        refusal_reason_code=text("refusal_reason_code"),
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
