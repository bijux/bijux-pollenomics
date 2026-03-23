from __future__ import annotations

import csv
import json
import ssl
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import Request, urlopen


NORDIC_BBOX = (4.0, 54.0, 35.0, 72.0)
NEOTOMA_LIMIT = 400
SEAD_LIMIT = 1000


@dataclass(frozen=True)
class ExternalPointRecord:
    source: str
    layer_key: str
    layer_label: str
    category: str
    country: str
    record_id: str
    name: str
    latitude: float
    longitude: float
    geometry_type: str
    subtitle: str
    description: str
    source_url: str
    record_count: int
    popup_rows: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ContextDataReport:
    generated_on: str
    output_root: Path
    neotoma_point_count: int
    sead_point_count: int
    raa_total_site_count: int
    raa_heritage_site_count: int


def collect_context_data(output_root: Path) -> ContextDataReport:
    """Download and normalize external archaeology and palaeo datasets."""
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    neotoma_raw_dir = output_root / "neotoma" / "raw"
    neotoma_norm_dir = output_root / "neotoma" / "normalized"
    sead_raw_dir = output_root / "sead" / "raw"
    sead_norm_dir = output_root / "sead" / "normalized"
    raa_raw_dir = output_root / "raa" / "raw"
    raa_norm_dir = output_root / "raa" / "normalized"
    boundaries_raw_dir = output_root / "boundaries" / "raw"
    boundaries_norm_dir = output_root / "boundaries" / "normalized"

    for directory in [
        neotoma_raw_dir,
        neotoma_norm_dir,
        sead_raw_dir,
        sead_norm_dir,
        raa_raw_dir,
        raa_norm_dir,
        boundaries_raw_dir,
        boundaries_norm_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    country_boundaries = fetch_country_boundaries()
    for country_name, payload in country_boundaries.items():
        write_json(
            boundaries_raw_dir / f"{slugify(country_name)}.geojson",
            payload,
        )
    combined_boundaries = build_combined_country_boundaries(country_boundaries)
    write_json(
        boundaries_norm_dir / "nordic_country_boundaries.geojson",
        combined_boundaries,
    )

    neotoma_rows = fetch_neotoma_pollen_rows()
    neotoma_raw_payload = {
        "generated_on": str(date.today()),
        "source": "Neotoma",
        "endpoint": "https://api.neotomadb.org/v2.0/data/sites?datasettype=pollen",
        "row_count": len(neotoma_rows),
        "rows": neotoma_rows,
    }
    write_json(neotoma_raw_dir / "neotoma_pollen_sites.json", neotoma_raw_payload)
    neotoma_records = normalize_neotoma_rows(
        neotoma_rows,
        bbox=NORDIC_BBOX,
        country_boundaries=country_boundaries,
    )
    write_external_points_csv(
        neotoma_norm_dir / "nordic_pollen_sites.csv",
        neotoma_records,
    )
    write_external_points_geojson(
        neotoma_norm_dir / "nordic_pollen_sites.geojson",
        neotoma_records,
    )

    sead_rows = fetch_sead_site_rows(bbox=NORDIC_BBOX)
    sead_raw_payload = {
        "generated_on": str(date.today()),
        "source": "SEAD",
        "endpoint": "https://browser.sead.se/postgrest/tbl_sites",
        "row_count": len(sead_rows),
        "rows": sead_rows,
    }
    write_json(sead_raw_dir / "nordic_sites.json", sead_raw_payload)
    sead_records = normalize_sead_rows(sead_rows, country_boundaries=country_boundaries)
    write_external_points_csv(
        sead_norm_dir / "nordic_environmental_sites.csv",
        sead_records,
    )
    write_external_points_geojson(
        sead_norm_dir / "nordic_environmental_sites.geojson",
        sead_records,
    )

    raa_metadata = fetch_raa_archaeology_metadata(country_boundaries=country_boundaries)
    write_text(raa_raw_dir / "arkreg_v1_0_wfs_capabilities.xml", raa_metadata["capabilities_xml"])
    write_text(raa_raw_dir / "publicerade_lamningar_centrumpunkt_schema.xml", raa_metadata["schema_xml"])
    write_json(raa_raw_dir / "fornsok_domains.json", raa_metadata["domain_payload"])
    write_json(
        raa_norm_dir / "sweden_archaeology_layer.json",
        raa_metadata["layer_metadata"],
    )
    write_json(
        raa_norm_dir / "sweden_archaeology_density.geojson",
        raa_metadata["density_geojson"],
    )

    return ContextDataReport(
        generated_on=str(date.today()),
        output_root=output_root,
        neotoma_point_count=len(neotoma_records),
        sead_point_count=len(sead_records),
        raa_total_site_count=raa_metadata["layer_metadata"]["counts"]["all_published_sites"],
        raa_heritage_site_count=raa_metadata["layer_metadata"]["counts"]["fornlamning"],
    )


def fetch_neotoma_pollen_rows() -> list[dict[str, object]]:
    """Download all Neotoma pollen site rows using stable chunked pagination."""
    rows: list[dict[str, object]] = []
    offset = 0
    while True:
        payload = fetch_json(
            "https://api.neotomadb.org/v2.0/data/sites",
            params={
                "datasettype": "pollen",
                "limit": str(NEOTOMA_LIMIT),
                "offset": str(offset),
            },
            insecure=True,
        )
        chunk = payload.get("data", [])
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(chunk)
        if len(chunk) < NEOTOMA_LIMIT:
            break
        offset += NEOTOMA_LIMIT

    deduplicated: dict[str, dict[str, object]] = {}
    for row in rows:
        deduplicated[str(row.get("siteid", ""))] = row
    return sorted(deduplicated.values(), key=lambda item: int(item.get("siteid", 0)))


def normalize_neotoma_rows(
    rows: Iterable[dict[str, object]],
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ExternalPointRecord]:
    """Convert raw Neotoma rows into compact Nordic pollen site records."""
    records: list[ExternalPointRecord] = []
    for row in rows:
        geography_text = str(row.get("geography", "")).strip()
        if not geography_text:
            continue
        representative_point = geometry_to_representative_point(json.loads(geography_text))
        if representative_point is None:
            continue
        longitude, latitude, geometry_type = representative_point
        if not point_in_bbox(longitude=longitude, latitude=latitude, bbox=bbox):
            continue
        country = classify_country(longitude, latitude, country_boundaries)
        if not country:
            continue

        collection_units = row.get("collectionunits", [])
        if not isinstance(collection_units, list):
            collection_units = []

        dataset_types = sorted(
            {
                str(dataset.get("datasettype", "")).strip()
                for unit in collection_units
                if isinstance(unit, dict)
                for dataset in unit.get("datasets", [])
                if isinstance(dataset, dict) and str(dataset.get("datasettype", "")).strip()
            }
        )
        dataset_count = sum(
            len(unit.get("datasets", []))
            for unit in collection_units
            if isinstance(unit, dict) and isinstance(unit.get("datasets", []), list)
        )
        collection_unit_count = len(collection_units)
        site_id = str(row.get("siteid", "")).strip()
        site_name = str(row.get("sitename", "")).strip() or f"Neotoma site {site_id}"
        source_url = f"https://apps.neotomadb.org/explorer/#/record/site/{site_id}"
        description = str(row.get("sitedescription", "") or "").strip()
        altitude = clean_optional_text(row.get("altitude"))

        popup_rows = [
            ("Site ID", site_id),
            ("Category", "Pollen"),
            ("Source", "Neotoma"),
            ("Country", country),
            ("Geometry", geometry_type),
            ("Collection units", str(collection_unit_count)),
            ("Datasets", str(dataset_count)),
        ]
        if dataset_types:
            popup_rows.append(("Dataset types", ", ".join(dataset_types)))
        if altitude:
            popup_rows.append(("Altitude", altitude))
        if description:
            popup_rows.append(("Description", description))

        records.append(
            ExternalPointRecord(
                source="Neotoma",
                layer_key="neotoma-pollen",
                layer_label="Neotoma pollen sites",
                category="Pollen",
                country=country,
                record_id=site_id,
                name=site_name,
                latitude=latitude,
                longitude=longitude,
                geometry_type=geometry_type,
                subtitle="Nordic pollen and paleoecology sites",
                description=description,
                source_url=source_url,
                record_count=dataset_count,
                popup_rows=tuple(popup_rows),
            )
        )

    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))


def fetch_sead_site_rows(bbox: tuple[float, float, float, float]) -> list[dict[str, object]]:
    """Download SEAD site rows inside the Nordic bounding box."""
    min_longitude, min_latitude, max_longitude, max_latitude = bbox
    base_url = (
        "https://browser.sead.se/postgrest/tbl_sites"
        "?select=site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,"
        "altitude,site_description,site_uuid"
        f"&latitude_dd=gte.{min_latitude}"
        f"&latitude_dd=lte.{max_latitude}"
        f"&longitude_dd=gte.{min_longitude}"
        f"&longitude_dd=lte.{max_longitude}"
    )

    rows: list[dict[str, object]] = []
    start = 0
    while True:
        chunk = fetch_json(
            base_url,
            headers={
                "Range-Unit": "items",
                "Range": f"{start}-{start + SEAD_LIMIT - 1}",
            },
        )
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(chunk)
        if len(chunk) < SEAD_LIMIT:
            break
        start += SEAD_LIMIT

    deduplicated: dict[str, dict[str, object]] = {}
    for row in rows:
        deduplicated[str(row.get("site_id", ""))] = row
    return sorted(deduplicated.values(), key=lambda item: int(item.get("site_id", 0)))


def normalize_sead_rows(
    rows: Iterable[dict[str, object]],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ExternalPointRecord]:
    """Convert SEAD site rows into compact environmental archaeology records."""
    records: list[ExternalPointRecord] = []
    for row in rows:
        latitude = row.get("latitude_dd")
        longitude = row.get("longitude_dd")
        if latitude is None or longitude is None:
            continue
        country = classify_country(float(longitude), float(latitude), country_boundaries)
        if not country:
            continue
        site_id = str(row.get("site_id", "")).strip()
        site_name = str(row.get("site_name", "")).strip() or f"SEAD site {site_id}"
        national_identifier = str(row.get("national_site_identifier", "") or "").strip()
        altitude = clean_optional_text(row.get("altitude"))
        description = str(row.get("site_description", "") or "").strip()
        source_url = f"https://browser.sead.se/site/{site_id}"

        popup_rows = [
            ("Site ID", site_id),
            ("Category", "Environmental archaeology"),
            ("Source", "SEAD"),
            ("Country", country),
        ]
        if national_identifier:
            popup_rows.append(("National identifier", national_identifier))
        if altitude:
            popup_rows.append(("Altitude", altitude))
        if description:
            popup_rows.append(("Description", description))

        records.append(
            ExternalPointRecord(
                source="SEAD",
                layer_key="sead-sites",
                layer_label="SEAD sites",
                category="Environmental archaeology",
                country=country,
                record_id=site_id,
                name=site_name,
                latitude=float(latitude),
                longitude=float(longitude),
                geometry_type="Point",
                subtitle="Nordic environmental archaeology sites",
                description=description,
                source_url=source_url,
                record_count=1,
                popup_rows=tuple(popup_rows),
            )
        )

    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))


def fetch_raa_archaeology_metadata(
    country_boundaries: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Download Swedish archaeology layer metadata from RAÄ and Fornsök."""
    capabilities_url = "https://karta.raa.se/geo/arkreg_v1.0/wfs?service=WFS&request=GetCapabilities"
    schema_url = (
        "https://karta.raa.se/geo/arkreg_v1.0/wfs"
        "?service=WFS&version=2.0.0&request=DescribeFeatureType"
        "&typeNames=arkreg_v1.0:publicerade_lamningar_centrumpunkt"
    )
    domain_url = "https://app.raa.se/open/fornsok/api/lamning/domaner"

    capabilities_xml = fetch_text(capabilities_url)
    schema_xml = fetch_text(schema_url)
    domain_payload = fetch_json(domain_url)

    count_all = fetch_raa_count()
    count_fornlamning = fetch_raa_count("antikvariskbedomningtyp_namn='Fornlämning'")
    count_fornlamning_or_possible = fetch_raa_count(
        "antikvariskbedomningtyp_namn IN ('Fornlämning','Möjlig fornlämning')"
    )
    density_geojson = fetch_raa_density_geojson(country_boundaries["Sweden"])

    layer_metadata = {
        "source": "Riksantikvarieämbetet",
        "layer_key": "raa-archaeology",
        "layer_label": "RAÄ archaeology density",
        "category": "Archaeological sites",
        "country": "Sweden",
        "description": (
            "Published archaeology density derived from Fornsök/RAÄ Open Data. "
            "The map renders grid-cell counts for `Fornlämning` records so Swedish archaeology is visible "
            "at national scale without loading hundreds of thousands of point markers."
        ),
        "feature_type": "arkreg_v1.0:publicerade_lamningar_centrumpunkt",
        "grid_cell_size_degrees": 1.0,
        "density_feature_count": len(density_geojson["features"]),
        "counts": {
            "all_published_sites": count_all,
            "fornlamning": count_fornlamning,
            "fornlamning_or_possible": count_fornlamning_or_possible,
        },
        "domain_url": domain_url,
    }

    return {
        "capabilities_xml": capabilities_xml,
        "schema_xml": schema_xml,
        "domain_payload": domain_payload,
        "layer_metadata": layer_metadata,
        "density_geojson": density_geojson,
    }


def fetch_raa_count(cql_filter: str | None = None) -> int:
    """Query the Swedish archaeology WFS for an exact feature count."""
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "arkreg_v1.0:publicerade_lamningar_centrumpunkt",
        "resultType": "hits",
    }
    if cql_filter:
        params["CQL_FILTER"] = cql_filter
    xml_text = fetch_text("https://karta.raa.se/geo/arkreg_v1.0/wfs", params=params)
    marker = 'numberMatched="'
    start = xml_text.find(marker)
    if start == -1:
        raise ValueError("Could not find RAÄ count in WFS hits response")
    start += len(marker)
    end = xml_text.find('"', start)
    return int(xml_text[start:end])


def fetch_raa_density_geojson(sweden_boundary: dict[str, object]) -> dict[str, object]:
    """Build a Swedish archaeology density grid from RAÄ WFS counts."""
    geometry = sweden_boundary["features"][0]["geometry"]
    min_longitude, min_latitude, max_longitude, max_latitude = geometry_bbox(geometry)
    cell_size = 1.0
    features = []
    latitude = int(min_latitude)
    while latitude < int(max_latitude) + 1:
        longitude = int(min_longitude)
        while longitude < int(max_longitude) + 1:
            cell = build_grid_cell_geometry(
                min_longitude=float(longitude),
                min_latitude=float(latitude),
                cell_size=cell_size,
            )
            if not grid_cell_relevant(cell["coordinates"][0], geometry):
                longitude += 1
                continue
            count = fetch_raa_count(
                (
                    "BBOX(centrumpunkt,"
                    f"{longitude},{latitude},{longitude + cell_size},{latitude + cell_size},'EPSG:4326') "
                    "AND antikvariskbedomningtyp_namn='Fornlämning'"
                )
            )
            if count > 0:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": cell,
                        "properties": {
                            "layer_key": "raa-archaeology",
                            "layer_label": "RAÄ archaeology density",
                            "country": "Sweden",
                            "count": count,
                            "count_label": format_count_label(count),
                        },
                    }
                )
            longitude += 1
        latitude += 1

    return {"type": "FeatureCollection", "features": features}


def write_external_points_csv(path: Path, records: Iterable[ExternalPointRecord]) -> None:
    """Write normalized external point records as CSV."""
    fieldnames = [
        "source",
        "layer_key",
        "layer_label",
        "category",
        "country",
        "record_id",
        "name",
        "latitude",
        "longitude",
        "geometry_type",
        "subtitle",
        "description",
        "source_url",
        "record_count",
        "popup_rows_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "source": record.source,
                    "layer_key": record.layer_key,
                    "layer_label": record.layer_label,
                    "category": record.category,
                    "country": record.country,
                    "record_id": record.record_id,
                    "name": record.name,
                    "latitude": f"{record.latitude:.6f}",
                    "longitude": f"{record.longitude:.6f}",
                    "geometry_type": record.geometry_type,
                    "subtitle": record.subtitle,
                    "description": record.description,
                    "source_url": record.source_url,
                    "record_count": record.record_count,
                    "popup_rows_json": json.dumps(record.popup_rows, ensure_ascii=False),
                }
            )


def write_external_points_geojson(path: Path, records: Iterable[ExternalPointRecord]) -> None:
    """Write normalized external point records as GeoJSON."""
    features = []
    for record in records:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [record.longitude, record.latitude],
                },
                "properties": {
                    "source": record.source,
                    "layer_key": record.layer_key,
                    "layer_label": record.layer_label,
                    "category": record.category,
                    "country": record.country,
                    "record_id": record.record_id,
                    "name": record.name,
                    "geometry_type": record.geometry_type,
                    "subtitle": record.subtitle,
                    "description": record.description,
                    "source_url": record.source_url,
                    "record_count": record.record_count,
                    "popup_rows": [
                        {"label": label, "value": value}
                        for label, value in record.popup_rows
                    ],
                },
            }
        )
    write_json(path, {"type": "FeatureCollection", "features": features})


def fetch_country_boundaries() -> dict[str, dict[str, object]]:
    """Download Nordic country boundaries used for country assignment and display."""
    urls = {
        "Sweden": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/SWE.geo.json",
        "Norway": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/NOR.geo.json",
        "Finland": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/FIN.geo.json",
        "Denmark": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/DNK.geo.json",
    }
    return {
        country: fetch_json(url)
        for country, url in urls.items()
    }


def build_combined_country_boundaries(
    country_boundaries: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Combine individual Nordic country files into one GeoJSON collection."""
    features = []
    for country, payload in country_boundaries.items():
        for feature in payload.get("features", []):
            features.append(
                {
                    "type": "Feature",
                    "geometry": feature["geometry"],
                    "properties": {
                        "country": country,
                        "name": country,
                        "layer_key": "country-boundaries",
                        "layer_label": "Country boundaries",
                    },
                }
            )
    return {"type": "FeatureCollection", "features": features}


def fetch_json(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
) -> object:
    """Fetch and decode a JSON payload."""
    return json.loads(fetch_text(url, params=params, headers=headers, insecure=insecure))


def fetch_text(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
) -> str:
    """Fetch a text payload using the standard library."""
    if params:
        query = urlencode(params)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"
    request = Request(url, headers=headers or {})
    context = None
    if insecure:
        context = ssl._create_unverified_context()
    try:
        with urlopen(request, context=context) as response:
            return response.read().decode("utf-8")
    except URLError as error:
        if insecure or not isinstance(error.reason, ssl.SSLCertVerificationError):
            raise
        with urlopen(request, context=ssl._create_unverified_context()) as response:
            return response.read().decode("utf-8")


def geometry_to_representative_point(geometry: dict[str, object]) -> tuple[float, float, str] | None:
    """Reduce a GeoJSON geometry to one representative point for map display."""
    geometry_type = str(geometry.get("type", "")).strip()
    coordinates = geometry.get("coordinates")
    if coordinates is None:
        return None

    if geometry_type == "Point":
        longitude, latitude = coordinates
        return float(longitude), float(latitude), geometry_type

    flattened = flatten_positions(coordinates)
    if not flattened:
        return None

    longitudes = [position[0] for position in flattened]
    latitudes = [position[1] for position in flattened]
    return (
        (min(longitudes) + max(longitudes)) / 2,
        (min(latitudes) + max(latitudes)) / 2,
        geometry_type,
    )


def flatten_positions(coordinates: object) -> list[tuple[float, float]]:
    """Flatten nested GeoJSON coordinate arrays into lon/lat pairs."""
    if not isinstance(coordinates, list):
        return []
    if len(coordinates) >= 2 and isinstance(coordinates[0], (int, float)) and isinstance(coordinates[1], (int, float)):
        return [(float(coordinates[0]), float(coordinates[1]))]

    positions: list[tuple[float, float]] = []
    for item in coordinates:
        positions.extend(flatten_positions(item))
    return positions


def point_in_bbox(
    longitude: float,
    latitude: float,
    bbox: tuple[float, float, float, float],
) -> bool:
    """Check whether a lon/lat pair falls inside a bbox."""
    min_longitude, min_latitude, max_longitude, max_latitude = bbox
    return (
        min_longitude <= longitude <= max_longitude
        and min_latitude <= latitude <= max_latitude
    )


def classify_country(
    longitude: float,
    latitude: float,
    country_boundaries: dict[str, dict[str, object]],
) -> str:
    """Assign a point to one of the Nordic countries based on polygon containment."""
    for country, payload in country_boundaries.items():
        for feature in payload.get("features", []):
            geometry = feature.get("geometry", {})
            if isinstance(geometry, dict) and point_in_geometry(longitude, latitude, geometry):
                return country
    return ""


def point_in_geometry(longitude: float, latitude: float, geometry: dict[str, object]) -> bool:
    """Check whether a point falls inside a GeoJSON Polygon or MultiPolygon."""
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        return point_in_polygon(longitude, latitude, coordinates)
    if geometry_type == "MultiPolygon":
        return any(point_in_polygon(longitude, latitude, polygon) for polygon in coordinates)
    return False


def point_in_polygon(longitude: float, latitude: float, polygon: list[object]) -> bool:
    """Ray-casting point-in-polygon with support for holes."""
    if not polygon:
        return False
    if not point_in_ring(longitude, latitude, polygon[0]):
        return False
    for hole in polygon[1:]:
        if point_in_ring(longitude, latitude, hole):
            return False
    return True


def point_in_ring(longitude: float, latitude: float, ring: list[object]) -> bool:
    """Return True when a point is inside a linear ring."""
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous[0], previous[1]
        x2, y2 = current[0], current[1]
        crosses = ((y1 > latitude) != (y2 > latitude)) and (
            longitude < (x2 - x1) * (latitude - y1) / ((y2 - y1) or 1e-12) + x1
        )
        if crosses:
            inside = not inside
        previous = current
    return inside


def geometry_bbox(geometry: dict[str, object]) -> tuple[float, float, float, float]:
    """Return the bounding box of a GeoJSON geometry."""
    flattened = flatten_positions(geometry.get("coordinates", []))
    longitudes = [position[0] for position in flattened]
    latitudes = [position[1] for position in flattened]
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def build_grid_cell_geometry(
    min_longitude: float,
    min_latitude: float,
    cell_size: float,
) -> dict[str, object]:
    """Build a rectangular polygon used for density aggregation."""
    max_longitude = min_longitude + cell_size
    max_latitude = min_latitude + cell_size
    return {
        "type": "Polygon",
        "coordinates": [[
            [min_longitude, min_latitude],
            [max_longitude, min_latitude],
            [max_longitude, max_latitude],
            [min_longitude, max_latitude],
            [min_longitude, min_latitude],
        ]],
    }


def grid_cell_relevant(ring: list[object], geometry: dict[str, object]) -> bool:
    """Keep a density cell when its center or corners overlap the Sweden boundary."""
    center_longitude = (ring[0][0] + ring[2][0]) / 2
    center_latitude = (ring[0][1] + ring[2][1]) / 2
    if point_in_geometry(center_longitude, center_latitude, geometry):
        return True
    return any(point_in_geometry(point[0], point[1], geometry) for point in ring[:-1])


def format_count_label(count: int) -> str:
    """Render archaeology density counts in a compact human-readable form."""
    return f"{count:,}"


def slugify(value: str) -> str:
    """Convert a label into a stable file slug."""
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def clean_optional_text(value: object) -> str:
    """Normalize optional text values used in normalized exports."""
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"", "null", "None"} else text


def write_json(path: Path, payload: object) -> None:
    """Write JSON with stable formatting."""
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text content."""
    path.write_text(content, encoding="utf-8")
