"""Compatibility tests for the static-assets package facade."""

from bijux_pollenomics.reporting.map_document import static_assets
from bijux_pollenomics.reporting.map_document.static_assets.budgets import (
    ATLAS_CHUNK_TARGET_BYTES,
    ATLAS_DETAIL_CHUNK_TARGET_BYTES,
)
from bijux_pollenomics.reporting.map_document.static_assets.models import (
    StaticAtlasAssets,
)
from bijux_pollenomics.reporting.map_document.static_assets.validation import (
    validate_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.writer import (
    write_static_atlas_assets,
)


def test_package_preserves_legacy_public_surface() -> None:
    assert static_assets.__all__ == [
        "ATLAS_BOOTSTRAP_MAX_BYTES",
        "ATLAS_CHUNK_MAX_BYTES",
        "ATLAS_DOCUMENT_MAX_BYTES",
        "ATLAS_FILTER_MAIN_THREAD_MAX_MS",
        "ATLAS_INITIAL_MAX_BYTES",
        "ATLAS_INITIAL_MAX_REQUESTS",
        "ATLAS_INTERACTION_MAX_BYTES",
        "ATLAS_INTERACTION_MAX_REQUESTS",
        "ATLAS_STATIC_ASSETS_MAX_BYTES",
        "ATLAS_STATIC_ASSETS_MAX_FILES",
        "StaticAtlasAssets",
        "validate_atlas_release_id",
        "validate_static_atlas_assets",
        "validate_static_atlas_document",
        "write_static_atlas_assets",
    ]
    assert static_assets.StaticAtlasAssets is StaticAtlasAssets
    assert static_assets.validate_static_atlas_assets is validate_static_atlas_assets
    assert static_assets.write_static_atlas_assets is write_static_atlas_assets


def test_package_preserves_direct_access_to_partition_budgets() -> None:
    assert static_assets.ATLAS_CHUNK_TARGET_BYTES == ATLAS_CHUNK_TARGET_BYTES
    assert (
        static_assets.ATLAS_DETAIL_CHUNK_TARGET_BYTES == ATLAS_DETAIL_CHUNK_TARGET_BYTES
    )
