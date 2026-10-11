"""Canonical Python admission for map-feature BP chronology."""

from __future__ import annotations

from collections.abc import Mapping
import math

from ...core.calendar_support import SIGNED_CALENDAR_PROFILE, SignedCalendarSupport


def feature_temporal_admission(
    feature: Mapping[str, object],
    *,
    temporal_profile: str | None = None,
) -> tuple[str, tuple[float, float] | None]:
    """Classify numeric, contextual, refused, and absent feature chronology."""
    calendar_profile_metadata(temporal_profile)
    if temporal_profile is not None:
        try:
            return ("admitted", signed_feature_interval(feature))
        except ValueError:
            return ("refused", None)
    if "source_calendar_support" in feature or "declared_calendar_support" in feature:
        return ("refused", None)
    temporal_semantics = feature.get("temporal_semantics")
    posture = ""
    if isinstance(temporal_semantics, Mapping):
        posture = str(temporal_semantics.get("comparability_posture", "")).strip()
        refusal_reason = str(temporal_semantics.get("refusal_reason_code", "")).strip()
        if posture == "refused" or refusal_reason:
            return ("refused", None)
    interval: tuple[float, float] | None = None
    declaration_status = "absent"
    if "time_start_bp" in feature or "time_end_bp" in feature:
        raw_start = feature.get("time_start_bp")
        raw_end = feature.get("time_end_bp")
        if raw_start is not None or raw_end is not None:
            declaration_status = "refused"
            start = finite_number(raw_start)
            end = finite_number(raw_end)
            if start is not None and end is not None and start <= end:
                interval = (start, end)
                declaration_status = "admitted"
    if declaration_status == "absent":
        for key in ("time_mean_bp", "time_year_bp"):
            if key not in feature or feature.get(key) is None:
                continue
            point = finite_number(feature.get(key))
            if point is None:
                return ("refused", None)
            interval = (point, point)
            declaration_status = "admitted"
            break
    if declaration_status == "refused":
        return ("refused", None)
    if declaration_status == "admitted":
        if posture and posture not in {
            "numeric_interval",
            "numeric_interval_with_caveat",
            "mixed_interval_and_context",
        }:
            return ("contextual", None)
        return ("admitted", interval)
    if isinstance(temporal_semantics, Mapping) and temporal_semantics:
        if posture in {
            "numeric_interval",
            "numeric_interval_with_caveat",
            "mixed_interval_and_context",
        }:
            return ("refused", None)
        return ("contextual", None)
    return ("absent", None)


def feature_interval(
    feature: Mapping[str, object], *, temporal_profile: str | None = None
) -> tuple[float, float] | None:
    """Return an admitted nonnegative point or interval age for a feature."""
    status, interval = feature_temporal_admission(
        feature, temporal_profile=temporal_profile
    )
    return interval if status == "admitted" else None


def finite_number(value: object) -> float | None:
    """Normalize a nonnegative finite scalar without treating booleans as numbers."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value) if isinstance(value, (int, float, str)) else math.nan
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def calendar_profile_metadata(profile: str | None) -> dict[str, str]:
    """Validate explicit caller authorization; never infer it from numeric signs."""
    if profile is None:
        return {}
    if not isinstance(profile, str) or profile != SIGNED_CALENDAR_PROFILE:
        raise ValueError("Unsupported map calendar profile")
    return {"temporal_profile": profile, "temporal_axis": "BP1950"}


def read_calendar_profile(payload: Mapping[str, object]) -> str | None:
    """Read the exact optional envelope discriminator without enabling a legacy call."""
    if "temporal_profile" not in payload and "temporal_axis" not in payload:
        return None
    if (
        payload.get("temporal_profile") != SIGNED_CALENDAR_PROFILE
        or payload.get("temporal_axis") != "BP1950"
    ):
        raise ValueError("Map calendar profile and axis disagree")
    return SIGNED_CALENDAR_PROFILE


def signed_support_pair(
    value: Mapping[str, object],
) -> tuple[SignedCalendarSupport, SignedCalendarSupport]:
    """Admit only closed source support inside its declared stationary envelope."""
    source = SignedCalendarSupport.from_dict(value.get("source_calendar_support"))
    declared = SignedCalendarSupport.from_dict(value.get("declared_calendar_support"))
    if (
        source.support_kind != "closed_age_support"
        or declared.support_kind != "declared_stationarity_envelope"
    ):
        raise ValueError("Signed map requires closed age and stationarity supports")
    if not declared.contains(source.younger_bp) or not declared.contains(
        source.older_bp
    ):
        raise ValueError("Signed source support is outside its declared envelope")
    return source, declared


def support_matches(support: SignedCalendarSupport, raw: object) -> bool:
    """Join strict browser-domain numbers by value, retaining source bytes separately."""
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        return False
    try:
        candidate = SignedCalendarSupport(
            raw[0], raw[1], support_kind=support.support_kind
        )
    except ValueError:
        return False
    return candidate == support


def signed_feature_interval(feature: Mapping[str, object]) -> tuple[float, float]:
    """Read a typed synthetic anchor after its caller validates the complete view."""
    if "temporal_semantics" in feature:
        raise ValueError("Signed feature cannot mix legacy temporal semantics")
    source, declared = signed_support_pair(feature)
    raw_source = feature.get("source_age_support_bp")
    if (
        feature.get("data_kind") != "synthetic"
        or feature.get("evidence_role") != "model_output"
        or feature.get("scientific_acceptance") != "not_evaluated"
        or feature.get("age_type") != "calendar_bp"
        or not isinstance(raw_source, list)
        or len(raw_source) != 1
        or not support_matches(source, raw_source[0])
        or not support_matches(
            declared, (feature.get("time_start_bp"), feature.get("time_end_bp"))
        )
    ):
        raise ValueError("Signed map feature metadata contradicts its support")
    return declared.younger_bp, declared.older_bp


__all__ = [
    "calendar_profile_metadata",
    "read_calendar_profile",
    "signed_support_pair",
    "support_matches",
    "feature_interval",
    "feature_temporal_admission",
    "finite_number",
]
