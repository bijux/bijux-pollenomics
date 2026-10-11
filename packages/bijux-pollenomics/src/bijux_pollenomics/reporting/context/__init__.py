"""Context-layer staging and validation surface for map publication."""

from .artifacts import stage_context_point_layers, stage_context_polygon_layers
from .layers import build_context_layers
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
from .raa import (
    RAA_ATLAS_INPUT_STATUS_FILENAME,
    build_raa_atlas_input_status,
)
from .time import (
    extract_layer_identity,
    feature_has_time,
    feature_time_payload,
    normalize_media_links,
    validate_feature_collection,
)

__all__ = [
    "RAA_ATLAS_INPUT_STATUS_FILENAME",
    "build_aadr_point_layer",
    "build_context_layers",
    "build_country_boundary_layer",
    "build_density_polygon_layer",
    "build_external_point_layer",
    "build_external_polygon_layer",
    "build_fieldwork_point_layer",
    "build_raa_atlas_input_status",
    "extract_layer_identity",
    "feature_has_time",
    "feature_time_payload",
    "normalize_media_links",
    "stage_context_point_layers",
    "stage_context_polygon_layers",
    "validate_feature_collection",
]
