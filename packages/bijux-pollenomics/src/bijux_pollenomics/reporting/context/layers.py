"""Build explicit source and opt-in aggregate context layers."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ..geography import GeographicScope
from ..map_publication import map_allows_fieldwork_layer
from ..models import SampleRecord
from .artifacts import stage_context_point_layers, stage_context_polygon_layers
from .nordic_point_inputs import NordicPointInputs
from .nordic_polygon_inputs import NordicPolygonInputs
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
from .raa_native import NativeRegistryContextSnapshot

__all__ = [
    "build_context_layers",
    "build_external_point_layer",
    "build_external_polygon_layer",
]


def build_context_layers(
    samples: Iterable[SampleRecord],
    version: str,
    output_dir: Path,
    context_root: Path | None,
    geography_scope: GeographicScope | None = None,
    published_output_dir: Path | None = None,
    *,
    native_registry_context: NativeRegistryContextSnapshot | None = None,
    nordic_point_inputs: NordicPointInputs | None = None,
    nordic_polygon_inputs: NordicPolygonInputs | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[tuple[str, str]]]:
    """Build embedded point layers and service-backed overlays for the shared map."""
    scope_key = "custom" if geography_scope is None else geography_scope.key
    point_layers = [build_aadr_point_layer(samples, version=version)]
    polygon_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []

    fieldwork_layer = (
        build_fieldwork_point_layer(
            output_dir,
            published_output_dir=published_output_dir,
        )
        if map_allows_fieldwork_layer(scope_key=scope_key)
        else None
    )
    if fieldwork_layer is not None:
        point_layers.append(fieldwork_layer)

    if nordic_point_inputs is not None and context_root is None:
        raise ValueError("Nordic point capture requires context")
    if context_root is not None:
        context_root = Path(context_root)
        external_point_layers, point_artifacts = stage_context_point_layers(
            scope_key=scope_key,
            context_root=context_root,
            output_dir=output_dir,
            build_external_point_layer_fn=build_external_point_layer,
            **(
                {"nordic_point_inputs": nordic_point_inputs}
                if nordic_point_inputs is not None
                else {}
            ),
        )
        point_layers.extend(external_point_layers)
        extra_artifacts.extend(point_artifacts)
    external_polygon_layers, polygon_artifacts = stage_context_polygon_layers(
        scope_key=scope_key,
        context_root=context_root,
        output_dir=output_dir,
        build_country_boundary_layer_fn=build_country_boundary_layer,
        build_density_polygon_layer_fn=build_density_polygon_layer,
        build_external_polygon_layer_fn=build_external_polygon_layer,
        native_registry_context=native_registry_context,
        **(
            {"nordic_polygon_inputs": nordic_polygon_inputs}
            if nordic_polygon_inputs is not None
            else {}
        ),
    )
    polygon_layers.extend(external_polygon_layers)
    extra_artifacts.extend(polygon_artifacts)

    return point_layers, polygon_layers, extra_artifacts


def require_capture_owner(
    context_root: Path | None,
    builder: object,
    point: NordicPointInputs | None,
    polygon: NordicPolygonInputs | None,
) -> None:
    """Keep selected captures on the maintained context path."""
    if context_root is None or builder is not build_context_layers:
        if point is not None:
            raise ValueError(
                "Nordic point capture requires the maintained context owner"
            )
        if polygon is not None:
            raise ValueError(
                "Nordic polygon capture requires the maintained context owner"
            )


def selected_capture_options(
    point: NordicPointInputs | None, polygon: NordicPolygonInputs | None
) -> dict[str, object]:
    """Forward only explicitly selected captures to the context owner."""
    return {
        key: value
        for key, value in (
            ("nordic_point_inputs", point),
            ("nordic_polygon_inputs", polygon),
        )
        if value is not None
    }
