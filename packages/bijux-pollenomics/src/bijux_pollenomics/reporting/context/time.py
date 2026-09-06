from __future__ import annotations

import math
from pathlib import Path

from ...core.bp_time import (
    build_bp_interval_label,
    midpoint_bp_year,
    parse_numeric_bp_year,
)
from ...core.geospatial.geojson import JsonObject, as_mapping
from ...core.temporal_semantics import (
    normalize_temporal_semantics_payload,
    resolve_temporal_window,
)

__all__ = [
    "extract_layer_identity",
    "feature_has_time",
    "feature_time_payload",
    "normalize_media_links",
    "parse_year_bp",
    "validate_feature_collection",
]


def parse_year_bp(value: object) -> int | None:
    """Parse one canonical nonnegative BP-year value from external metadata."""
    source_value = source_numeric_bp_value(value)
    if source_value is None or not math.isfinite(source_value) or source_value < 0:
        return None
    return parse_numeric_bp_year(source_value)


def source_numeric_bp_value(value: object) -> float | None:
    """Return an unrounded source number so signed values cannot round into zero."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except (OverflowError, ValueError):
        return None


def bp_refusal_reason(value: object) -> str:
    """Classify one populated source BP value against the canonical domain."""
    source_value = source_numeric_bp_value(value)
    if source_value is None or not math.isfinite(source_value):
        return "non_finite"
    return "negative_bp" if source_value < 0 else ""


def feature_time_payload(properties: JsonObject) -> dict[str, object]:
    """Normalize temporal properties from external feature metadata."""
    raw_start_bp = properties.get("time_start_bp")
    raw_end_bp = properties.get("time_end_bp")
    raw_mean_bp = properties.get("time_mean_bp")
    interval_declared = (
        "time_start_bp" in properties or "time_end_bp" in properties
    ) and (raw_start_bp is not None or raw_end_bp is not None)
    mean_declared = "time_mean_bp" in properties and raw_mean_bp is not None
    time_start_bp = parse_year_bp(raw_start_bp)
    time_end_bp = parse_year_bp(raw_end_bp)
    time_mean_bp = parse_year_bp(raw_mean_bp)
    refusal_reason = ""
    mean_issue = ""
    if interval_declared and (
        time_start_bp is None or time_end_bp is None or time_start_bp > time_end_bp
    ):
        endpoint_reasons = {
            bp_refusal_reason(value)
            for value in (raw_start_bp, raw_end_bp)
            if value is not None
        }
        if "negative_bp" in endpoint_reasons:
            refusal_reason = "negative_bp"
        elif "non_finite" in endpoint_reasons:
            refusal_reason = "non_finite"
        elif time_start_bp is None or time_end_bp is None:
            refusal_reason = "partial_interval"
        else:
            refusal_reason = "reversed_interval"
        time_start_bp = None
        time_end_bp = None
        time_mean_bp = None
    elif time_start_bp is not None and time_end_bp is not None:
        if not mean_declared:
            time_mean_bp = midpoint_bp_year(time_start_bp, time_end_bp)
        elif time_mean_bp is None:
            mean_issue = bp_refusal_reason(raw_mean_bp)
        elif not time_start_bp <= time_mean_bp <= time_end_bp:
            time_mean_bp = None
            mean_issue = "mean_outside_interval"
    elif mean_declared and time_mean_bp is None:
        refusal_reason = bp_refusal_reason(raw_mean_bp)
    time_label = str(properties.get("time_label", "")).strip()
    if not time_label and time_start_bp is not None and time_end_bp is not None:
        time_label = build_bp_interval_label(time_start_bp, time_end_bp)
    temporal_semantics = normalize_temporal_semantics_payload(
        properties.get("temporal_semantics")
    )
    if temporal_semantics:
        temporal_semantics.update(
            {
                "time_start_bp": time_start_bp,
                "time_end_bp": time_end_bp,
                "time_mean_bp": time_mean_bp,
                "duration_years": (
                    time_end_bp - time_start_bp
                    if time_start_bp is not None and time_end_bp is not None
                    else None
                ),
            }
        )
    if refusal_reason or mean_issue:
        existing_notes = temporal_semantics.get("uncertainty_notes", [])
        uncertainty_notes = (
            list(existing_notes) if isinstance(existing_notes, list) else []
        )
        reason = refusal_reason or mean_issue
        if reason not in uncertainty_notes:
            uncertainty_notes.append(reason)
        temporal_semantics["uncertainty_notes"] = uncertainty_notes
    if refusal_reason:
        temporal_semantics.update(
            {
                "comparability_posture": "refused",
                "refusal_reason_code": refusal_reason,
                "temporal_window_key": "unresolved",
                "temporal_window_label": "Unresolved time window",
            }
        )
    if refusal_reason:
        temporal_window_key = "unresolved"
        temporal_window_label = "Unresolved time window"
    else:
        temporal_window_key, temporal_window_label = resolve_temporal_window(
            time_start_bp=time_start_bp,
            time_end_bp=time_end_bp,
            time_mean_bp=time_mean_bp,
        )
        if temporal_semantics:
            temporal_semantics["temporal_window_key"] = temporal_window_key
            temporal_semantics["temporal_window_label"] = temporal_window_label
    return {
        "time_start_bp": time_start_bp,
        "time_end_bp": time_end_bp,
        "time_mean_bp": time_mean_bp,
        "time_year_bp": time_mean_bp,
        "time_label": time_label,
        "temporal_semantics": temporal_semantics,
        "temporal_window_key": temporal_window_key,
        "temporal_window_label": temporal_window_label,
        "temporal_comparability_posture": str(
            temporal_semantics.get("comparability_posture", "")
        ).strip(),
        "temporal_comparison_note": str(
            temporal_semantics.get("comparison_note", "")
        ).strip(),
    }


def feature_has_time(feature: JsonObject) -> bool:
    """Return whether a feature can participate in numeric timeline filtering."""
    payload = feature_time_payload(feature)
    return any(
        payload.get(key) is not None
        for key in (
            "time_start_bp",
            "time_end_bp",
            "time_mean_bp",
        )
    )


def validate_feature_collection(
    geojson: JsonObject,
    *,
    source_path: Path | None,
) -> list[JsonObject]:
    """Validate a GeoJSON feature collection and return its feature list."""
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    if geojson.get("type") != "FeatureCollection":
        raise ValueError(f"{source_label} must be a GeoJSON FeatureCollection")
    raw_features = geojson.get("features", [])
    if not isinstance(raw_features, list) or not raw_features:
        raise ValueError(f"{source_label} did not contain any features")
    normalized_features: list[JsonObject] = [
        feature for feature in raw_features if isinstance(feature, dict)
    ]
    if len(normalized_features) != len(raw_features):
        raise ValueError(f"{source_label} contains non-object features")
    return normalized_features


def extract_layer_identity(
    raw_features: list[JsonObject],
    *,
    source_path: Path | None,
) -> tuple[JsonObject, str, str]:
    """Extract and validate shared layer metadata from the first feature."""
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    sample_properties = as_mapping(raw_features[0].get("properties"))
    if sample_properties is None:
        raise ValueError(f"{source_label} properties must be an object")

    layer_key = str(sample_properties.get("layer_key", "")).strip()
    layer_label = str(sample_properties.get("layer_label", "")).strip()
    if not layer_key:
        raise ValueError(f"{source_label} is missing a non-empty layer_key property")
    if not layer_label:
        raise ValueError(f"{source_label} is missing a non-empty layer_label property")
    return sample_properties, layer_key, layer_label


def normalize_media_links(value: object) -> list[dict[str, str]]:
    """Normalize map popup media links into a stable list structure."""
    if not isinstance(value, list):
        return []
    links: list[dict[str, str]] = []
    for raw_link in value:
        if not isinstance(raw_link, dict):
            continue
        label = str(raw_link.get("label", "")).strip()
        url = str(raw_link.get("url", "")).strip()
        kind = str(raw_link.get("kind", "")).strip().lower() or "link"
        if not label or not url:
            continue
        links.append({"label": label, "url": url, "kind": kind})
    return links
