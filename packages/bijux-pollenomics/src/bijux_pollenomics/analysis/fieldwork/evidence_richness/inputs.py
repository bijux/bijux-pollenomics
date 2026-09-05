"""Governed lake and context evidence readers."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.spatial.representative_points import (
    geometry_to_representative_point,
)
from .candidates import (
    _build_lake_token,
    _clean_lake_name_display,
    _lake_name_key,
    _normalize_note_text,
    _note_signals_position_uncertainty,
)
from .models import (
    _DensityCell,
    _SvarLakeRecord,
)
from .temporal import (
    _optional_int,
)

__all__ = []


def _load_sweden_pollen_points(context_root: Path) -> tuple[ContextPointRecord, ...]:
    paths = (
        context_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
        context_root
        / "landclim"
        / "normalized"
        / "nordic_pollen_site_sequences.geojson",
    )
    records: list[ContextPointRecord] = []
    for path in paths:
        records.extend(_load_sweden_context_points(path, country="Sweden"))
    return tuple(records)


def _load_sweden_context_points(
    path: Path,
    *,
    country: str,
) -> tuple[ContextPointRecord, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    records: list[ContextPointRecord] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue
        if str(properties.get("country", "")).strip() != country:
            continue
        coordinates = geometry.get("coordinates", [])
        if (
            geometry.get("type") != "Point"
            or not isinstance(coordinates, list)
            or len(coordinates) < 2
        ):
            continue
        longitude, latitude = coordinates[0], coordinates[1]
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        popup_rows = tuple(
            (
                str(item.get("label", "")),
                str(item.get("value", "")),
            )
            for item in properties.get("popup_rows", [])
            if isinstance(item, dict)
        )
        records.append(
            ContextPointRecord(
                source=str(properties.get("source", "")),
                layer_key=str(properties.get("layer_key", "")),
                layer_label=str(properties.get("layer_label", "")),
                category=str(properties.get("category", "")),
                country=str(properties.get("country", "")),
                record_id=str(properties.get("record_id", "")),
                name=str(properties.get("name", "")),
                latitude=float(latitude),
                longitude=float(longitude),
                geometry_type=str(properties.get("geometry_type", "Point")),
                subtitle=str(properties.get("subtitle", "")),
                description=str(properties.get("description", "")),
                source_url=str(properties.get("source_url", "")),
                record_count=int(properties.get("record_count", 1) or 1),
                popup_rows=popup_rows,
                time_start_bp=_optional_int(properties.get("time_start_bp")),
                time_end_bp=_optional_int(properties.get("time_end_bp")),
                time_mean_bp=_optional_int(properties.get("time_mean_bp")),
                time_label=str(properties.get("time_label", "")),
                temporal_semantics=properties.get("temporal_semantics")
                if isinstance(properties.get("temporal_semantics"), dict)
                else None,
            )
        )
    return tuple(records)


def _load_sweden_density_cells(path: Path) -> tuple[_DensityCell, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    cells: list[_DensityCell] = []
    for feature in payload.get("features", []):
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        if not isinstance(geometry, dict) or not isinstance(properties, dict):
            continue
        if geometry.get("type") != "Polygon":
            continue
        rings = geometry.get("coordinates", [])
        if not isinstance(rings, list) or not rings:
            continue
        ring = rings[0]
        if not isinstance(ring, list) or not ring:
            continue
        latitudes = [
            float(coordinate[1])
            for coordinate in ring
            if isinstance(coordinate, list)
            and len(coordinate) >= 2
            and isinstance(coordinate[0], (int, float))
            and isinstance(coordinate[1], (int, float))
        ]
        longitudes = [
            float(coordinate[0])
            for coordinate in ring
            if isinstance(coordinate, list)
            and len(coordinate) >= 2
            and isinstance(coordinate[0], (int, float))
            and isinstance(coordinate[1], (int, float))
        ]
        if not latitudes or not longitudes:
            continue
        cells.append(
            _DensityCell(
                min_latitude=min(latitudes),
                max_latitude=max(latitudes),
                min_longitude=min(longitudes),
                max_longitude=max(longitudes),
                count=int(properties.get("count", 0) or 0),
            )
        )
    return tuple(cells)


def _load_sweden_svar_lakes(path: Path) -> tuple[_SvarLakeRecord, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    lakes: list[_SvarLakeRecord] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue
        country = str(properties.get("country", "")).strip()
        if country not in {"SE", "Sweden"}:
            continue
        representative_point = geometry_to_representative_point(geometry)
        if representative_point is None:
            continue
        longitude, latitude, _geometry_type = representative_point
        lake_name = next(
            (
                value.strip()
                for value in (
                    str(properties.get("name", "")),
                    str(properties.get("register_name", "")),
                    str(properties.get("water_name", "")),
                    str(properties.get("fallback_name", "")),
                )
                if value.strip()
            ),
            "",
        )
        if not lake_name:
            continue
        cleaned_name = _clean_lake_name_display(lake_name)
        name_key = _lake_name_key(cleaned_name)
        if not name_key:
            continue
        area_km2 = properties.get("area_km2")
        lakes.append(
            _SvarLakeRecord(
                lake_name=cleaned_name,
                lake_label=cleaned_name,
                lake_token=_build_lake_token(
                    cleaned_name,
                    latitude=float(latitude),
                    longitude=float(longitude),
                ),
                name_key=name_key,
                latitude=round(float(latitude), 6),
                longitude=round(float(longitude), 6),
                source_url=str(properties.get("source_url", "")).strip(),
                lake_registry_id=str(properties.get("sjoid", "")).strip(),
                lake_registry_uuid=str(properties.get("sj_uuid", "")).strip(),
                lake_water_identity=str(properties.get("sj_vatten_id", "")).strip(),
                lake_name_status=str(properties.get("lake_name_status", "")).strip(),
                lake_area_km2=float(area_km2)
                if isinstance(area_km2, (int, float))
                else None,
                lake_sampling_readiness_posture=str(
                    properties.get("sampling_readiness_posture", "site_review_required")
                ).strip(),
                lake_sampling_missing_inputs=tuple(
                    str(value).strip()
                    for value in properties.get("sampling_missing_inputs", [])
                    if str(value).strip()
                )
                if isinstance(properties.get("sampling_missing_inputs"), list)
                else (),
            )
        )
    return tuple(
        sorted(lakes, key=lambda lake: (lake.lake_name, lake.latitude, lake.longitude))
    )


def _load_sweden_neotoma_position_notes(context_root: Path) -> dict[str, str]:
    path = context_root / "neotoma" / "raw" / "neotoma_pollen_sites.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return {}
    notes: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        site_id = str(row.get("siteid", "")).strip()
        note = _normalize_note_text(str(row.get("notes", "")))
        if site_id and note and _note_signals_position_uncertainty(note):
            notes[site_id] = note
    return notes


def _load_review_payload(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}
