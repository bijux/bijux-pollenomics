"""Authenticated finite source-resource transport for browser consumer controls."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document import render
from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogueInput,
    load_atlas_resource_catalogue,
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
from bijux_pollenomics.reporting.scope_policy import MAP_SCOPE_POLICIES

from ....source_resources.catalogue_inputs import atlas_catalogue as atlas_catalogue
from ....source_resources.catalogue_inputs import catalogue_sources as catalogue_sources


@pytest.fixture
def resource_script(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]], tmp_path: Path
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    root, digest, _ = atlas_catalogue()
    source = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))
    output = tmp_path / "assets"
    output.mkdir()
    assets = write_static_atlas_assets(
        output,
        slug="nordic",
        version="v66",
        point_layers=[],
        polygon_layers=[],
        source_resources=source,
    )
    html, _ = render.write_static_map_document(
        output / "index.html",
        title="Metadata",
        version="v66",
        generated_on="2026-11-15",
        countries=("Sweden",),
        policy=MAP_SCOPE_POLICIES["custom"],
        asset_base_path="_map_assets",
        point_layers=[],
        polygon_layers=[],
        static_assets=assets,
    )
    rows = cast(
        list[dict[str, Any]], normalize_asset_inventory(assets.manifest["assets"])
    )
    payloads = {
        row["asset_key"]: decode_chunk_script(
            path.read_bytes(),
            expected_asset_key=row["asset_key"],
            expected_payload_sha256=row["payload_sha256"],
            expected_payload_encoding=row["payload_encoding"],
            expected_decoded_byte_count=row["decoded_byte_count"],
        )
        for row, path in zip(rows, assets.asset_paths, strict=True)
    }
    manifest = {**assets.manifest, "assets": rows}
    return (
        render.static_map_optional_controller_paths(html)[0].read_text(),
        manifest,
        payloads,
    )
