"""Bind selected SEAD site features to their historical lineage."""

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from pathlib import Path

from .chronology_overlay import _canonical


def validate_site_binding(
    data_root: Path,
    lineage_sha256: str,
    site_rows: Mapping[str, Mapping[str, object]],
    layers: Sequence[Mapping[str, object]],
) -> None:
    """Bind the site rows and displayed identity/bounds to the selected lineage."""
    from bijux_pollenomics.core.filesystem import read_regular_file
    from bijux_pollenomics.reporting.context.points.external import (
        build_external_point_layer,
    )

    normalized = data_root / "sead/normalized"
    lineage_bytes = read_regular_file(
        normalized / "source_lineage.json", max_bytes=8 * 1024 * 1024
    )
    if hashlib.sha256(lineage_bytes).hexdigest() != lineage_sha256:
        raise ValueError("SEAD derived chronology site lineage differs")
    lineage = json.loads(lineage_bytes)
    source_bytes = read_regular_file(
        normalized / "nordic_environmental_sites.geojson", max_bytes=64 * 1024 * 1024
    )
    if (
        not isinstance(lineage, dict)
        or not isinstance(lineage.get("normalized_surface_sha256"), dict)
        or lineage["normalized_surface_sha256"].get(
            "normalized/nordic_environmental_sites.geojson"
        )
        != hashlib.sha256(source_bytes).hexdigest()
    ):
        raise ValueError("SEAD derived chronology site source differs")
    source = json.loads(source_bytes)
    if (
        not isinstance(source, dict)
        or source.get("type") != "FeatureCollection"
        or not isinstance(source.get("features"), list)
    ):
        raise ValueError("SEAD derived chronology site source differs")
    rows: dict[str, Mapping[str, object]] = {}
    coordinates: dict[str, tuple[float, float]] = {}
    for feature in source["features"]:
        if not isinstance(feature, dict) or not isinstance(
            feature.get("properties"), dict
        ):
            raise ValueError("SEAD derived chronology site source differs")
        properties = feature["properties"]
        identifier = properties.get("record_id")
        if not isinstance(identifier, str) or not identifier or identifier in rows:
            raise ValueError("SEAD derived chronology site identity differs")
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("type") != "Point":
            raise ValueError("SEAD derived chronology site geometry differs")
        point = geometry.get("coordinates")
        if (
            not isinstance(point, list)
            or len(point) < 2
            or any(
                type(value) not in (int, float) or not math.isfinite(value)
                for value in point[:2]
            )
        ):
            raise ValueError("SEAD derived chronology site coordinates differ")
        longitude, latitude = float(point[0]), float(point[1])
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise ValueError("SEAD derived chronology site coordinates differ")
        coordinates[identifier] = (longitude, latitude)
        rows[identifier] = properties
    if _canonical(rows) != _canonical(site_rows):
        raise ValueError("SEAD derived chronology site rows differ")
    site_layers = [layer for layer in layers if layer.get("key") == "sead-sites"]
    if len(site_layers) != 1 or not isinstance(site_layers[0].get("features"), list):
        raise ValueError("SEAD derived chronology site layer differs")
    reference = build_external_point_layer(
        source, source_path=Path("nordic_environmental_sites.geojson")
    )
    actual_metadata = {
        key: value for key, value in site_layers[0].items() if key != "features"
    }
    reference_metadata = {
        key: value for key, value in reference.items() if key != "features"
    }
    if _canonical(actual_metadata) != _canonical(reference_metadata):
        raise ValueError("SEAD derived chronology site layer differs")
    reference_features = reference.get("features")
    if not isinstance(reference_features, list):
        raise ValueError("SEAD derived chronology site reference differs")
    expected = {
        item["evidence_row_id"]: item
        for item in reference_features
        if isinstance(item, dict) and isinstance(item.get("evidence_row_id"), str)
    }
    if len(expected) != len(rows):
        raise ValueError("SEAD derived chronology site reference differs")
    seen: set[str] = set()
    features = site_layers[0]["features"]
    if not isinstance(features, list):
        raise ValueError("SEAD derived chronology site layer differs")
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError("SEAD derived chronology site feature differs")
        identifier = feature.get("evidence_row_id")
        if (
            not isinstance(identifier, str)
            or identifier in seen
            or identifier not in rows
        ):
            raise ValueError("SEAD derived chronology site identity differs")
        seen.add(identifier)
        layer_longitude, layer_latitude = (
            feature.get("longitude"),
            feature.get("latitude"),
        )
        if (
            not isinstance(layer_longitude, (int, float))
            or isinstance(layer_longitude, bool)
            or not isinstance(layer_latitude, (int, float))
            or isinstance(layer_latitude, bool)
            or not math.isfinite(layer_longitude)
            or not math.isfinite(layer_latitude)
            or (layer_longitude, layer_latitude) != coordinates[identifier]
        ):
            raise ValueError("SEAD derived chronology site coordinates differ")
        copied = dict(feature)
        record_id = copied.pop("record_id", None)
        if record_id is not None and record_id != f"sead:site:{identifier}":
            raise ValueError("SEAD derived chronology site identity differs")
        if _canonical(copied) != _canonical(expected[identifier]):
            raise ValueError("SEAD derived chronology site feature differs")
        if any(
            _canonical(feature.get(key)) != _canonical(rows[identifier].get(key))
            for key in ("site_uuid", "country", "time_start_bp", "time_end_bp")
        ):
            raise ValueError("SEAD derived chronology site feature differs")
    if seen != set(rows):
        raise ValueError("SEAD derived chronology site set differs")


def validate_staged_site_copy(
    data_root: Path, staging_root: Path, lineage_sha256: str
) -> None:
    """Check the selected site bytes and the Atlas staged copy against lineage."""
    from bijux_pollenomics.core.filesystem import read_regular_file

    normalized = data_root / "sead/normalized"
    lineage_bytes = read_regular_file(
        normalized / "source_lineage.json", max_bytes=8 * 1024 * 1024
    )
    if hashlib.sha256(lineage_bytes).hexdigest() != lineage_sha256:
        raise ValueError("staged SEAD site lineage differs")
    lineage = json.loads(lineage_bytes)
    surfaces = (
        lineage.get("normalized_surface_sha256") if isinstance(lineage, dict) else None
    )
    if not isinstance(surfaces, dict):
        raise ValueError("staged SEAD site lineage differs")
    expected = surfaces.get("normalized/nordic_environmental_sites.geojson")
    name = "nordic_environmental_sites.geojson"
    selected = read_regular_file(normalized / name, max_bytes=64 * 1024 * 1024)
    staged = read_regular_file(staging_root / name, max_bytes=64 * 1024 * 1024)
    if (
        not isinstance(expected, str)
        or hashlib.sha256(selected).hexdigest() != expected
        or selected != staged
    ):
        raise ValueError("staged SEAD site copy differs")
