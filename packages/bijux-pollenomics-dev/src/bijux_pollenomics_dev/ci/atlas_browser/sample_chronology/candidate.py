"""Render source-owned disconnected supports through production static assets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, cast

from bijux_pollenomics.reporting.map_document.render import write_static_map_document
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.indexes import build_indexes
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_occurrence_intervals,
)
from bijux_pollenomics.reporting.map_publication import MapScopePolicy

from ..candidate_files import regular_bytes
from ..source_custody import observed_source_inputs
from .source_rows import GAP_BP, load_source_features


def generate_candidate(repository: Path, destination: Path) -> dict[str, Any]:
    """Use original date fields and unknowns; qualify selection software only."""
    repository, destination = repository.absolute(), destination.absolute()
    if (
        ".." in destination.parts
        or not destination.is_relative_to(repository / "artifacts")
        or destination == repository / "artifacts"
        or destination.exists()
        or any(path.is_symlink() for path in (destination, *destination.parents))
    ):
        raise ValueError(
            "Sample chronology candidate needs an absent confined artifact destination"
        )
    features, inputs, source_records = load_source_features(repository)
    intervals = feature_occurrence_intervals(features[0])
    if any(start <= GAP_BP + 1 and end >= GAP_BP for start, end in intervals):
        raise ValueError("Frozen source control must retain its disconnected gap")
    layer = {
        "key": "sample-owned-chronology",
        "label": "Published sample chronology",
        "style": {"fill": "#2563eb", "stroke": "#1d4ed8"},
        "group": "human-context",
        "default_enabled": True,
        "applies_time_filter": True,
        "features": features,
    }
    index = build_indexes([layer])
    components = index["time_interval_feature_indexes"]
    if not isinstance(components, list) or len(components) < 2:
        raise ValueError("Frozen source control must retain multiple dated components")
    queries = [
        {
            "label": "disjoint-source-gap",
            "start_bp": GAP_BP,
            "end_bp": GAP_BP + 1,
            "expected_visible_features": 0,
        }
    ]
    for number, component in enumerate(components):
        if not isinstance(component, list):
            raise ValueError("Source component index is malformed")
        younger = int(component[0])
        older = int(component[1])
        start = min(younger + 1, older)
        queries.append(
            {
                "label": f"dated-source-component-{number + 1}",
                "start_bp": start,
                "end_bp": start + 1,
                "expected_visible_features": 1,
            }
        )
    policy = MapScopePolicy(
        key="sample-chronology",
        label="Published sample chronology",
        eyebrow_label="Source context",
        summary="Sample-owned temporal supports; no new source age admission.",
        bounds_summary="Original source coordinates",
        default_basemap="none",
        initial_diameter_km=0,
        minimum_bounds=((54.0, 10.0), (61.0, 15.0)),
        filter_surfaces=(),
        legend_sections=(),
        visible_caveats=(
            "Published export date fields only; unresolved chronology is not time zero.",
            "Disconnected source supports do not date the intervening locality hull.",
        ),
        engine_summary="No reconstruction or date conversion",
    )
    destination.mkdir(parents=True)
    assets = write_static_atlas_assets(
        destination,
        slug="sample-chronology",
        version="published-v66",
        point_layers=[layer],
        polygon_layers=[],
    )
    html_path, _ = write_static_map_document(
        destination / "index.html",
        "Sample-owned chronology",
        "published-v66",
        "2026-10-14",
        ("Sweden", "Denmark"),
        policy,
        [layer],
        [],
        "./_map_assets",
        static_assets=assets,
    )
    map_assets = (
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map"
    )
    for path in sorted(map_assets.rglob("*")):
        if path.is_file():
            inputs[path.relative_to(repository).as_posix()] = hashlib.sha256(
                regular_bytes(path)
            ).hexdigest()
    shutil.copytree(map_assets, destination / "_map_assets")
    source_path = (
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document"
    )
    for path in sorted(source_path.rglob("*")):
        if path.is_file() and path.suffix in {".py", ".html", ".js"}:
            inputs[path.relative_to(repository).as_posix()] = hashlib.sha256(
                regular_bytes(path)
            ).hexdigest()
    (destination / "sample-support.json").write_text(
        json.dumps(
            {
                "schema_version": "atlas-published-sample-support.v1",
                "records": source_records,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    own_source = Path(__file__).absolute()
    inputs[own_source.relative_to(repository).as_posix()] = hashlib.sha256(
        regular_bytes(own_source)
    ).hexdigest()
    inputs.update(observed_source_inputs(repository))
    receipt = {
        "schema_version": "atlas-sample-owned-chronology-candidate.v1",
        "inputs_sha256": dict(sorted(inputs.items())),
        "source_records": source_records,
        "queries": queries,
        "dated_feature_count": 1,
        "undated_feature_count": 1,
        "candidate_build_id": assets.manifest["build_id"],
        "candidate_document_sha256": hashlib.sha256(html_path.read_bytes()).hexdigest(),
        "component_index_schema": cast(
            dict[str, Any], assets.manifest["compatibility"]
        )["index_schema"],
        "scientific_posture": "Published sample date fields only; missing chronology stays unknown, locality hull is display-only. No new raw-source authentication, review, epoch conversion, calibration, event, biological absence or propagation claim.",
    }
    for relative_path, digest in inputs.items():
        if (
            hashlib.sha256(regular_bytes(repository / relative_path)).hexdigest()
            != digest
        ):
            raise ValueError(
                "Sample chronology candidate input changed during generation"
            )
    (destination / "generation.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> None:
    """Generate the declared sample chronology atlas candidate."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    generate_candidate(args.repository, args.destination)


if __name__ == "__main__":
    main()
