"""Atlas context-discovery projection tests."""

from __future__ import annotations
from pathlib import Path
from bijux_pollenomics.reporting.context.artifacts import stage_context_point_layers
from .fixtures.common import _write_json


def test_discovery_keeps_nordic_sead_sites_without_bulk_temporal_duplicates(
    tmp_path: Path,
) -> None:
    root = tmp_path / "data"
    output = tmp_path / "output"
    output.mkdir()
    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [10, 55]},
        "properties": {"layer_key": "fixture"},
    }
    for relative in (
        "sead/normalized/nordic_environmental_sites.geojson",
        "sead/normalized/nordic_temporal_evidence.geojson",
        "sead/derived/sweden_archaeology_site_discovery.geojson",
    ):
        _write_json(
            root / relative, {"type": "FeatureCollection", "features": [feature]}
        )

    layers, _artifacts = stage_context_point_layers(
        scope_key="nordic",
        context_root=root,
        output_dir=output,
        build_external_point_layer_fn=lambda _geojson, source_path: {
            "key": source_path.name
        },
    )

    assert [layer["key"] for layer in layers] == [
        "nordic_environmental_sites.geojson",
        "sweden_archaeology_site_discovery.geojson",
    ]
