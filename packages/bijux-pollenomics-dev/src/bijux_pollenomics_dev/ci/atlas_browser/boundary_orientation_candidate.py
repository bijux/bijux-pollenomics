"""Render controlled boundary geometry through the production atlas document."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, cast

from bijux_pollenomics.core.geospatial.geojson import JsonObject
from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.scope_policy import MAP_SCOPE_POLICIES

COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
RECTANGLES = {
    "Denmark": (9.0, 55.0, 11.0, 57.0),
    "Finland": (24.0, 61.0, 26.0, 63.0),
    "Norway": (8.0, 61.0, 10.0, 63.0),
    "Sweden": (17.0, 58.0, 19.0, 60.0),
}


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def boundary_layers() -> list[dict[str, Any]]:
    """Schematic boxes exercise orientation rendering without source claims."""
    features = []
    for country, (west, south, east, north) in RECTANGLES.items():
        features.append(
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
                "properties": {"country": country, "controlled_geometry": True},
            }
        )
    return [
        {
            "key": "country-boundaries",
            "kind": "country-boundaries",
            "label": "Controlled country outlines",
            "group": "orientation",
            "source_name": "Controlled schematic geometry",
            "coverage_label": "Schematic rectangles only; no admitted national boundary geometry.",
            "default_enabled": True,
            "geojson": {"type": "FeatureCollection", "features": features},
        }
    ]


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
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/scope_policy.py",
        repository
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/boundary_orientation_candidate.py",
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

    layers = boundary_layers()
    destination.mkdir(parents=True)
    document = render_multi_country_map_html(
        "Controlled boundary orientation fixture",
        "controlled-boundary-orientation",
        "2026-09-28",
        COUNTRIES,
        MAP_SCOPE_POLICIES["nordic"],
        [],
        cast(list[JsonObject], layers),
        "./_map_assets",
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
    geometry = layers[0]["geojson"]
    manifest = {
        "schema_version": "atlas-controlled-boundary-candidate.v1",
        "status": "controlled_synthetic_geometry_only",
        "scientific_admission": "not_evaluated",
        "countries": list(COUNTRIES),
        "polygon_count": len(geometry["features"]),
        "geometry_sha256": digest(
            json.dumps(geometry, sort_keys=True, separators=(",", ":")).encode()
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
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "polygon_count": manifest["polygon_count"],
            }
        )
    )


if __name__ == "__main__":
    main()
