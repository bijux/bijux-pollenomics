"""Static-atlas manifest ownership refusal behavior."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

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


def test_prepare_layers_sends_null_publication_values_to_static_writer(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "atlas-map-assets.json"
    bundle_paths = SimpleNamespace(
        samples_geojson_path=tmp_path / "samples.geojson",
        map_static_assets_manifest_path=manifest_path,
    )
    static_assets = SimpleNamespace(manifest_path=manifest_path, asset_paths=())
    captured: dict[str, object] = {}

    def write_static_atlas_assets(*args: object, **kwargs: object) -> object:
        captured.update(kwargs)
        return static_assets

    surface = SimpleNamespace(
        json=json,
        AnimalCoordinateVisibilityReview=SimpleNamespace,
        build_sweden_lake_atlas_layers=lambda **kwargs: [],
        _attach_traceability_surfaces=lambda point_layers, paths: None,
        write_static_atlas_assets=write_static_atlas_assets,
    )
    source_properties = {
        "dataset_id": "937075",
        "quality_class": "no_pollen_data",
        "reconstruction_values": {"OL": 17.5},
        "standard_errors": {"OL": 2.5},
    }
    polygon_layers = [
        {
            "key": "landclim-reveals-temporal-grid",
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": source_properties,
                        "geometry": None,
                    }
                ],
            },
        }
    ]

    prepare_layers(
        tmp_path,
        report=SimpleNamespace(slug="atlas", output_dir=tmp_path),
        version="v66",
        all_samples=(),
        context_root=None,
        geography_scope=None,
        build_atlas_bundle_paths_fn=lambda **kwargs: bundle_paths,
        build_context_layers_fn=lambda **kwargs: ([], polygon_layers, []),
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

    written_layers = cast(list[dict[str, object]], captured["polygon_layers"])
    written_geojson = cast(dict[str, object], written_layers[0]["geojson"])
    written_features = cast(list[dict[str, object]], written_geojson["features"])
    written_properties = cast(dict[str, object], written_features[0]["properties"])
    assert written_properties["reconstruction_values"] == {"OL": None}
    assert written_properties["standard_errors"] == {"OL": None}
    assert source_properties["reconstruction_values"] == {"OL": 17.5}
