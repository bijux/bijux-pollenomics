from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .common import fetch_json, fetch_text
from .geometry import build_grid_cell_geometry, geometry_bbox, grid_cell_relevant
from .common import write_json, write_text


@dataclass(frozen=True)
class RaaDataReport:
    output_dir: Path
    total_site_count: int
    heritage_site_count: int
    metadata_path: Path
    density_path: Path


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


def format_count_label(count: int) -> str:
    """Render archaeology density counts in a compact human-readable form."""
    return f"{count:,}"


def collect_raa_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
) -> RaaDataReport:
    """Download and write the RAÄ dataset under data/raa."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    metadata = fetch_raa_archaeology_metadata(country_boundaries=country_boundaries)
    write_text(raw_dir / "arkreg_v1_0_wfs_capabilities.xml", metadata["capabilities_xml"])
    write_text(raw_dir / "publicerade_lamningar_centrumpunkt_schema.xml", metadata["schema_xml"])
    write_json(raw_dir / "fornsok_domains.json", metadata["domain_payload"])
    metadata_path = normalized_dir / "sweden_archaeology_layer.json"
    density_path = normalized_dir / "sweden_archaeology_density.geojson"
    write_json(metadata_path, metadata["layer_metadata"])
    write_json(density_path, metadata["density_geojson"])

    return RaaDataReport(
        output_dir=output_root,
        total_site_count=metadata["layer_metadata"]["counts"]["all_published_sites"],
        heritage_site_count=metadata["layer_metadata"]["counts"]["fornlamning"],
        metadata_path=metadata_path,
        density_path=density_path,
    )
