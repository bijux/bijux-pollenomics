from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ...core.bp_time import (
    build_bp_interval_label,
    midpoint_bp_year,
)
from ...core.geospatial.geojson import JsonObject, as_mapping
from ...core.temporal_semantics import (
    normalize_temporal_semantics_payload,
    resolve_temporal_window,
)
from ..map_document.adna_exports import (
    NUMERIC_POSTURES,
    exported_record_semantics,
    is_public_chronology_export,
    validate_public_geojson_schemas,
)
from ..map_document.temporal_admission import feature_temporal_admission

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
    if bp_refusal_reason(value) or source_value is None:
        return None
    return int(source_value)


def source_numeric_bp_value(value: object) -> Decimal | None:
    """Read exact source values before integer projection, including explicit text intake."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    try:
        return Decimal.from_float(value) if isinstance(value, float) else Decimal(value)
    except (InvalidOperation, OverflowError, ValueError):
        return None


def bp_refusal_reason(value: object) -> str:
    """Classify populated source values before any lossy numeric conversion."""
    source_value = source_numeric_bp_value(value)
    if source_value is None or not source_value.is_finite():
        return "non_finite"
    if source_value < 0:
        return "negative_bp"
    if source_value > 2**53 - 1:
        return "unsafe_integer_bp"
    return "" if source_value == source_value.to_integral_value() else "fractional_bp"


def feature_time_payload(properties: JsonObject) -> dict[str, object]:
    """Normalize temporal metadata, preserving absent versus declared semantics.

    Spatial-only source input omits ``temporal_semantics``. Consumers must use
    optional access: an explicit empty declaration is contextual rather than
    absent, and an explicit refusal must remain refused.
    """
    if (
        "source_calendar_support" in properties
        or "declared_calendar_support" in properties
        or "sample_chronologies" in properties
        or "sample_chronology" in properties
        or is_public_chronology_export(properties)
        or (
            "schema_version" in properties
            and not isinstance(properties["schema_version"], str)
        )
    ):
        return _public_export_time_payload(properties)
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
        elif "unsafe_integer_bp" in endpoint_reasons:
            refusal_reason = "unsafe_integer_bp"
        elif "fractional_bp" in endpoint_reasons:
            refusal_reason = "fractional_bp"
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
    if "temporal_semantics" not in properties and (interval_declared or mean_declared):
        temporal_semantics = {
            "schema_version": "temporal-semantics.v1",
            "comparability_posture": "contextual_label_only",
            "refusal_reason_code": "",
            "comparison_note": "Numeric source fields have no declared comparison posture.",
        }
    raw_semantics = properties.get("temporal_semantics")
    if "temporal_semantics" in properties and (
        not isinstance(raw_semantics, dict)
        or any(
            key in raw_semantics and not isinstance(raw_semantics[key], str)
            for key in (
                "schema_version",
                "comparability_posture",
                "refusal_reason_code",
            )
        )
    ):
        temporal_semantics = {
            "comparability_posture": "refused",
            "refusal_reason_code": "malformed_temporal_semantics",
        }
    if temporal_semantics:
        posture = temporal_semantics.get("comparability_posture")
        semantics_refusal = temporal_semantics.get("refusal_reason_code")
        if semantics_refusal or posture not in {
            "numeric_interval",
            "numeric_interval_with_caveat",
            "mixed_interval_and_context",
        }:
            time_start_bp = None
            time_end_bp = None
            time_mean_bp = None
            if semantics_refusal:
                refusal_reason = str(semantics_refusal)
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
    result: dict[str, object] = {
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
    if temporal_semantics or "temporal_semantics" in properties:
        result["source_record"] = deepcopy(dict(properties))
    if "temporal_semantics" not in properties and not temporal_semantics:
        result.pop("temporal_semantics")
    return result


def feature_has_time(feature: JsonObject) -> bool:
    """Return whether a feature can participate in numeric timeline filtering."""
    payload = feature_time_payload(feature)
    return feature_temporal_admission(payload)[0] == "admitted"


def _public_export_time_payload(properties: JsonObject) -> dict[str, object]:
    """Keep source assertions separately from the qualified numeric map view."""
    semantics = exported_record_semantics(properties)
    if "schema_version" in properties and not isinstance(
        properties["schema_version"], str
    ):
        semantics = {
            "comparability_posture": "refused",
            "refusal_reason_code": "malformed_record_schema",
        }
    if (
        "source_calendar_support" in properties
        or "declared_calendar_support" in properties
    ):
        semantics = {
            "comparability_posture": "refused",
            "refusal_reason_code": "signed_support_requires_authorized_profile",
        }
    supplied = properties.get("temporal_semantics")
    if "temporal_semantics" in properties:
        normalized = normalize_temporal_semantics_payload(supplied)
        if not isinstance(supplied, dict) or any(
            key in supplied and not isinstance(supplied[key], str)
            for key in (
                "schema_version",
                "comparability_posture",
                "refusal_reason_code",
            )
        ):
            semantics = {
                "comparability_posture": "refused",
                "refusal_reason_code": "malformed_temporal_semantics",
            }
        elif (
            normalized.get("refusal_reason_code")
            or normalized.get("comparability_posture") not in NUMERIC_POSTURES
        ):
            semantics = normalized
    view = dict(properties)
    if semantics is not None:
        view["temporal_semantics"] = semantics
    status, interval = feature_temporal_admission(view)
    start = properties.get("time_start_bp") if interval is not None else None
    end = properties.get("time_end_bp") if interval is not None else None
    mean = properties.get("time_mean_bp") if interval is not None else None
    if "sample_chronologies" in properties and interval is not None:
        start, end = interval
    comparable = status == "admitted"
    if not comparable:
        start = end = mean = None
    window_key, window_label = resolve_temporal_window(
        time_start_bp=parse_year_bp(start),
        time_end_bp=parse_year_bp(end),
        time_mean_bp=parse_year_bp(mean),
    )
    result: dict[str, object] = {
        "source_record": deepcopy(dict(properties)),
        "time_start_bp": start,
        "time_end_bp": end,
        "time_mean_bp": mean,
        "time_year_bp": mean,
        "time_label": properties.get("time_label", ""),
        "temporal_window_key": window_key,
        "temporal_window_label": window_label,
        "temporal_comparability_posture": (semantics or {}).get(
            "comparability_posture", ""
        ),
        "temporal_comparison_note": (semantics or {}).get("comparison_note", ""),
    }
    for key in (
        "schema_version",
        "genetic_id",
        "sample_id",
        "master_id",
        "group_id",
        "sample_namespace",
        "accession_lineage",
        "source_family",
        "sample_chronology",
        "sample_identity",
        "identity",
        "locality_identity",
        "political_entity",
        "locality_namespace",
        "locality_token",
        "sample_chronologies",
        "sample_ids",
        "sample_count",
        "chronology_role",
        "source_calendar_support",
        "declared_calendar_support",
    ):
        if key in properties:
            result[key] = deepcopy(properties[key])
    if semantics is not None:
        result["temporal_semantics"] = semantics
    return result


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
    validate_public_geojson_schemas(geojson, normalized_features)
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
