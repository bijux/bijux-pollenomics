from __future__ import annotations

from pathlib import Path

from ...core.bp_time import (
    build_bp_interval_label,
    midpoint_bp_year,
    parse_numeric_bp_year,
)

__all__ = [
    "extract_layer_identity",
    "feature_has_time",
    "feature_time_payload",
    "normalize_media_links",
    "parse_year_bp",
    "validate_feature_collection",
]


def parse_year_bp(value: str) -> int | None:
    """Parse a numeric BP-year value from external date text."""
    return parse_numeric_bp_year(value)


def feature_time_payload(properties: dict[str, object]) -> dict[str, object]:
    """Normalize temporal properties from external feature metadata."""
    time_start_bp = parse_numeric_bp_year(properties.get("time_start_bp"))
    time_end_bp = parse_numeric_bp_year(properties.get("time_end_bp"))
    time_mean_bp = parse_numeric_bp_year(properties.get("time_mean_bp"))
    if time_mean_bp is None and time_start_bp is not None and time_end_bp is not None:
        time_mean_bp = midpoint_bp_year(time_start_bp, time_end_bp)
    time_label = str(properties.get("time_label", "")).strip()
    if not time_label and time_start_bp is not None and time_end_bp is not None:
        time_label = build_bp_interval_label(time_start_bp, time_end_bp)
    return {
        "time_start_bp": time_start_bp,
        "time_end_bp": time_end_bp,
        "time_mean_bp": time_mean_bp,
        "time_year_bp": time_mean_bp,
        "time_label": time_label,
    }


def feature_has_time(feature: dict[str, object]) -> bool:
    """Return whether a point or polygon feature carries temporal metadata."""
    payload = feature_time_payload(feature)
    return any(
        payload.get(key) not in (None, "")
        for key in ("time_start_bp", "time_end_bp", "time_mean_bp", "time_label")
    )


def validate_feature_collection(
    geojson: dict[str, object],
    *,
    source_path: Path | None,
) -> list[dict[str, object]]:
    """Validate a GeoJSON feature collection and return its feature list."""
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    if geojson.get("type") != "FeatureCollection":
        raise ValueError(f"{source_label} must be a GeoJSON FeatureCollection")
    raw_features = geojson.get("features", [])
    if not isinstance(raw_features, list) or not raw_features:
        raise ValueError(f"{source_label} did not contain any features")
    normalized_features = [
        feature for feature in raw_features if isinstance(feature, dict)
    ]
    if len(normalized_features) != len(raw_features):
        raise ValueError(f"{source_label} contains non-object features")
    return normalized_features


def extract_layer_identity(
    raw_features: list[dict[str, object]],
    *,
    source_path: Path | None,
) -> tuple[dict[str, object], str, str]:
    """Extract and validate shared layer metadata from the first feature."""
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    sample_properties = raw_features[0].get("properties", {})
    if not isinstance(sample_properties, dict):
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
