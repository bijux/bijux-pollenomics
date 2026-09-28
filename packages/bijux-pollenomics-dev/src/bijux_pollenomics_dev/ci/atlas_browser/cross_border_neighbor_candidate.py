"""Render a controlled cross-border relation through the production atlas."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, cast

from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic
from bijux_pollenomics.core.geospatial.geojson import JsonObject
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.scope_policy import MAP_SCOPE_POLICIES

COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
POINTS = (
    ("controlled:no:older", "Norway", 63.0, 12.0, 200),
    ("controlled:se:younger", "Sweden", 63.0, 13.0, 100),
)
RECTANGLES = {
    "Denmark": (9.0, 55.0, 11.0, 57.0),
    "Finland": (24.0, 61.0, 26.0, 63.0),
    "Norway": (11.5, 62.5, 12.5, 63.5),
    "Sweden": (12.5, 62.5, 13.5, 63.5),
}


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fixture_layers() -> tuple[list[JsonObject], list[JsonObject]]:
    point_features = [
        {
            "record_id": record_id,
            "title": f"Controlled {country} event",
            "subtitle": "Controlled cross-border fixture",
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "age_type": "calendar_bp",
            "time_start_bp": age,
            "time_end_bp": age,
            "scientific_signal_ids": ["fixture:whole"],
            "fixture_status": "controlled_cross_border_only",
        }
        for record_id, country, latitude, longitude, age in POINTS
    ]
    point_layers = [
        {
            "key": "controlled-cross-border-points",
            "kind": "point",
            "label": "Controlled relation endpoints",
            "description": "Two schematic dated event points",
            "group": "environmental-context",
            "source_name": "Controlled fixture",
            "coverage_label": "No admitted source evidence.",
            "default_enabled": True,
            "applies_time_filter": True,
            "applies_country_filter": True,
            "scientific_selection_enabled": True,
            "circle_enabled": False,
            "style": {"fill": "#475569", "stroke": "#1e293b"},
            "features": point_features,
        }
    ]
    boundary_features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [west, south],
                        [east, south],
                        [east, north],
                        [west, north],
                        [west, south],
                    ]
                ],
            },
            "properties": {"country": country, "name": f"Controlled {country} outline"},
        }
        for country, (west, south, east, north) in RECTANGLES.items()
    ]
    polygon_layers = [
        {
            "key": "controlled-country-outlines",
            "kind": "country-boundaries",
            "label": "Controlled schematic outlines",
            "group": "orientation",
            "source_name": "Controlled fixture",
            "coverage_label": "Schematic boxes only, not national boundaries.",
            "default_enabled": True,
            "geojson": {"type": "FeatureCollection", "features": boundary_features},
        }
    ]
    return cast(list[JsonObject], point_layers), cast(list[JsonObject], polygon_layers)


def fixture_edges() -> list[JsonObject]:
    return cast(
        list[JsonObject],
        [
            {
                "edge_id": "controlled:no-to-se",
                "signal_id": "fixture:whole",
                "source_record_id": "controlled:no:older",
                "target_record_id": "controlled:se:younger",
                "source_country": "Norway",
                "target_country": "Sweden",
                "status": "definite_candidate",
                "predicates": [
                    {
                        "predicate": "distance_within_threshold",
                        "status": "fixture_pass",
                    },
                    {"predicate": "lag_within_threshold", "status": "fixture_pass"},
                ],
            }
        ],
    )


def generate_candidate(repository: Path, destination: Path) -> dict[str, Any]:
    repository, destination = repository.resolve(), destination.resolve()
    if not destination.is_relative_to(repository / "artifacts"):
        raise ValueError("candidate must be generated under repository artifacts")
    if destination.exists():
        raise ValueError("candidate destination must be absent")
    source_roots = (
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document",
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/modeled_context",
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map",
    )
    source_files = [
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/core/geospatial/distance.py",
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/scope_policy.py",
        repository
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/cross_border_neighbor_candidate.py",
    ]
    for root in source_roots:
        source_files.extend(path for path in root.rglob("*") if path.is_file())
    inputs: dict[str, str] = {}
    for path in sorted(source_files):
        if "__pycache__" in path.parts:
            continue
        if path.is_symlink():
            raise ValueError(f"symbolic candidate input: {path}")
        inputs[path.relative_to(repository).as_posix()] = digest(path.read_bytes())

    point_layers, polygon_layers = fixture_layers()
    edges = fixture_edges()
    source, target = POINTS
    distance = wgs84_inverse_geodesic(
        latitude_a=source[2],
        longitude_a=source[3],
        latitude_b=target[2],
        longitude_b=target[3],
    )
    lag_years = source[4] - target[4]
    if not 0 < distance.distance_km_unrounded < 100 or not 0 < lag_years <= 100:
        raise ValueError("controlled cross-border fixture is outside its declared rule")
    signals: list[JsonObject] = [
        {
            "signal_id": "fixture:whole",
            "feature_key": "fixture:whole",
            "label": "Controlled relation fixture",
            "resolution": "whole",
            "status": "accepted",
        }
    ]
    destination.mkdir(parents=True)
    assets = write_static_atlas_assets(
        destination,
        slug="cross-border-neighbor",
        version="controlled-cross-border",
        point_layers=point_layers,
        polygon_layers=polygon_layers,
        scientific_signals=signals,
        edge_records=edges,
    )
    document = render_multi_country_map_html(
        "Controlled cross-border neighbor fixture",
        "controlled-cross-border",
        "2026-09-28",
        COUNTRIES,
        MAP_SCOPE_POLICIES["nordic"],
        point_layers,
        polygon_layers,
        "./_map_assets",
        static_assets=assets,
    )
    (destination / "index.html").write_text(document, encoding="utf-8")
    shutil.copytree(
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map",
        destination / "_map_assets",
    )
    outputs = {
        path.relative_to(destination).as_posix(): digest(path.read_bytes())
        for path in sorted(destination.rglob("*"))
        if path.is_file()
    }
    for name, original in inputs.items():
        if digest((repository / name).read_bytes()) != original:
            raise ValueError(f"candidate input changed during generation: {name}")
    manifest = {
        "schema_version": "atlas-controlled-cross-border-candidate.v1",
        "status": "controlled_cross_border_only",
        "scientific_admission": "not_evaluated",
        "geometry_status": "controlled_schematic_rectangles_only",
        "countries": list(COUNTRIES),
        "point_record_ids": [point[0] for point in POINTS],
        "edge_ids": [edge["edge_id"] for edge in edges],
        "edge_relation": {
            "source_record_id": source[0],
            "source_country": source[1],
            "target_record_id": target[0],
            "target_country": target[1],
            "cross_border": True,
            "lag_years": lag_years,
            "wgs84_distance_km": distance.distance_km_unrounded,
        },
        "fixture_sha256": digest(
            json.dumps(
                {"points": point_layers, "polygons": polygon_layers, "edges": edges},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ),
        "inputs_sha256": inputs,
        "outputs_sha256": outputs,
    }
    (destination / "generation.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    manifest = generate_candidate(args.repository, args.destination)
    print(json.dumps({"status": manifest["status"], "edge_ids": manifest["edge_ids"]}))


if __name__ == "__main__":
    main()
