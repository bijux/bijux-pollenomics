"""Render controlled BP chronology for production atlas keyboard playback checks."""

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

from .boundary_orientation_candidate import COUNTRIES, boundary_layers


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fixture_points() -> list[dict[str, Any]]:
    """Use explicit fixture BP intervals; no source chronology is inferred."""
    records = (
        ("Denmark", 56.0, 10.0, 0),
        ("Finland", 62.0, 25.0, 150),
        ("Sweden", 59.0, 18.0, 300),
    )
    return [
        {
            "record_id": f"controlled:bp:{bp}",
            "label": f"Controlled {bp} BP point",
            "latitude": latitude,
            "longitude": longitude,
            "country": country,
            "age_type": "calendar_bp",
            "time_start_bp": bp,
            "time_end_bp": bp,
            "fixture_status": "controlled_bp_chronology_only",
        }
        for country, latitude, longitude, bp in records
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
        repository
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/playback_keyboard_candidate.py",
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

    points = fixture_points()
    layers = [
        {
            "key": "controlled-bp-points",
            "kind": "point",
            "label": "Controlled BP points",
            "group": "environmental-context",
            "source_name": "Controlled BP fixture",
            "coverage_label": "Three fixture point ages; no scientific admission.",
            "semantic_role": "controlled_fixture_context",
            "default_enabled": True,
            "applies_time_filter": True,
            "applies_country_filter": True,
            "circle_enabled": False,
            "style": {"fill": "#334155", "stroke": "#0f172a"},
            "features": points,
        }
    ]
    destination.mkdir(parents=True)
    document = render_multi_country_map_html(
        "Controlled BP playback fixture",
        "controlled-bp-playback",
        "2026-09-28",
        COUNTRIES,
        MAP_SCOPE_POLICIES["nordic"],
        cast(list[JsonObject], layers),
        cast(list[JsonObject], boundary_layers()),
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
    manifest = {
        "schema_version": "atlas-controlled-playback-candidate.v1",
        "status": "controlled_bp_chronology_only",
        "scientific_admission": "not_evaluated",
        "geometry_status": "controlled_schematic_rectangles_only",
        "countries": list(COUNTRIES),
        "fixture_bp_values": [point["time_start_bp"] for point in points],
        "fixture_sha256": digest(
            json.dumps(points, sort_keys=True, separators=(",", ":")).encode()
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
                "fixture_bp_values": manifest["fixture_bp_values"],
            }
        )
    )


if __name__ == "__main__":
    main()
