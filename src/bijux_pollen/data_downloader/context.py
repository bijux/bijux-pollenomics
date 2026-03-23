from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Iterable

from .boundaries import build_combined_country_boundaries, fetch_country_boundaries
from .common import slugify, write_json, write_text
from .models import ContextDataReport, ContextPointRecord
from .neotoma import fetch_neotoma_pollen_rows, normalize_neotoma_rows
from .raa import fetch_raa_archaeology_metadata
from .sead import fetch_sead_site_rows, normalize_sead_rows


NORDIC_BBOX = (4.0, 54.0, 35.0, 72.0)


def collect_context_data(output_root: Path) -> ContextDataReport:
    """Download and normalize archaeology, pollen, and boundary datasets."""
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
        write_json(boundaries_raw_dir / f"{slugify(country_name)}.geojson", payload)
    write_json(
        boundaries_norm_dir / "nordic_country_boundaries.geojson",
        build_combined_country_boundaries(country_boundaries),
    )

    neotoma_rows = fetch_neotoma_pollen_rows()
    write_json(
        neotoma_raw_dir / "neotoma_pollen_sites.json",
        {
            "generated_on": str(date.today()),
            "source": "Neotoma",
            "endpoint": "https://api.neotomadb.org/v2.0/data/sites?datasettype=pollen",
            "row_count": len(neotoma_rows),
            "rows": neotoma_rows,
        },
    )
    neotoma_records = normalize_neotoma_rows(
        neotoma_rows,
        bbox=NORDIC_BBOX,
        country_boundaries=country_boundaries,
    )
    write_context_points_csv(neotoma_norm_dir / "nordic_pollen_sites.csv", neotoma_records)
    write_context_points_geojson(neotoma_norm_dir / "nordic_pollen_sites.geojson", neotoma_records)

    sead_rows = fetch_sead_site_rows(bbox=NORDIC_BBOX)
    write_json(
        sead_raw_dir / "nordic_sites.json",
        {
            "generated_on": str(date.today()),
            "source": "SEAD",
            "endpoint": "https://browser.sead.se/postgrest/tbl_sites",
            "row_count": len(sead_rows),
            "rows": sead_rows,
        },
    )
    sead_records = normalize_sead_rows(sead_rows, country_boundaries=country_boundaries)
    write_context_points_csv(sead_norm_dir / "nordic_environmental_sites.csv", sead_records)
    write_context_points_geojson(sead_norm_dir / "nordic_environmental_sites.geojson", sead_records)

    raa_metadata = fetch_raa_archaeology_metadata(country_boundaries=country_boundaries)
    write_text(raa_raw_dir / "arkreg_v1_0_wfs_capabilities.xml", raa_metadata["capabilities_xml"])
    write_text(raa_raw_dir / "publicerade_lamningar_centrumpunkt_schema.xml", raa_metadata["schema_xml"])
    write_json(raa_raw_dir / "fornsok_domains.json", raa_metadata["domain_payload"])
    write_json(raa_norm_dir / "sweden_archaeology_layer.json", raa_metadata["layer_metadata"])
    write_json(raa_norm_dir / "sweden_archaeology_density.geojson", raa_metadata["density_geojson"])

    return ContextDataReport(
        generated_on=str(date.today()),
        output_root=output_root,
        neotoma_point_count=len(neotoma_records),
        sead_point_count=len(sead_records),
        raa_total_site_count=raa_metadata["layer_metadata"]["counts"]["all_published_sites"],
        raa_heritage_site_count=raa_metadata["layer_metadata"]["counts"]["fornlamning"],
    )


def write_context_points_csv(path: Path, records: Iterable[ContextPointRecord]) -> None:
    """Write normalized context point records as CSV."""
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


def write_context_points_geojson(path: Path, records: Iterable[ContextPointRecord]) -> None:
    """Write normalized context point records as GeoJSON."""
    features = []
    for record in records:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [record.longitude, record.latitude]},
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
