from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]
from pyproj import Transformer

from ..core.files import write_json
from ..core.http import fetch_text
from .contracts import SVAR_LAKE_GEOJSON

SVAR_WFS_URL: Final[str] = "https://vattenwebb.smhi.se/svarwebb/svar.map"
SVAR_TYPENAME: Final[str] = "lakes"
SVAR_PAGE_SIZE: Final[int] = 250
SVAR_SOURCE_URL: Final[str] = "https://vattenwebb.smhi.se/svarwebb/"
_NAMESPACES: Final[dict[str, str]] = {
    "gml": "http://www.opengis.net/gml/3.2",
    "ms": "http://mapserver.gis.umn.edu/mapserver",
    "wfs": "http://www.opengis.net/wfs/2.0",
}
_SWEREF99_TM_TO_WGS84 = Transformer.from_crs(
    "EPSG:3006",
    "EPSG:4326",
    always_xy=True,
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
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    matched_count = _fetch_svar_lake_count()
    features = _fetch_svar_lake_features()

    raw_manifest_path = raw_dir / "svar_lake_registry_manifest.json"
    normalized_lake_geojson_path = SVAR_LAKE_GEOJSON.source_path_under(output_root)
    summary_path = normalized_dir / "svar_summary.json"
    write_json(
        raw_manifest_path,
        {
            "generated_on": str(date.today()),
            "source": "SMHI SVAR",
            "source_url": SVAR_SOURCE_URL,
            "wfs_url": SVAR_WFS_URL,
            "typename": SVAR_TYPENAME,
            "page_size": SVAR_PAGE_SIZE,
            "matched_lake_count": matched_count,
            "normalized_lake_count": len(features),
        },
    )
    write_json(
        normalized_lake_geojson_path,
        {
            "type": "FeatureCollection",
            "features": features,
        },
    )
    write_json(
        summary_path,
        {
            "generated_on": str(date.today()),
            "source": "SMHI SVAR",
            "lake_count": len(features),
            "layer_key": "svar-lakes",
        },
    )
    return SvarDataReport(
        output_dir=output_root,
        lake_count=len(features),
        raw_manifest_path=raw_manifest_path,
        normalized_lake_geojson_path=normalized_lake_geojson_path,
        summary_path=summary_path,
    )


def _fetch_svar_lake_count() -> int:
    payload = fetch_text(
        SVAR_WFS_URL,
        params={
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "TYPENAME": SVAR_TYPENAME,
            "RESULTTYPE": "hits",
        },
    )
    root = ET.fromstring(payload)
    matched = root.attrib.get("numberMatched", "0")
    return int(matched) if str(matched).isdigit() else 0


def _fetch_svar_lake_features() -> list[dict[str, object]]:
    matched_count = _fetch_svar_lake_count()
    features: list[dict[str, object]] = []
    for start_index in range(0, matched_count, SVAR_PAGE_SIZE):
        payload = fetch_text(
            SVAR_WFS_URL,
            params={
                "SERVICE": "WFS",
                "VERSION": "2.0.0",
                "REQUEST": "GetFeature",
                "TYPENAME": SVAR_TYPENAME,
                "COUNT": str(SVAR_PAGE_SIZE),
                "STARTINDEX": str(start_index),
            },
        )
        features.extend(_parse_svar_lake_features(payload))
    return features


def _parse_svar_lake_features(payload: str) -> list[dict[str, object]]:
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
            rings = _parse_polygon_rings(polygon)
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


def _parse_polygon_rings(polygon: ET.Element) -> list[list[list[float]]]:
    rings: list[list[list[float]]] = []
    for ring in polygon.findall(".//gml:LinearRing", _NAMESPACES):
        pos_list = ring.findtext("gml:posList", default="", namespaces=_NAMESPACES)
        coordinates = _parse_pos_list(pos_list)
        if coordinates:
            rings.append(coordinates)
    return rings


def _parse_pos_list(pos_list: str) -> list[list[float]]:
    values = pos_list.strip().split()
    if len(values) < 4 or len(values) % 2 != 0:
        return []
    coordinates: list[list[float]] = []
    for index in range(0, len(values), 2):
        easting = float(values[index])
        northing = float(values[index + 1])
        longitude, latitude = _SWEREF99_TM_TO_WGS84.transform(easting, northing)
        coordinates.append([round(longitude, 6), round(latitude, 6)])
    return coordinates


def _parse_svar_properties(
    lake: ET.Element,
    geometry: dict[str, object],
) -> dict[str, object]:
    register_name = lake.findtext("ms:Register/ms:SNAMN", default="", namespaces=_NAMESPACES)
    water_name = lake.findtext("ms:VYNAMN", default="", namespaces=_NAMESPACES)
    fallback_name = lake.findtext("ms:LW_PopNamn", default="", namespaces=_NAMESPACES)
    lake_name = next(
        (
            value.strip()
            for value in (register_name, water_name, fallback_name)
            if value and value.strip()
        ),
        "",
    )
    return {
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
        "sj_vatten_id": lake.findtext("ms:SJVattenID", default="", namespaces=_NAMESPACES),
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
]
