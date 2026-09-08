"""Static-atlas transport proof for source chronology layers."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)

from .support import projection


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
