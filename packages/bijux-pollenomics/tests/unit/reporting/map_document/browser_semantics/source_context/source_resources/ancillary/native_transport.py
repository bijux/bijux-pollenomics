"""Build v1/v2 browser packets with the maintained catalogue and asset publishers."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
from typing import Any, cast

from bijux_pollenomics.reporting.map_document import render
from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogue,
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


def publish(
    catalogue: AtlasResourceCatalogue,
    root: Path,
    *,
    ancillary: bool = True,
    countries: tuple[str, ...] = ("Sweden", "Norway", "Denmark", "Finland"),
) -> dict[str, Any]:
    """Publish actual serialized metadata; never read a scientific input fixture."""
    if not ancillary:
        catalogue = replace(catalogue, ancillary=None)
    root.mkdir()
    assets = write_static_atlas_assets(
        root,
        slug="metadata",
        version="ancillary-reader",
        point_layers=[],
        polygon_layers=[],
        source_resources=catalogue,
    )
    html, _ = render.write_static_map_document(
        root / "index.html",
        title="Generated source metadata",
        version="ancillary-reader",
        generated_on="Generated fixture",
        countries=countries,
        policy=MAP_SCOPE_POLICIES["custom"],
        point_layers=[],
        polygon_layers=[],
        asset_base_path="_map_assets",
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
    return {
        "source": render.static_map_optional_controller_paths(html)[0].read_text(),
        "manifest": {**assets.manifest, "assets": rows},
        "payloads": payloads,
        "root": root,
        "routes": {},
    }


def invoke(packet: dict[str, Any], probe: str) -> dict[str, Any]:
    """Expose actual packaged JavaScript refusal messages in causal test failures."""
    from ...test_source_resources import invoke as invoke_browser

    try:
        return invoke_browser(
            (packet["source"], packet["manifest"], packet["payloads"]), probe
        )
    except subprocess.CalledProcessError as error:
        raise AssertionError(error.stderr) from error
