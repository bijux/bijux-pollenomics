"""Static-atlas transport proof for source chronology layers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import (
    validate_static_atlas_assets,
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.index_bundles import (
    decode_index_bundle,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)
from bijux_pollenomics.reporting.source_chronology import (
    build_source_chronology_atlas_projection,
)

from ..map_document.browser_semantics.support import run_node_json, template_block
from .support import DETAIL_ID, projection, source_result


def test_source_layers_fit_static_chunk_contract(tmp_path: Path) -> None:
    _, atlas = projection()

    assets = write_static_atlas_assets(
        tmp_path,
        slug="source-chronology",
        version="fixture",
        point_layers=atlas.point_layers,
        polygon_layers=(),
    )

    assert len(normalize_asset_inventory(assets.manifest["assets"])) == len(
        assets.asset_paths
    )
    assert all(path.stat().st_size <= 4_194_304 for path in assets.asset_paths)


@pytest.mark.parametrize("bounds", [(0, 0), (0.75, 878.26), (1150, 1250)])
def test_selected_source_interval_survives_static_index_and_narrowed_js_selection(
    tmp_path: Path, bounds: tuple[int | float, int | float]
) -> None:
    result = source_result(younger_bp=bounds[0], older_bp=bounds[1])
    atlas = build_source_chronology_atlas_projection(
        result, detail_record_ids={DETAIL_ID}
    )
    assets = write_static_atlas_assets(
        tmp_path,
        slug="source-chronology",
        version="fixture",
        point_layers=atlas.point_layers,
        polygon_layers=(),
    )
    validate_static_atlas_assets(assets)
    rows = normalize_asset_inventory(assets.manifest["assets"])
    observed_intervals: list[object] = []
    nodes: list[dict[str, object]] = []
    for row, path in zip(rows, assets.asset_paths, strict=True):
        decoded_count = row["decoded_byte_count"]
        assert isinstance(decoded_count, int)
        payload = decode_chunk_script(
            path.read_bytes(),
            expected_asset_key=str(row["asset_key"]),
            expected_payload_sha256=str(row["payload_sha256"]),
            expected_payload_encoding=str(row["payload_encoding"]),
            expected_decoded_byte_count=decoded_count,
        )
        if row["domain"] == "nodes":
            assert (row["time_min_bp"], row["time_max_bp"]) == bounds
            assert row["untimed_record_count"] == 0
            assert row["contextual_chronology_record_count"] == 0
            assert row["refused_chronology_record_count"] == 0
            features = payload["features"]
            assert isinstance(features, list) and len(features) == 1
            nodes.append({"row": row, "feature": features[0]})
        if row["domain"] == "indexes":
            intervals = decode_index_bundle(payload)["time_interval_feature_indexes"]
            assert isinstance(intervals, list)
            observed_intervals.extend(intervals)
    assert len(observed_intervals) == 3
    assert all(
        [*bounds, layer["key"], 0] in observed_intervals for layer in atlas.point_layers
    )
    helpers = "\n".join(
        [
            template_block(
                "function staticAtlasFailure(",
                "function staticAtlasNullableFiniteNumber(",
            ),
            template_block(
                "function staticAtlasTimeNeeded(", "function staticAtlasSignalNeeded("
            ),
            template_block("function finiteTimeValue(", "function valueIsAvailable("),
            template_block(
                "function featureTimeAdmission(", "function featureTimeLabel("
            ),
        ]
    )
    observed = run_node_json(
        helpers
        + "\nconst nodes="
        + json.dumps(nodes)
        + ";\n"
        + f"const TIME_HAS_DATA=true;let timeStartBp={bounds[0]};let end={bounds[1]};\n"
        + "function timeWindowEndBp(){return end;}function timeFilterUsesFullExtent(){return false;}\n"
        + "const layer={applies_time_filter:true,semantic_role:'source_chronology_context'};\n"
        + "const inside=nodes.map(({row,feature})=>[staticAtlasTimeNeeded(row,layer),featureInTimeWindow(layer,feature),featureTimeAdmission(feature)]);\n"
        + f"timeStartBp={bounds[1] + 1};end=timeStartBp+1;\n"
        + "const outside=nodes.map(({row,feature})=>[staticAtlasTimeNeeded(row,layer),featureInTimeWindow(layer,feature)]);\n"
        + "console.log(JSON.stringify({inside,outside}));"
    )
    assert observed == {
        "inside": [
            [
                True,
                True,
                {"status": "valid", "window": {"start": bounds[0], "end": bounds[1]}},
            ]
        ]
        * 3,
        "outside": [[False, False]] * 3,
    }
