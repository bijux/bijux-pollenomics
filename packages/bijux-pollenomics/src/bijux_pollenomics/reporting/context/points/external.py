from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from ....collection.contracts.cardinality import require_nonnegative_count
from ...map_document.adna_exports import (
    LOCALITY_SCHEMA,
    SAMPLE_SCHEMA,
    validate_locality_export_identity,
)
from ..time import (
    extract_layer_identity,
    feature_has_time,
    feature_time_payload,
    normalize_media_links,
    validate_feature_collection,
)
from .shared import POINT_LAYER_METADATA, POINT_LAYER_STYLES


def build_external_point_layer(
    geojson: dict[str, object],
    *,
    source_path: Path | None = None,
) -> dict[str, object]:
    """Convert normalized GeoJSON into a map layer payload."""
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    raw_features = validate_feature_collection(geojson, source_path=source_path)
    sample_properties, layer_key, layer_label = extract_layer_identity(
        raw_features, source_path=source_path
    )
    features = []
    for feature in raw_features:
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        if not isinstance(geometry, dict) or not isinstance(properties, dict):
            raise ValueError(
                f"{source_label} contains a feature with invalid geometry or properties"
            )
        if geometry.get("type") != "Point":
            raise ValueError(
                f"{source_label} point layers must contain only Point geometries"
            )
        coordinates = geometry.get("coordinates", [])
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise ValueError(
                f"{source_label} point layers must contain coordinate pairs"
            )
        popup_rows = properties.get("popup_rows", [])
        if not isinstance(popup_rows, list):
            popup_rows = []
        try:
            longitude = float(coordinates[0])
            latitude = float(coordinates[1])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{source_label} contains a point with non-numeric coordinates"
            ) from exc
        native_record_id, native_title = _export_record_identity(properties)
        mapped_feature = {
            "latitude": latitude,
            "longitude": longitude,
            "country": _export_country(properties),
            "title": native_title or str(properties.get("name", "")).strip(),
            "subtitle": str(properties.get("category", "")).strip(),
            "popup_rows": popup_rows,
            "source_url": str(properties.get("source_url", "")).strip(),
            "evidence_row_id": native_record_id
            or str(properties.get("record_id", "")).strip(),
            "media_links": normalize_media_links(properties.get("media_links", [])),
            **feature_time_payload(properties),
        }
        for key, envelope in (
            ("source_feature_schema_version", feature),
            ("source_collection_schema_version", geojson),
        ):
            if "schema_version" in envelope:
                mapped_feature[key] = envelope["schema_version"]
        if "record_count" in properties:
            mapped_feature["record_count"] = require_nonnegative_count(
                properties["record_count"],
                field=f"{source_label} feature record_count",
            )
        site_uuid = properties.get("site_uuid")
        if isinstance(site_uuid, str) and site_uuid.strip():
            mapped_feature["site_uuid"] = site_uuid.strip()
        features.append(mapped_feature)

    applies_country_filter = any(feature.get("country") for feature in features)
    applies_time_filter = any(feature_has_time(feature) for feature in features)
    metadata = cast(dict[str, object], POINT_LAYER_METADATA.get(layer_key, {}))
    return {
        "key": layer_key,
        "label": layer_label,
        "count": len(features),
        "description": str(sample_properties.get("subtitle", "")).strip(),
        "group": metadata.get("group", "context"),
        "source_name": metadata.get("source_name", layer_label),
        "coverage_label": metadata.get(
            "coverage_label", "Country-aware contextual points."
        ),
        "geometry_label": metadata.get("geometry_label", "Point records"),
        "default_enabled": metadata.get("default_enabled", True),
        "applies_country_filter": applies_country_filter,
        "applies_time_filter": metadata.get("applies_time_filter", applies_time_filter),
        "circle_enabled": True,
        "traceability_artifact": "" if source_path is None else source_path.name,
        "style": POINT_LAYER_STYLES.get(
            layer_key,
            {
                "fill": "#475569",
                "stroke": "#1e293b",
                "circleStroke": "rgba(71, 85, 105, 0.42)",
                "circleFill": "rgba(148, 163, 184, 0.10)",
            },
        ),
        "features": features,
    }


__all__ = ["build_external_point_layer"]


def _export_country(properties: dict[str, object]) -> str:
    """Retain declared native geography without coordinate or label inference."""
    schema = properties.get("schema_version")
    if not isinstance(schema, str) or schema not in {
        SAMPLE_SCHEMA,
        "adna-sample-record-export.v1",
        LOCALITY_SCHEMA,
        "adna-locality-summary-export.v1",
    }:
        return str(properties.get("country", "")).strip()
    if schema == LOCALITY_SCHEMA:
        validate_locality_export_identity(properties)
    identity = properties.get("locality_identity", properties.get("identity"))
    political = properties.get("political_entity")
    if "political_entity" not in properties and isinstance(identity, dict):
        political = identity.get("political_entity")
    country = properties.get("country")
    if any(
        value is not None and not isinstance(value, str)
        for value in (political, country)
    ):
        raise ValueError("Sample export geography must remain source text or null")
    political_text = political.strip() if isinstance(political, str) else ""
    country_text = country.strip() if isinstance(country, str) else ""
    if country_text and political_text and country_text != political_text:
        raise ValueError("Sample export country and political entity disagree")
    return country_text or political_text


def _export_record_identity(properties: dict[str, object]) -> tuple[str, str]:
    """Project source-owned identity for named exports, never labels or coordinates."""
    schema = properties.get("schema_version")
    identity: object = None
    if schema == SAMPLE_SCHEMA:
        identity = properties.get("sample_identity")
        support = properties.get("sample_chronology")
        if (
            not isinstance(identity, dict)
            or not isinstance(support, dict)
            or identity.get("stable_token") != properties.get("genetic_id")
            or identity.get("namespace") != properties.get("sample_namespace")
            or support.get("sample_id") != properties.get("genetic_id")
        ):
            return ("", "")
    elif schema == LOCALITY_SCHEMA:
        identity = properties.get("locality_identity", properties.get("identity"))
        validate_locality_export_identity(properties)
    else:
        return ("", "")
    if not isinstance(identity, dict) or any(
        not isinstance(identity.get(key), str) or not str(identity[key]).strip()
        for key in ("namespace", "stable_token")
    ):
        return ("", "")
    record_id = json.dumps(
        [identity["namespace"], identity["stable_token"]],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    title = next(
        (
            value.strip()
            for value in (
                properties.get("name"),
                properties.get("locality"),
                identity.get("locality_text"),
                identity["stable_token"],
            )
            if isinstance(value, str) and value.strip()
        ),
        "",
    )
    return record_id, title
