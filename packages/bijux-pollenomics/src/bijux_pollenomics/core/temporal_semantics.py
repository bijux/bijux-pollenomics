from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from typing import cast

from .bp_time import (
    build_bp_interval_label,
    mean_bp_year_from_interval,
    normalize_bp_interval,
)
from .chronology.source_metadata import _json_metadata_copy, _source_metadata_copy

__all__ = [
    "TEMPORAL_COMPARABILITY_POSTURES",
    "TEMPORAL_WINDOW_ROWS",
    "BpInterval",
    "BpIntervalAdmission",
    "DirectionalLagBounds",
    "InvalidBpIntervalError",
    "TemporalSemantics",
    "admit_bp_interval",
    "build_temporal_semantics",
    "canonical_bp_interval",
    "closed_bp_intervals_overlap",
    "directional_lag_bounds",
    "normalize_temporal_semantics_payload",
    "resolve_temporal_window",
    "temporal_semantics_has_numeric_interval",
]

_MAX_EXACT_BP_INTEGER = 2**53 - 1

TEMPORAL_COMPARABILITY_POSTURES = (
    "numeric_interval",
    "numeric_interval_with_caveat",
    "contextual_label_only",
    "mixed_interval_and_context",
    "unresolved",
    "refused",
)
TEMPORAL_WINDOW_ROWS = (
    ("recent_historical", "Recent and historical (0-1000 BP)", 0, 1000),
    ("late_holocene", "Late Holocene (1001-3000 BP)", 1001, 3000),
    ("mid_holocene", "Mid-Holocene (3001-6000 BP)", 3001, 6000),
    ("early_holocene_and_older", "Early Holocene and older (6001+ BP)", 6001, None),
    ("unresolved", "Unresolved time window", None, None),
)


class InvalidBpIntervalError(ValueError):
    """Raised when a claimed canonical BP interval violates its contract."""


@dataclass(frozen=True)
class BpInterval:
    """One closed calendar-BP interval ordered from younger to older."""

    younger_bp: float
    older_bp: float

    def __post_init__(self) -> None:
        younger = _canonical_bp_endpoint(self.younger_bp, field_name="younger_bp")
        older = _canonical_bp_endpoint(self.older_bp, field_name="older_bp")
        if younger > older:
            raise InvalidBpIntervalError(
                "younger_bp must be less than or equal to older_bp"
            )
        object.__setattr__(self, "younger_bp", younger)
        object.__setattr__(self, "older_bp", older)


@dataclass(frozen=True)
class BpIntervalAdmission:
    """Reason-coded admission to the integer BP-year projection."""

    interval: BpInterval | None
    refusal_reason_code: str = ""

    def __post_init__(self) -> None:
        if self.interval is None:
            return
        endpoints = (self.interval.younger_bp, self.interval.older_bp)
        reason = (
            "unsafe_integer_bp"
            if any(value > _MAX_EXACT_BP_INTEGER for value in endpoints)
            else "fractional_bp"
            if any(not value.is_integer() for value in endpoints)
            else ""
        )
        if reason:
            object.__setattr__(self, "interval", None)
            if not self.refusal_reason_code:
                object.__setattr__(self, "refusal_reason_code", reason)

    @property
    def admitted(self) -> bool:
        return self.interval is not None and not self.refusal_reason_code

    def as_tuple(self) -> tuple[int, int] | None:
        if self.interval is None or self.refusal_reason_code:
            return None
        return (int(self.interval.younger_bp), int(self.interval.older_bp))


@dataclass(frozen=True)
class DirectionalLagBounds:
    """Supported BP lag range for an asserted source-to-target orientation."""

    minimum_lag_years: float
    maximum_lag_years: float


def canonical_bp_interval(
    younger_bp: float | None,
    older_bp: float | None,
) -> BpInterval | None:
    """Validate canonical ``[younger_bp, older_bp]`` input without reordering it."""
    if younger_bp is None and older_bp is None:
        return None
    if younger_bp is None or older_bp is None:
        raise InvalidBpIntervalError(
            "younger_bp and older_bp must either both be present or both be null"
        )
    return BpInterval(younger_bp=younger_bp, older_bp=older_bp)


def admit_bp_interval(
    younger_bp: object,
    older_bp: object,
) -> BpIntervalAdmission:
    """Admit integer-year source bounds without rounding, reordering or lost refusal."""
    if younger_bp is None and older_bp is None:
        return BpIntervalAdmission(interval=None)
    if younger_bp is None or older_bp is None:
        return BpIntervalAdmission(
            interval=None, refusal_reason_code="partial_interval"
        )
    reasons = (
        _bp_value_refusal_reason(younger_bp),
        _bp_value_refusal_reason(older_bp),
    )
    for reason in ("non_finite", "negative_bp", "unsafe_integer_bp"):
        if reason in reasons:
            return BpIntervalAdmission(interval=None, refusal_reason_code=reason)
    assert isinstance(younger_bp, (int, float))
    assert isinstance(older_bp, (int, float))
    if younger_bp > older_bp:
        return BpIntervalAdmission(
            interval=None, refusal_reason_code="reversed_interval"
        )
    if "fractional_bp" in reasons:
        return BpIntervalAdmission(interval=None, refusal_reason_code="fractional_bp")
    return BpIntervalAdmission(interval=BpInterval(younger_bp, older_bp))


def directional_lag_bounds(
    source: BpInterval | None,
    target: BpInterval | None,
) -> DirectionalLagBounds | None:
    """Return all supported lags for source (older) to target (younger)."""
    if source is None or target is None:
        return None
    return DirectionalLagBounds(
        minimum_lag_years=source.younger_bp - target.older_bp,
        maximum_lag_years=source.older_bp - target.younger_bp,
    )


def closed_bp_intervals_overlap(left: BpInterval, right: BpInterval) -> bool:
    """Return closed interval algebra; source comparability is a separate admission."""
    # Relations consume interval values. Import here to preserve that dependency
    # direction while keeping the established value and boolean API owners.
    from .chronology.relations import TemporalRelationKind, bp_interval_relation_kind

    return bp_interval_relation_kind(left, right) is TemporalRelationKind.OVERLAPPING


def _canonical_bp_endpoint(value: object, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidBpIntervalError(f"{field_name} must be a finite number")
    try:
        endpoint = float(value)
    except OverflowError as error:
        raise InvalidBpIntervalError(f"{field_name} must be finite") from error
    if isinstance(value, int) and endpoint != value:
        raise InvalidBpIntervalError(f"{field_name} must be exactly representable")
    if not isfinite(endpoint):
        raise InvalidBpIntervalError(f"{field_name} must be finite")
    if endpoint < 0:
        raise InvalidBpIntervalError(f"{field_name} must be non-negative")
    return endpoint


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
    refusal_reason_code: str = ""
    provenance_path: str = ""
    provenance_locator: str = ""
    provenance_excerpt: str = ""
    original_labels: tuple[str, ...] = ()
    normalized_labels: tuple[str, ...] = ()
    uncertainty_notes: tuple[str, ...] = ()
    source_metadata: Mapping[str, object] | None = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
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
            "refusal_reason_code": self.refusal_reason_code,
            "provenance_path": self.provenance_path,
            "provenance_locator": self.provenance_locator,
            "provenance_excerpt": self.provenance_excerpt,
            "original_labels": list(self.original_labels),
            "normalized_labels": list(self.normalized_labels),
            "uncertainty_notes": list(self.uncertainty_notes),
        }
        payload.update(_source_metadata_copy(self.source_metadata, reserved=payload))
        return payload


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
    refusal_reason_code: str = "",
    provenance_path: str = "",
    provenance_locator: str = "",
    provenance_excerpt: str = "",
    original_labels: tuple[str, ...] = (),
    normalized_labels: tuple[str, ...] = (),
    uncertainty_notes: tuple[str, ...] = (),
    source_metadata: Mapping[str, object] | None = None,
) -> TemporalSemantics:
    """Build one normalized temporal semantics payload."""
    admission = admit_bp_interval(time_start_bp, time_end_bp)
    interval = admission.as_tuple()
    resolved_refusal = refusal_reason_code.strip() or admission.refusal_reason_code
    resolved_posture = "refused" if resolved_refusal else comparability_posture
    resolved_mean = None
    if not resolved_refusal:
        if time_mean_bp is None:
            resolved_mean = mean_bp_year_from_interval(interval)
        else:
            mean_refusal = _bp_value_refusal_reason(time_mean_bp)
            if mean_refusal:
                resolved_refusal = mean_refusal
                resolved_posture = "refused"
                interval = None
            else:
                resolved_mean = int(time_mean_bp)
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
        comparability_posture=resolved_posture,
        summary_label=resolved_summary,
        temporal_window_key=window_key,
        temporal_window_label=window_label,
        time_start_bp=interval[0] if interval is not None else None,
        time_end_bp=interval[1] if interval is not None else None,
        time_mean_bp=resolved_mean,
        duration_years=duration_years,
        comparison_note=comparison_note.strip(),
        refusal_reason_code=resolved_refusal,
        provenance_path=provenance_path.strip(),
        provenance_locator=provenance_locator.strip(),
        provenance_excerpt=provenance_excerpt.strip(),
        original_labels=_normalize_string_tuple(original_labels),
        normalized_labels=_normalize_string_tuple(normalized_labels),
        uncertainty_notes=_normalize_string_tuple(uncertainty_notes),
        source_metadata=source_metadata,
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
    if payload.get("refusal_reason_code"):
        return False
    if (
        payload.get("schema_version", "temporal-semantics.v1")
        != "temporal-semantics.v1"
    ):
        return False
    admission = admit_bp_interval(
        payload.get("time_start_bp"), payload.get("time_end_bp")
    )
    if admission.refusal_reason_code:
        return False
    if payload.get("time_mean_bp") is not None and _bp_value_refusal_reason(
        payload["time_mean_bp"]
    ):
        return False
    if admission.admitted:
        return True
    return _as_optional_int(payload.get("time_mean_bp")) is not None


def normalize_temporal_semantics_payload(value: object) -> dict[str, object]:
    """Normalize one temporal semantics payload recovered from JSON or GeoJSON."""
    if not isinstance(value, dict):
        return {}
    payload: dict[str, object] = {
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
        "refusal_reason_code": str(value.get("refusal_reason_code", "")).strip(),
        "provenance_path": str(value.get("provenance_path", "")).strip(),
        "provenance_locator": str(value.get("provenance_locator", "")).strip(),
        "provenance_excerpt": str(value.get("provenance_excerpt", "")).strip(),
        "original_labels": _normalize_string_list(value.get("original_labels")),
        "normalized_labels": _normalize_string_list(value.get("normalized_labels")),
        "uncertainty_notes": _normalize_string_list(value.get("uncertainty_notes")),
    }
    extensions = {key: item for key, item in value.items() if key not in payload}
    payload.update(_source_metadata_copy(extensions, reserved=payload))
    if value.get("schema_version", "temporal-semantics.v1") != "temporal-semantics.v1":
        payload["schema_version"] = _json_metadata_copy(
            value["schema_version"], seen=set()
        )
        payload["comparability_posture"] = "refused"
        payload["refusal_reason_code"] = "unsupported_temporal_semantics_schema"
        payload["time_start_bp"] = None
        payload["time_end_bp"] = None
        payload["time_mean_bp"] = None
        payload["duration_years"] = None
        payload["temporal_window_key"] = "unresolved"
        payload["temporal_window_label"] = "Unresolved time window"
        notes = cast(list[str], payload["uncertainty_notes"])
        if "unsupported_temporal_semantics_schema" not in notes:
            notes.append("unsupported_temporal_semantics_schema")
        return payload
    admission = admit_bp_interval(
        payload.get("time_start_bp"), payload.get("time_end_bp")
    )
    interval = admission.as_tuple()
    mean = _as_optional_int(payload.get("time_mean_bp"))
    if (
        interval is not None
        and mean is not None
        and not interval[0] <= mean <= interval[1]
    ):
        mean = None
    interval_refusal = admission.refusal_reason_code
    if (
        not interval_refusal
        and payload.get("time_mean_bp") is not None
        and _bp_value_refusal_reason(payload["time_mean_bp"])
    ):
        interval_refusal = _bp_value_refusal_reason(payload["time_mean_bp"])
    if interval_refusal:
        payload["comparability_posture"] = "refused"
        payload["refusal_reason_code"] = interval_refusal
        notes = cast(list[str], payload["uncertainty_notes"])
        if interval_refusal not in notes:
            notes.append(interval_refusal)
        interval = None
        mean = None
    elif payload.get("time_mean_bp") is not None and mean is None and interval is None:
        payload["comparability_posture"] = "refused"
        payload["refusal_reason_code"] = _bp_value_refusal_reason(
            payload.get("time_mean_bp")
        )
    normalized_start = interval[0] if interval is not None else None
    normalized_end = interval[1] if interval is not None else None
    payload["time_start_bp"] = normalized_start
    payload["time_end_bp"] = normalized_end
    payload["time_mean_bp"] = mean
    payload["duration_years"] = (
        interval[1] - interval[0] if interval is not None else None
    )
    payload["temporal_window_key"], payload["temporal_window_label"] = (
        resolve_temporal_window(
            time_start_bp=normalized_start,
            time_end_bp=normalized_end,
            time_mean_bp=mean,
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
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if _bp_value_refusal_reason(value):
        return None
    return int(value)


def _bp_value_refusal_reason(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "non_finite"
    if isinstance(value, float) and not isfinite(value):
        return "non_finite"
    if value < 0:
        return "negative_bp"
    if value > _MAX_EXACT_BP_INTEGER:
        return "unsafe_integer_bp"
    if isinstance(value, float) and not value.is_integer():
        return "fractional_bp"
    return ""
