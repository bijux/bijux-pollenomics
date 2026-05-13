from __future__ import annotations

from dataclasses import dataclass

from .bp_time import (
    build_bp_interval_label,
    mean_bp_year_from_interval,
    normalize_bp_interval,
)

__all__ = [
    "TEMPORAL_COMPARABILITY_POSTURES",
    "TEMPORAL_WINDOW_ROWS",
    "TemporalSemantics",
    "build_temporal_semantics",
    "normalize_temporal_semantics_payload",
    "resolve_temporal_window",
    "temporal_semantics_has_numeric_interval",
]

TEMPORAL_COMPARABILITY_POSTURES = (
    "numeric_interval",
    "numeric_interval_with_caveat",
    "contextual_label_only",
    "mixed_interval_and_context",
    "unresolved",
)
TEMPORAL_WINDOW_ROWS = (
    ("recent_historical", "Recent and historical (0-1000 BP)", 0, 1000),
    ("late_holocene", "Late Holocene (1001-3000 BP)", 1001, 3000),
    ("mid_holocene", "Mid-Holocene (3001-6000 BP)", 3001, 6000),
    ("early_holocene_and_older", "Early Holocene and older (6001+ BP)", 6001, None),
    ("unresolved", "Unresolved time window", None, None),
)


@dataclass(frozen=True)
class TemporalSemantics:
    """Shared temporal contract carried across direct and contextual evidence layers."""

    source_family: str
    evidence_class: str
    precision_posture: str
    comparability_posture: str
    summary_label: str
    temporal_window_key: str
    temporal_window_label: str
    time_start_bp: int | None
    time_end_bp: int | None
    time_mean_bp: int | None
    duration_years: int | None
    comparison_note: str = ""
    provenance_path: str = ""
    provenance_locator: str = ""
    provenance_excerpt: str = ""
    original_labels: tuple[str, ...] = ()
    normalized_labels: tuple[str, ...] = ()
    uncertainty_notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "temporal-semantics.v1",
            "source_family": self.source_family,
            "evidence_class": self.evidence_class,
            "precision_posture": self.precision_posture,
            "comparability_posture": self.comparability_posture,
            "summary_label": self.summary_label,
            "temporal_window_key": self.temporal_window_key,
            "temporal_window_label": self.temporal_window_label,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "time_mean_bp": self.time_mean_bp,
            "duration_years": self.duration_years,
            "comparison_note": self.comparison_note,
            "provenance_path": self.provenance_path,
            "provenance_locator": self.provenance_locator,
            "provenance_excerpt": self.provenance_excerpt,
            "original_labels": list(self.original_labels),
            "normalized_labels": list(self.normalized_labels),
            "uncertainty_notes": list(self.uncertainty_notes),
        }


def build_temporal_semantics(
    *,
    source_family: str,
    evidence_class: str,
    precision_posture: str,
    comparability_posture: str,
    time_start_bp: int | None,
    time_end_bp: int | None,
    time_mean_bp: int | None = None,
    summary_label: str = "",
    comparison_note: str = "",
    provenance_path: str = "",
    provenance_locator: str = "",
    provenance_excerpt: str = "",
    original_labels: tuple[str, ...] = (),
    normalized_labels: tuple[str, ...] = (),
    uncertainty_notes: tuple[str, ...] = (),
) -> TemporalSemantics:
    """Build one normalized temporal semantics payload."""
    interval = normalize_bp_interval(time_start_bp, time_end_bp)
    resolved_mean = (
        time_mean_bp
        if time_mean_bp is not None
        else mean_bp_year_from_interval(interval)
    )
    duration_years = None
    if interval is not None:
        duration_years = max(0, interval[1] - interval[0])
    window_key, window_label = resolve_temporal_window(
        time_start_bp=interval[0] if interval is not None else None,
        time_end_bp=interval[1] if interval is not None else None,
        time_mean_bp=resolved_mean,
    )
    resolved_summary = summary_label.strip()
    if not resolved_summary:
        resolved_summary = build_bp_interval_label(
            interval[0] if interval is not None else None,
            interval[1] if interval is not None else None,
        )
    if not resolved_summary:
        resolved_summary = (
            "; ".join(label for label in original_labels if label)
            or "Unresolved time semantics"
        )
    return TemporalSemantics(
        source_family=source_family,
        evidence_class=evidence_class,
        precision_posture=precision_posture,
        comparability_posture=comparability_posture,
        summary_label=resolved_summary,
        temporal_window_key=window_key,
        temporal_window_label=window_label,
        time_start_bp=interval[0] if interval is not None else None,
        time_end_bp=interval[1] if interval is not None else None,
        time_mean_bp=resolved_mean,
        duration_years=duration_years,
        comparison_note=comparison_note.strip(),
        provenance_path=provenance_path.strip(),
        provenance_locator=provenance_locator.strip(),
        provenance_excerpt=provenance_excerpt.strip(),
        original_labels=_normalize_string_tuple(original_labels),
        normalized_labels=_normalize_string_tuple(normalized_labels),
        uncertainty_notes=_normalize_string_tuple(uncertainty_notes),
    )


def resolve_temporal_window(
    *,
    time_start_bp: int | None,
    time_end_bp: int | None,
    time_mean_bp: int | None,
) -> tuple[str, str]:
    """Assign one durable time window from a numeric BP interval or midpoint."""
    candidate = time_mean_bp
    if candidate is None:
        candidate = mean_bp_year_from_interval(
            normalize_bp_interval(time_start_bp, time_end_bp)
        )
    if candidate is None:
        return ("unresolved", "Unresolved time window")
    for key, label, minimum, maximum in TEMPORAL_WINDOW_ROWS:
        if minimum is None:
            continue
        if candidate < minimum:
            continue
        if maximum is not None and candidate > maximum:
            continue
        return (key, label)
    return ("unresolved", "Unresolved time window")


def temporal_semantics_has_numeric_interval(payload: dict[str, object] | None) -> bool:
    """Return whether one serialized temporal payload supports interval-based filtering."""
    if not isinstance(payload, dict):
        return False
    posture = str(payload.get("comparability_posture", "")).strip()
    if posture not in {
        "numeric_interval",
        "numeric_interval_with_caveat",
        "mixed_interval_and_context",
    }:
        return False
    return any(
        payload.get(key) is not None
        for key in ("time_start_bp", "time_end_bp", "time_mean_bp")
    )


def normalize_temporal_semantics_payload(value: object) -> dict[str, object]:
    """Normalize one temporal semantics payload recovered from JSON or GeoJSON."""
    if not isinstance(value, dict):
        return {}
    payload = {
        "schema_version": "temporal-semantics.v1",
        "source_family": str(value.get("source_family", "")).strip(),
        "evidence_class": str(value.get("evidence_class", "")).strip(),
        "precision_posture": str(value.get("precision_posture", "")).strip(),
        "comparability_posture": str(value.get("comparability_posture", "")).strip(),
        "summary_label": str(value.get("summary_label", "")).strip(),
        "temporal_window_key": str(value.get("temporal_window_key", "")).strip(),
        "temporal_window_label": str(value.get("temporal_window_label", "")).strip(),
        "time_start_bp": value.get("time_start_bp"),
        "time_end_bp": value.get("time_end_bp"),
        "time_mean_bp": value.get("time_mean_bp"),
        "duration_years": value.get("duration_years"),
        "comparison_note": str(value.get("comparison_note", "")).strip(),
        "provenance_path": str(value.get("provenance_path", "")).strip(),
        "provenance_locator": str(value.get("provenance_locator", "")).strip(),
        "provenance_excerpt": str(value.get("provenance_excerpt", "")).strip(),
        "original_labels": _normalize_string_list(value.get("original_labels")),
        "normalized_labels": _normalize_string_list(value.get("normalized_labels")),
        "uncertainty_notes": _normalize_string_list(value.get("uncertainty_notes")),
    }
    if not payload["temporal_window_key"] or not payload["temporal_window_label"]:
        payload["temporal_window_key"], payload["temporal_window_label"] = (
            resolve_temporal_window(
                time_start_bp=_as_optional_int(payload.get("time_start_bp")),
                time_end_bp=_as_optional_int(payload.get("time_end_bp")),
                time_mean_bp=_as_optional_int(payload.get("time_mean_bp")),
            )
        )
    return payload


def _normalize_string_tuple(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_normalize_string_list(values))


def _normalize_string_list(values: object) -> list[str]:
    if not isinstance(values, (list, tuple)):
        return []
    normalized: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _as_optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(round(float(text)))
    except ValueError:
        return None
