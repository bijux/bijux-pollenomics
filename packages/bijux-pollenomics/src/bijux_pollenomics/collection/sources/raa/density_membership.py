"""Deterministic native-record membership in the legacy RAÄ density grid."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import json
import math
from typing import TypedDict

from ....core.geospatial.geojson import as_mapping
from ....core.text import clean_optional_text
from ...spatial import geometry_to_representative_point, point_in_geometry
from ...spatial.country_classification.topology import polygons_from_geometry
from .inventory import native_feature_ids, source_features, validate_inventory

SCHEMA_VERSION = "raa-density-membership-v1"


class DensityRecord(TypedDict):
    """One original native identity and its mutually exclusive disposition."""

    native_id: str
    source_status: object
    geometry_type: object
    disposition: str
    reason_code: str
    representative_method: str | None
    representative_point: list[float] | None
    grid_cell: list[int] | None


class DensityCell(TypedDict):
    """An occupied one-degree cell supported by included native identities."""

    longitude: int
    latitude: int
    count: int


class DensityMembership(TypedDict):
    """Source accounting that makes no claim of scientific authority."""

    schema_version: str
    selection_policy: str
    grid_cell_size_degrees: float
    semantic_payload_identity: dict[str, str]
    raw_inventory_identity: dict[str, object] | None
    counts: dict[str, int]
    records: list[DensityRecord]
    cells: list[DensityCell]
    scientific_admission: bool


def semantic_payload_sha256(payload: Mapping[str, object]) -> str:
    """Hash canonical JSON values, independently of any captured byte spelling."""
    encoded = json.dumps(
        dict(payload),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def build_raa_density_membership(
    *,
    feature_inventory: Mapping[str, object],
    sweden_boundary: Mapping[str, object],
) -> DensityMembership:
    """Account for every original source ID before aggregating country members."""
    features = validate_inventory(feature_inventory)
    identifiers = native_feature_ids(features)
    boundary_features = source_features(sweden_boundary)
    if not boundary_features:
        raise ValueError("Sweden boundary payload must contain features")
    geometries = []
    for feature in boundary_features:
        geometry = as_mapping(feature.get("geometry"))
        polygons = polygons_from_geometry(geometry) if geometry is not None else ()
        if not polygons or any(not polygon or not polygon[0] for polygon in polygons):
            raise ValueError(
                "Sweden boundary feature must contain nonempty polygon geometry"
            )
        assert geometry is not None
        geometries.append(geometry)
    counts = {
        "archived": len(features),
        "heritage_source_class": 0,
        "included": 0,
        "excluded_source_class": 0,
        "excluded_outside_boundary": 0,
        "unusable_geometry": 0,
    }
    records: list[DensityRecord] = []
    cells: dict[tuple[int, int], int] = {}
    for feature, identifier in zip(features, identifiers, strict=True):
        properties = as_mapping(feature.get("properties"))
        assert properties is not None
        source_status = properties.get("antikvariskbedomningtyp_namn")
        geometry = as_mapping(feature.get("geometry"))
        record: DensityRecord = {
            "native_id": identifier,
            "source_status": deepcopy(source_status),
            "geometry_type": deepcopy(geometry.get("type"))
            if geometry is not None
            else None,
            "disposition": "excluded_source_class",
            "reason_code": "source_class_not_selected",
            "representative_method": None,
            "representative_point": None,
            "grid_cell": None,
        }
        if clean_optional_text(source_status) == "Fornlämning":
            counts["heritage_source_class"] += 1
            record["disposition"] = "unusable_geometry"
            record["reason_code"] = (
                "missing_geometry"
                if feature.get("geometry") is None
                else "unrepresentable_geometry"
            )
            try:
                point = (
                    geometry_to_representative_point(geometry)
                    if geometry is not None
                    else None
                )
            except (OverflowError, TypeError, ValueError):
                point = None
            if point is not None and all(math.isfinite(value) for value in point[:2]):
                longitude, latitude, _ = point
                record["representative_point"] = [longitude, latitude]
                record["representative_method"] = "geometry_to_representative_point"
                record["disposition"] = "excluded_outside_boundary"
                record["reason_code"] = "representative_point_outside_sweden"
                if any(
                    point_in_geometry(longitude, latitude, boundary)
                    for boundary in geometries
                ):
                    cell = (math.floor(longitude), math.floor(latitude))
                    record["disposition"] = "included"
                    record["reason_code"] = "representative_point_inside_sweden"
                    record["grid_cell"] = list(cell)
                    cells[cell] = cells.get(cell, 0) + 1
        counts[record["disposition"]] += 1
        records.append(record)
    return {
        "schema_version": SCHEMA_VERSION,
        "selection_policy": "exact-fornlamning-existing-representative-point-sweden-all-components-v1",
        "grid_cell_size_degrees": 1.0,
        "semantic_payload_identity": {
            "canonicalization": "json-sorted-keys-utf8-compact-v1",
            "feature_inventory_sha256": semantic_payload_sha256(feature_inventory),
            "sweden_boundary_sha256": semantic_payload_sha256(sweden_boundary),
        },
        "raw_inventory_identity": None,
        "counts": counts,
        "records": sorted(records, key=lambda record: record["native_id"]),
        "cells": [
            {"longitude": longitude, "latitude": latitude, "count": count}
            for (longitude, latitude), count in sorted(
                cells.items(), key=lambda item: (item[0][1], item[0][0])
            )
        ],
        "scientific_admission": False,
    }
