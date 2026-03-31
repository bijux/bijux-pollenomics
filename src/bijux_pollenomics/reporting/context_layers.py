from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Iterable

from ..data_downloader.contracts import (
    ATLAS_POINT_ARTIFACTS,
    BOUNDARY_COLLECTION,
    LANDCLIM_GRID_GEOJSON,
    RAA_DENSITY_GEOJSON,
    RAA_LAYER_METADATA,
)
from .context_point_layers import build_aadr_point_layer, build_external_point_layer, build_fieldwork_point_layer
from .context_polygon_layers import (
    build_country_boundary_layer,
    build_density_polygon_layer,
    build_external_polygon_layer,
)
from .models import SampleRecord

__all__ = ["build_context_layers", "build_external_point_layer", "build_external_polygon_layer"]


def build_context_layers(
    samples: Iterable[SampleRecord],
    output_dir: Path,
    context_root: Path | None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[tuple[str, str]]]:
    """Build embedded point layers and service-backed overlays for the shared map."""
    point_layers = [build_aadr_point_layer(samples)]
    polygon_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []

    fieldwork_layer = build_fieldwork_point_layer(output_dir)
    if fieldwork_layer is not None:
        point_layers.append(fieldwork_layer)

    if context_root is None:
        return point_layers, polygon_layers, extra_artifacts

    context_root = Path(context_root)
    for contract in ATLAS_POINT_ARTIFACTS:
        source_path = contract.path_under(context_root)
        if not source_path.exists():
            continue
        destination_path = output_dir / source_path.name
        shutil.copyfile(source_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        point_layers.append(build_external_point_layer(geojson, source_path=destination_path))
        extra_artifacts.append((contract.label, destination_path.name))

    boundary_path = BOUNDARY_COLLECTION.path_under(context_root)
    if boundary_path.exists():
        destination_path = output_dir / boundary_path.name
        shutil.copyfile(boundary_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_country_boundary_layer(geojson))
        extra_artifacts.append((BOUNDARY_COLLECTION.label, destination_path.name))

    landclim_grid_path = LANDCLIM_GRID_GEOJSON.path_under(context_root)
    if landclim_grid_path.exists():
        destination_path = output_dir / landclim_grid_path.name
        shutil.copyfile(landclim_grid_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_external_polygon_layer(geojson, source_path=destination_path))
        extra_artifacts.append((LANDCLIM_GRID_GEOJSON.label, destination_path.name))

    archaeology_path = RAA_LAYER_METADATA.path_under(context_root)
    archaeology_density_path = RAA_DENSITY_GEOJSON.path_under(context_root)
    if archaeology_path.exists():
        destination_path = output_dir / archaeology_path.name
        shutil.copyfile(archaeology_path, destination_path)
        extra_artifacts.append((RAA_LAYER_METADATA.label, destination_path.name))
    if archaeology_density_path.exists():
        destination_path = output_dir / archaeology_density_path.name
        shutil.copyfile(archaeology_density_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_density_polygon_layer(geojson))
        extra_artifacts.append((RAA_DENSITY_GEOJSON.label, destination_path.name))

    return point_layers, polygon_layers, extra_artifacts
