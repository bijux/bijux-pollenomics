from __future__ import annotations

from pathlib import Path


from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths


def test_bundle_paths_own_static_asset_manifest(tmp_path: Path) -> None:
    paths = build_atlas_bundle_paths(tmp_path, "Nordic Atlas", "v66")
    assert paths.map_static_assets_manifest_path == (
        tmp_path / "nordic-atlas_map_assets.json"
    )
