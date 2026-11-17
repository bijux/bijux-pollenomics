"""Use packaged renderer and transport for registry context, not a second map."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.reporting.context.raa_native.publication import (
    build_native_registry_layer,
)
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)

from ...map_document.browser_semantics.support import run_node_json, template_block
from .test_snapshot import capture, generated_inputs


def test_popup_preserves_zero_and_explicit_partial_full_cell_meaning(
    tmp_path: Path,
) -> None:
    generated_inputs(tmp_path / "input")
    layer = build_native_registry_layer(capture(tmp_path / "input"))
    feature = layer["geojson"]["features"][0]
    feature["properties"]["popup_rows"][0]["value"] = 0
    helper = template_block("function polygonPopupHtml", "function densityFillColor")
    observed = run_node_json(
        "function escapeHtml(v){return String(v).replaceAll('<','&lt;');}"
        "function availablePopupRows(rows){return rows.filter(r=>r.value!==null&&r.value!==undefined);}"
        "function isModeledContextFeature(){return false;} function currentModeledContextMetric(){return null;}"
        "function modeledContextEstimate(){return null;}function modeledContextStandardError(){return null;}\n"
        + helper
        + "\nconst layer="
        + json.dumps(layer)
        + ";console.log(JSON.stringify(polygonPopupHtml(layer,layer.geojson.features[0].properties)));"
    )
    assert "</strong> 0</div>" in observed
    assert "full-cell" in observed
    assert "not prorated" in observed
    assert "country unassigned" in observed
    assert "chronology unsupported" in observed
    assert "coordinate accuracy" in observed


def test_current_country_and_time_predicates_leave_opt_in_context_unassigned(
    tmp_path: Path,
) -> None:
    generated_inputs(tmp_path / "input")
    layer = build_native_registry_layer(capture(tmp_path / "input"))
    helper = template_block(
        "function polygonFeatureVisible", "function removeRenderedLayers"
    )
    observed = run_node_json(
        "const activeLayerKeys=new Set(['raa-native-registry-cells']); const activeCountries=new Set();"
        "function modeledContextFeatureVisible(){return true;}"
        "function featureInTimeWindow(layer){return layer.applies_time_filter===false;}"
        "function finiteCoordinateValue(v,min,max){return typeof v==='number'&&v>=min&&v<=max?v:null;}\n"
        + helper
        + "\nconst layer="
        + json.dumps(layer)
        + ";console.log(JSON.stringify(layer.geojson.features.map(f=>({visible:polygonFeatureVisible(layer,f.properties),geometry:polygonGeometryIsAdmitted(f)}))));"
    )
    assert observed == [{"visible": True, "geometry": True}] * 2


def test_real_static_publisher_conserves_full_cell_metadata(tmp_path: Path) -> None:
    generated_inputs(tmp_path / "input")
    layer = build_native_registry_layer(capture(tmp_path / "input"))
    output = tmp_path / "assets"
    output.mkdir()
    assets = write_static_atlas_assets(
        output,
        slug="registry",
        version="generated",
        point_layers=[],
        polygon_layers=[layer],
    )
    rows = normalize_asset_inventory(assets.manifest["assets"])
    payloads = [
        decode_chunk_script(
            path.read_bytes(),
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
        )
        for path, row in zip(assets.asset_paths, rows, strict=True)
    ]
    nodes = [
        payload
        for payload in payloads
        if payload.get("layer_kind") == "polygon" and "features" in payload
    ]
    features = [row for payload in nodes for row in payload["features"]]
    assert len(features) == 2
    assert sum(row["properties"]["count"] for row in features) == 3
    assert all("country" not in row["properties"] for row in features)
    assert features[0]["properties"]["partial_display_footprint"] is True
    assert features[0]["properties"]["native_cell_bounds"] == [10, 57, 11, 58]


def test_native_context_uses_bounded_static_document_writer(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.map_document.render import (
        write_static_map_document,
    )
    from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy

    generated_inputs(tmp_path / "input")
    layer = build_native_registry_layer(capture(tmp_path / "input"))
    output = tmp_path / "document"
    output.mkdir()
    assets = write_static_atlas_assets(
        output,
        slug="registry",
        version="generated",
        point_layers=[],
        polygon_layers=[layer],
    )
    document, runtime = write_static_map_document(
        output / "index.html",
        "Registry context",
        "generated",
        "2026-11-17",
        (),
        resolve_map_scope_policy(None),
        [],
        [layer],
        "./_map_assets",
        static_assets=assets,
    )
    assert document.stat().st_size <= 524288
    assert runtime.stat().st_size <= 524288
    text = runtime.read_text()
    assert "registry-context" in text
    assert "properties.registry_fill" in text
