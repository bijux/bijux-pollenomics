from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..models import SampleRecord
from .artifacts import stage_context_point_layers, stage_context_polygon_layers
from .points import (
    build_aadr_point_layer,
    build_external_point_layer,
    build_fieldwork_point_layer,
)
from .polygons import (
    build_country_boundary_layer,
    build_density_polygon_layer,
    build_external_polygon_layer,
)

__all__ = [
    "build_context_layers",
    "build_external_point_layer",
    "build_external_polygon_layer",
]


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
    external_point_layers, point_artifacts = stage_context_point_layers(
        context_root=context_root,
        output_dir=output_dir,
        build_external_point_layer_fn=build_external_point_layer,
    )
    point_layers.extend(external_point_layers)
    extra_artifacts.extend(point_artifacts)
    external_polygon_layers, polygon_artifacts = stage_context_polygon_layers(
        context_root=context_root,
        output_dir=output_dir,
        build_country_boundary_layer_fn=build_country_boundary_layer,
        build_density_polygon_layer_fn=build_density_polygon_layer,
        build_external_polygon_layer_fn=build_external_polygon_layer,
    )
    polygon_layers.extend(external_polygon_layers)
    extra_artifacts.extend(polygon_artifacts)

    return point_layers, polygon_layers, extra_artifacts
