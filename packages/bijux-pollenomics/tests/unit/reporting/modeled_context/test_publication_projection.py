from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
from typing import cast

import pytest

from bijux_pollenomics.reporting.context.polygons import build_external_polygon_layer
from bijux_pollenomics.reporting.map_document.payload import build_map_document_payload
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy
from bijux_pollenomics.reporting.modeled_context import (
    ModeledContextContractError,
    build_modeled_context_manifest,
)
from bijux_pollenomics.reporting.modeled_context.publication_projection import (
    project_modeled_context_layers,
)
from tests.support.repository import REPOSITORY_ROOT


def _repository_layer() -> dict[str, object]:
    source_path = (
        REPOSITORY_ROOT
        / "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson"
    )
    geojson = json.loads(source_path.read_text(encoding="utf-8"))
    return build_external_polygon_layer(geojson, source_path=source_path)


def _features(layer: Mapping[str, object]) -> list[dict[str, object]]:
    geojson = cast(dict[str, object], layer["geojson"])
    return cast(list[dict[str, object]], geojson["features"])


def test_projection_nulls_every_unavailable_value_without_mutating_source() -> None:
    layer = _repository_layer()
    source_before = deepcopy(layer)

    projected = project_modeled_context_layers([layer])[0]
    source_rows = _features(layer)
    projected_rows = _features(projected)
    unavailable = [
        cast(dict[str, object], row["properties"])
        for row in projected_rows
        if cast(dict[str, object], row["properties"]).get("dataset_id") == "937075"
        and cast(dict[str, object], row["properties"]).get("quality_class")
        == "no_pollen_data"
    ]

    assert len(unavailable) == 307
    assert all(
        set(cast(dict[str, object], properties[field]).values()) == {None}
        for properties in unavailable
        for field in ("reconstruction_values", "standard_errors")
    )
    assert all(
        properties["publication_value_posture"]
        == "unavailable_source_placeholders_replaced_with_null"
        for properties in unavailable
    )
    assert layer == source_before
    assert any(
        any(
            value not in (0, 0.0)
            for value in cast(
                dict[str, object],
                cast(dict[str, object], row["properties"])["reconstruction_values"],
            ).values()
        )
        for row in source_rows
        if cast(dict[str, object], row["properties"]).get("dataset_id") == "937075"
        and cast(dict[str, object], row["properties"]).get("quality_class")
        == "no_pollen_data"
    )


def test_projection_preserves_real_zero_values_in_available_rows() -> None:
    projected = project_modeled_context_layers([_repository_layer()])[0]
    available = [
        cast(dict[str, object], row["properties"])
        for row in _features(projected)
        if cast(dict[str, object], row["properties"]).get("dataset_id") == "937075"
        and cast(dict[str, object], row["properties"]).get("quality_class")
        in {"high", "low"}
    ]

    assert any(
        value == 0
        for properties in available
        for value in cast(
            dict[str, object], properties["reconstruction_values"]
        ).values()
    )
    assert all(
        "publication_value_posture" not in properties for properties in available
    )


def test_canonical_roundtrip_preserves_native_and_published_manifest() -> None:
    native = _repository_layer()
    original = deepcopy(native)
    expected = build_modeled_context_manifest([native])
    sorted_native = json.loads(json.dumps([native], sort_keys=True))
    assert build_modeled_context_manifest(sorted_native) == expected

    projected = project_modeled_context_layers([native])
    canonical_projection = json.loads(json.dumps(projected, sort_keys=True))
    assert build_modeled_context_manifest(canonical_projection) == expected
    assert canonical_projection == projected
    assert native == original


@pytest.mark.parametrize(
    "change",
    [
        "numeric_estimate",
        "numeric_error",
        "missing_marker",
        "unknown_marker",
        "null_marker",
        "high_quality",
        "low_quality",
        "missing_metric",
        "extra_metric",
    ],
)
def test_unavailable_projection_cannot_admit_mixed_or_unmarked_values(
    change: str,
) -> None:
    projected = project_modeled_context_layers([_repository_layer()])
    properties = next(
        cast(dict[str, object], feature["properties"])
        for feature in _features(projected[0])
        if cast(dict[str, object], feature["properties"]).get("dataset_id") == "937075"
        and cast(dict[str, object], feature["properties"]).get("quality_class")
        == "no_pollen_data"
    )
    estimates = cast(dict[str, object], properties["reconstruction_values"])
    errors = cast(dict[str, object], properties["standard_errors"])
    if change == "numeric_estimate":
        estimates["Picea"] = 0
    elif change == "numeric_error":
        errors["Picea"] = 0
    elif change == "missing_marker":
        properties.pop("publication_value_posture")
    elif change == "unknown_marker":
        properties["publication_value_posture"] = "unqualified"
    elif change == "null_marker":
        properties["publication_value_posture"] = None
    elif change in {"high_quality", "low_quality"}:
        properties["quality_class"] = change.removesuffix("_quality")
    elif change == "missing_metric":
        errors.pop("Picea")
    else:
        estimates["foreign_metric"] = None
    with pytest.raises(ModeledContextContractError):
        build_modeled_context_manifest(projected)


def test_numeric_source_rejects_unavailable_publication_marker() -> None:
    layer = _repository_layer()
    properties = next(
        cast(dict[str, object], feature["properties"])
        for feature in _features(layer)
        if cast(dict[str, object], feature["properties"]).get("dataset_id") == "937075"
        and cast(dict[str, object], feature["properties"]).get("quality_class")
        == "no_pollen_data"
    )
    properties["publication_value_posture"] = (
        "unavailable_source_placeholders_replaced_with_null"
    )
    with pytest.raises(ModeledContextContractError, match="values or posture differ"):
        build_modeled_context_manifest([layer])


def test_inline_map_payload_serializes_null_publication_values() -> None:
    layer = _repository_layer()

    payload = build_map_document_payload(
        title="Nordic",
        version="modeled-projection-test",
        generated_on="2026-09-07",
        countries=("Denmark", "Finland", "Norway", "Sweden"),
        policy=resolve_map_scope_policy(None),
        point_layers=[],
        polygon_layers=[layer],
        asset_base_path="assets",
        escape_html_fn=lambda value: value,
    )
    serialized_layers = cast(
        list[dict[str, object]], json.loads(payload["__POLYGON_LAYERS_JSON__"])
    )
    unavailable = [
        cast(dict[str, object], row["properties"])
        for row in _features(serialized_layers[0])
        if cast(dict[str, object], row["properties"]).get("dataset_id") == "937075"
        and cast(dict[str, object], row["properties"]).get("quality_class")
        == "no_pollen_data"
    ]

    assert len(unavailable) == 307
    assert all(
        value is None
        for properties in unavailable
        for value in cast(
            dict[str, object], properties["reconstruction_values"]
        ).values()
    )
