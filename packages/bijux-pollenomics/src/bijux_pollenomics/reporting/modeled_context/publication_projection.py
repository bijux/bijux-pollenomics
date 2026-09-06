"""Publication projection for source-modeled context values."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import cast

from ...core.geospatial.geojson import JsonObject, as_mapping, feature_list
from .contracts import PANGAEA_DATASET_ID

_VALUE_FIELDS = ("reconstruction_values", "standard_errors")


def project_modeled_context_layers(
    polygon_layers: Sequence[Mapping[str, object]],
) -> list[JsonObject]:
    """Return map-safe layers with unavailable modeled values represented as null."""
    projected = deepcopy(list(polygon_layers))
    for layer in projected:
        geojson = as_mapping(layer.get("geojson"))
        if geojson is None:
            continue
        for feature in feature_list(geojson):
            properties = as_mapping(feature.get("properties"))
            if (
                properties is None
                or properties.get("dataset_id") != PANGAEA_DATASET_ID
                or properties.get("quality_class") != "no_pollen_data"
            ):
                continue
            mutable_properties = dict(properties)
            for field in _VALUE_FIELDS:
                source_values = as_mapping(properties.get(field))
                if source_values is None:
                    raise ValueError(f"PANGAEA no-pollen row lacks a {field} mapping")
                mutable_properties[field] = {
                    str(metric): None for metric in source_values
                }
            mutable_properties["publication_value_posture"] = (
                "unavailable_source_placeholders_replaced_with_null"
            )
            cast(dict[str, object], feature)["properties"] = mutable_properties
    return [dict(layer) for layer in projected]


__all__ = ["project_modeled_context_layers"]
