"""Static-atlas manifest ownership refusal behavior."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.reporting.bundles.atlas_bundle.layers import prepare_layers


def test_prepare_layers_refuses_a_manifest_outside_bundle_ownership(
    tmp_path: Path,
) -> None:
    expected_manifest = tmp_path / "expected-manifest.json"
    bundle_paths = SimpleNamespace(
        samples_geojson_path=tmp_path / "samples.geojson",
        map_static_assets_manifest_path=expected_manifest,
    )
    static_assets = SimpleNamespace(
        manifest_path=tmp_path / "foreign-manifest.json",
        asset_paths=(),
    )
    surface = SimpleNamespace(
        json=json,
        AnimalCoordinateVisibilityReview=SimpleNamespace,
        build_sweden_lake_atlas_layers=lambda **kwargs: [],
        _attach_traceability_surfaces=lambda point_layers, paths: None,
        write_static_atlas_assets=lambda *args, **kwargs: static_assets,
    )

    with pytest.raises(
        ValueError,
        match="static atlas manifest path does not match bundle ownership",
    ):
        prepare_layers(
            tmp_path,
            report=SimpleNamespace(slug="atlas", output_dir=tmp_path),
            version="v66",
            all_samples=(),
            context_root=None,
            geography_scope=None,
            build_atlas_bundle_paths_fn=lambda **kwargs: bundle_paths,
            build_context_layers_fn=lambda **kwargs: ([], [], []),
            build_samples_geojson_fn=lambda samples: {
                "type": "FeatureCollection",
                "features": [],
            },
            atlas_detail_records=None,
            atlas_scientific_signals=None,
            atlas_edge_records=None,
            atlas_sequence_records=None,
            surface=surface,
        )

    assert not expected_manifest.exists()
