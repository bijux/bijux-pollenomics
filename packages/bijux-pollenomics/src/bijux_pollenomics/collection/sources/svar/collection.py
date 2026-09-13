from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Final

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]
from pyproj import Transformer

from ....core.files import write_json
from ....core.owned_tree import publish_new_output_tree
from ...contracts.artifacts import SVAR_LAKE_GEOJSON
from .capture import capture_svar_wfs
from .replay import (
    SUPPORTED_CRS,
    SVAR_PAGE_SIZE,
    SVAR_TYPENAME,
    SVAR_WFS_URL,
    replay_svar_capture,
)

SVAR_SOURCE_URL: Final[str] = "https://vattenwebb.smhi.se/svarwebb/"
_NAMESPACES: Final[dict[str, str]] = {
    "gml": "http://www.opengis.net/gml/3.2",
    "ms": "http://mapserver.gis.umn.edu/mapserver",
    "wfs": "http://www.opengis.net/wfs/2.0",
}
_PROPERTY_PATHS: Final[tuple[str, ...]] = (
    "Register/SNAMN",
    "VYNAMN",
    "LW_PopNamn",
    "COUNTRY",
    "SJOID",
    "SJ_UUID",
    "SJVattenID",
    "DISTRICT",
    "VYHOJD",
    "AREA",
)


@dataclass(frozen=True)
class SvarDataReport:
    output_dir: Path
    lake_count: int
    raw_manifest_path: Path
    normalized_lake_geojson_path: Path
    summary_path: Path


def collect_svar_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
) -> SvarDataReport:
    """Download and normalize the official SMHI SVAR Sweden lake registry."""
    del country_boundaries
    output_root = Path(output_root)
    for path in (output_root, *output_root.parents):
        if path.is_symlink():
            raise ValueError("svar_symlink_output_or_capture")
    output_root = Path(os.path.abspath(output_root))
    for path in (output_root, *output_root.parents):
        if path.is_symlink():
            raise ValueError("svar_symlink_output_or_capture")
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)

    capture_root = raw_dir / "wfs-capture"
    digest = capture_svar_wfs(capture_root)
    features = _replay_features(capture_root, digest)
    matched_count = len(features)
    generated_on = _capture_date(capture_root, digest)

    raw_manifest_path = raw_dir / "svar_lake_registry_manifest.json"
    normalized_lake_geojson_path = SVAR_LAKE_GEOJSON.source_path_under(output_root)
    summary_path = normalized_dir / "svar_summary.json"
    write_json(
        raw_manifest_path,
        {
            "generated_on": generated_on,
            "source": "SMHI SVAR",
            "source_url": SVAR_SOURCE_URL,
            "wfs_url": SVAR_WFS_URL,
            "typename": SVAR_TYPENAME,
            "page_size": SVAR_PAGE_SIZE,
            "matched_lake_count": matched_count,
            "normalized_lake_count": len(features),
            "capture_sha256": digest,
            "capture_path": "raw/wfs-capture",
        },
    )
    _publish_normalized(normalized_dir, features, generated_on=generated_on)
    return SvarDataReport(
        output_dir=output_root,
        lake_count=len(features),
        raw_manifest_path=raw_manifest_path,
        normalized_lake_geojson_path=normalized_lake_geojson_path,
        summary_path=summary_path,
    )


def _replay_features(capture_root: Path, digest: str) -> list[dict[str, object]]:
    features = []
    for payload in replay_svar_capture(capture_root, expected_sha256=digest):
        features.extend(_parse_svar_lake_features(payload))
    # Reject nonfinite normalized geometry/properties before any publication.
    json.dumps(features, allow_nan=False)
    return features


def _capture_date(directory: Path, digest: str) -> str:
    payload = (directory / "capture.json").read_bytes()
    if sha256(payload).hexdigest() != digest:
        raise ValueError("svar_capture_changed_during_replay")
    manifest = json.loads(payload)
    value: str = manifest["members"][0]["retrieved_at"]
    return value.split("T", 1)[0]


def _publish_normalized(
    directory: Path, features: list[dict[str, object]], *, generated_on: str
) -> None:
    staging = Path(tempfile.mkdtemp(prefix=".svar-normalized-", dir=directory.parent))
    write_json(
        staging / "sweden_lake_registry.geojson",
        {"type": "FeatureCollection", "features": features},
    )
    write_json(
        staging / "svar_summary.json",
        {
            "generated_on": generated_on,
            "source": "SMHI SVAR",
            "lake_count": len(features),
            "layer_key": "svar-lakes",
            "coordinate_precision": "unrounded_binary64",
            "source_coordinate_order": "northing_easting",
            "output_coordinate_order": "longitude_latitude",
        },
    )
    publish_new_output_tree(final_output_root=directory, staging_output_root=staging)


def replay_svar_data(
    capture_root: Path, output_root: Path, *, expected_sha256: str
) -> SvarDataReport:
    """Build a new normalized-only family from one pinned raw capture, offline.

    The source capture is copied with its original retrieval metadata and exact
    digest. It is not relabelled as newly acquired. No review is inferred.
    """
    capture_root = Path(capture_root)
    output_root = Path(output_root)
    for path in (
        output_root,
        *output_root.parents,
        capture_root,
        *capture_root.parents,
    ):
        if path.is_symlink():
            raise ValueError("svar_symlink_output_or_capture")
    output_root = Path(os.path.abspath(output_root))
    capture_root = Path(os.path.abspath(capture_root))
    for path in (
        output_root,
        *output_root.parents,
        capture_root,
        *capture_root.parents,
    ):
        if path.is_symlink():
            raise ValueError("svar_symlink_output_or_capture")
    if output_root.is_relative_to(capture_root) or capture_root.is_relative_to(
        output_root
    ):
        raise ValueError("svar_overlapping_output_or_capture")
    if output_root.exists():
        raise FileExistsError(output_root)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".svar-replay-", dir=output_root.parent))
    copied_capture = staging / "raw/wfs-capture"
    # Preserve symlinks rather than following them; replay rejects them.
    shutil.copytree(capture_root, copied_capture, symlinks=True)
    features = _replay_features(copied_capture, expected_sha256)
    generated_on = _capture_date(copied_capture, expected_sha256)
    manifest_path = staging / "raw/svar_lake_registry_manifest.json"
    write_json(
        manifest_path,
        {
            "generated_on": generated_on,
            "source": "SMHI SVAR",
            "matched_lake_count": len(features),
            "normalized_lake_count": len(features),
            "capture_sha256": expected_sha256,
            "capture_path": "raw/wfs-capture",
        },
    )
    _publish_normalized(staging / "normalized", features, generated_on=generated_on)
    publish_new_output_tree(final_output_root=output_root, staging_output_root=staging)
    return SvarDataReport(
        output_root,
        len(features),
        output_root / "raw/svar_lake_registry_manifest.json",
        output_root / "normalized/sweden_lake_registry.geojson",
        output_root / "normalized/svar_summary.json",
    )


def _parse_svar_lake_features(payload: str | bytes) -> list[dict[str, object]]:
    root = ET.fromstring(payload)
    features: list[dict[str, object]] = []
    for member in root.findall("wfs:member", _NAMESPACES):
        lake = member.find("ms:lakes", _NAMESPACES)
        if lake is None:
            continue
        geometry = _parse_svar_geometry(lake)
        if geometry is None:
            continue
        properties = _parse_svar_properties(lake, geometry)
        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
            }
        )
    return features


def _parse_svar_geometry(lake: ET.Element) -> dict[str, object] | None:
    geometry = lake.find("ms:msGeometry", _NAMESPACES)
    if geometry is None:
        return None
    multipolygon = geometry.find("gml:MultiSurface", _NAMESPACES)
    if multipolygon is not None:
        polygons = []
        for polygon_member in multipolygon.findall(".//gml:surfaceMember", _NAMESPACES):
            polygon = polygon_member.find("gml:Polygon", _NAMESPACES)
            if polygon is None:
                continue
            rings = _parse_polygon_rings(
                polygon, inherited_crs=multipolygon.get("srsName")
            )
            if rings:
                polygons.append(rings)
        if polygons:
            return {"type": "MultiPolygon", "coordinates": polygons}
        return None
    polygon = geometry.find("gml:Polygon", _NAMESPACES)
    if polygon is None:
        return None
    rings = _parse_polygon_rings(polygon)
    if not rings:
        return None
    return {"type": "Polygon", "coordinates": rings}


def _parse_polygon_rings(
    polygon: ET.Element, *, inherited_crs: str | None = None
) -> list[list[list[float]]]:
    rings: list[list[list[float]]] = []
    for ring in polygon.findall(".//gml:LinearRing", _NAMESPACES):
        pos_list = ring.findtext("gml:posList", default="", namespaces=_NAMESPACES)
        coordinates = _parse_pos_list(
            pos_list, source_crs=polygon.get("srsName", inherited_crs)
        )
        if coordinates:
            rings.append(coordinates)
    return rings


@lru_cache(maxsize=4)
def _coordinate_transformer(source_crs: str | None) -> Transformer:
    # The no-CRS helper retains its historical explicit easting/northing API.
    # Production pages must pass declared-CRS admission before reaching it.
    if source_crs is None:
        return Transformer.from_crs("EPSG:3006", "OGC:CRS84", always_xy=True)
    if source_crs not in SUPPORTED_CRS:
        raise ValueError("svar_unsupported_or_missing_crs")
    return Transformer.from_crs(SUPPORTED_CRS[source_crs], "OGC:CRS84", always_xy=False)


def _parse_pos_list(
    pos_list: str, *, source_crs: str | None = None
) -> list[list[float]]:
    values = pos_list.strip().split()
    if len(values) < 4 or len(values) % 2 != 0:
        return []
    coordinates: list[list[float]] = []
    for index in range(0, len(values), 2):
        native_first = float(values[index])
        native_second = float(values[index + 1])
        longitude, latitude = _coordinate_transformer(source_crs).transform(
            native_first, native_second, errcheck=True
        )
        if (
            not math.isfinite(longitude)
            or not math.isfinite(latitude)
            or not (-180 <= longitude <= 180 and -90 <= latitude <= 90)
        ):
            raise ValueError("svar_invalid_transformed_coordinate")
        coordinates.append(
            [round(longitude, 6), round(latitude, 6)]
            if source_crs is None
            else [longitude, latitude]
        )
    return coordinates


def _parse_svar_properties(
    lake: ET.Element,
    geometry: dict[str, object],
) -> dict[str, object]:
    register_name = _normalize_svar_text(
        lake.findtext("ms:Register/ms:SNAMN", default="", namespaces=_NAMESPACES)
    )
    water_name = _normalize_svar_text(
        lake.findtext("ms:VYNAMN", default="", namespaces=_NAMESPACES)
    )
    fallback_name = _normalize_svar_text(
        lake.findtext("ms:LW_PopNamn", default="", namespaces=_NAMESPACES)
    )
    lake_name = next(
        (
            value.strip()
            for value in (register_name, water_name, fallback_name)
            if value and value.strip()
        ),
        "",
    )
    return {
        "source_native_properties": _source_native_properties(lake),
        "derived_properties_policy": {
            "native_representation": "xml_decoded_text_and_attributes_in_occurrence_order",
            "lexical_byte_authority": "captured_wfs_page_xml",
            "missing_native_element": "empty_occurrence_list",
            "labels": "legacy_whitespace_trim_and_conditional_mojibake_repair",
            "country": (
                "legacy_absent_element_default_SE_not_source_assertion"
                if lake.find("ms:COUNTRY", _NAMESPACES) is None
                else "legacy_first_source_element"
            ),
            "numeric_values": "legacy_optional_binary64_conversion",
        },
        "source": "SMHI SVAR",
        "layer_key": "svar-lakes",
        "layer_label": "SMHI SVAR lake registry",
        "category": "Lake registry",
        "country": lake.findtext("ms:COUNTRY", default="SE", namespaces=_NAMESPACES),
        "record_id": lake.findtext("ms:SJOID", default="", namespaces=_NAMESPACES),
        "name": lake_name,
        "register_name": register_name.strip(),
        "water_name": water_name.strip(),
        "fallback_name": fallback_name.strip(),
        "sjoid": lake.findtext("ms:SJOID", default="", namespaces=_NAMESPACES),
        "sj_uuid": lake.findtext("ms:SJ_UUID", default="", namespaces=_NAMESPACES),
        "sj_vatten_id": lake.findtext(
            "ms:SJVattenID", default="", namespaces=_NAMESPACES
        ),
        "district": lake.findtext("ms:DISTRICT", default="", namespaces=_NAMESPACES),
        "water_surface_elevation_m": _optional_float(
            lake.findtext("ms:VYHOJD", default="", namespaces=_NAMESPACES)
        ),
        "area_km2": _optional_float(
            lake.findtext("ms:AREA", default="", namespaces=_NAMESPACES)
        ),
        "lake_name_status": _lake_name_status(register_name, water_name, fallback_name),
        "source_url": _svar_lake_source_url(
            lake.findtext("ms:SJOID", default="", namespaces=_NAMESPACES)
        ),
        "geometry_type": str(geometry.get("type", "")),
    }


def _source_native_properties(lake: ET.Element) -> dict[str, object]:
    """Preserve all ten consumed scalar fields before display normalization."""
    result: dict[str, object] = {}
    for path in _PROPERTY_PATHS:
        occurrences = []
        for element in lake.findall(
            "/".join("ms:" + part for part in path.split("/")), _NAMESPACES
        ):
            if len(element):
                raise ValueError("svar_non_scalar_property")
            occurrences.append(
                {"text": element.text, "attributes": dict(element.attrib)}
            )
        result[path] = occurrences
    return result


def _normalize_svar_text(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if "Ã" not in value and "Â" not in value:
        return value
    for source_encoding in ("cp1252", "latin-1"):
        try:
            repaired = value.encode(source_encoding).decode("utf-8")
        except UnicodeError:
            continue
        return repaired.strip() or value
    return value


def _optional_float(raw: str) -> float | None:
    value = raw.strip()
    if not value:
        return None
    return float(value)


def _lake_name_status(register_name: str, water_name: str, fallback_name: str) -> str:
    if register_name.strip():
        return "official_register_name"
    if water_name.strip():
        return "water_surface_name"
    if fallback_name.strip():
        return "fallback_waterwebb_label"
    return "unnamed"


def _svar_lake_source_url(sjoid: str) -> str:
    return f"{SVAR_SOURCE_URL}?sjoid={sjoid}" if sjoid else SVAR_SOURCE_URL


__all__ = [
    "SVAR_PAGE_SIZE",
    "SVAR_SOURCE_URL",
    "SVAR_TYPENAME",
    "SVAR_WFS_URL",
    "SvarDataReport",
    "collect_svar_data",
    "replay_svar_data",
]
