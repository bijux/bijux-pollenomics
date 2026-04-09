from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import shutil

from ...core.geojson import as_mapping
from ...data_downloader.contracts import (
    ATLAS_POINT_ARTIFACTS,
    BOUNDARY_COLLECTION,
    LANDCLIM_GRID_GEOJSON,
    RAA_DENSITY_GEOJSON,
    RAA_LAYER_METADATA,
)

__all__ = ["stage_context_point_layers", "stage_context_polygon_layers"]


def stage_context_point_layers(
    *,
    context_root: Path,
    output_dir: Path,
    build_external_point_layer_fn: Callable[..., dict[str, object]],
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    """Copy external point layers into the bundle and return rendered layer configs."""
    point_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []
    for contract in ATLAS_POINT_ARTIFACTS:
        source_path = contract.path_under(context_root)
        if not source_path.exists():
            continue
        destination_path = stage_context_artifact(
            source_path=source_path, output_dir=output_dir
        )
        geojson = load_context_geojson(destination_path)
        point_layers.append(
            build_external_point_layer_fn(geojson, source_path=destination_path)
        )
        extra_artifacts.append((contract.label, destination_path.name))
    return point_layers, extra_artifacts


def stage_context_polygon_layers(
    *,
    context_root: Path,
    output_dir: Path,
    build_country_boundary_layer_fn: Callable[[dict[str, object]], dict[str, object]],
    build_density_polygon_layer_fn: Callable[[dict[str, object]], dict[str, object]],
    build_external_polygon_layer_fn: Callable[..., dict[str, object]],
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    """Copy external polygon layers into the bundle and return rendered layer configs."""
    polygon_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []

    boundary_path = BOUNDARY_COLLECTION.path_under(context_root)
    if boundary_path.exists():
        destination_path = stage_context_artifact(
            source_path=boundary_path, output_dir=output_dir
        )
        polygon_layers.append(
            build_country_boundary_layer_fn(load_context_geojson(destination_path))
        )
        extra_artifacts.append((BOUNDARY_COLLECTION.label, destination_path.name))

    landclim_grid_path = LANDCLIM_GRID_GEOJSON.path_under(context_root)
    if landclim_grid_path.exists():
        destination_path = stage_context_artifact(
            source_path=landclim_grid_path, output_dir=output_dir
        )
        polygon_layers.append(
            build_external_polygon_layer_fn(
                load_context_geojson(destination_path), source_path=destination_path
            )
        )
        extra_artifacts.append((LANDCLIM_GRID_GEOJSON.label, destination_path.name))

    archaeology_path = RAA_LAYER_METADATA.path_under(context_root)
    if archaeology_path.exists():
        destination_path = stage_context_artifact(
            source_path=archaeology_path, output_dir=output_dir
        )
        extra_artifacts.append((RAA_LAYER_METADATA.label, destination_path.name))

    archaeology_density_path = RAA_DENSITY_GEOJSON.path_under(context_root)
    if archaeology_density_path.exists():
        destination_path = stage_context_artifact(
            source_path=archaeology_density_path, output_dir=output_dir
        )
        polygon_layers.append(
            build_density_polygon_layer_fn(load_context_geojson(destination_path))
        )
        extra_artifacts.append((RAA_DENSITY_GEOJSON.label, destination_path.name))

    return polygon_layers, extra_artifacts


def stage_context_artifact(*, source_path: Path, output_dir: Path) -> Path:
    """Copy one context artifact into the atlas bundle and return the staged path."""
    destination_path = output_dir / source_path.name
    shutil.copyfile(source_path, destination_path)
    return destination_path


def load_context_geojson(path: Path) -> dict[str, object]:
    """Load one staged GeoJSON artifact."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping = as_mapping(payload)
    if mapping is None:
        raise ValueError(f"Context GeoJSON must be a JSON object: {path}")
    return {str(key): value for key, value in mapping.items()}
