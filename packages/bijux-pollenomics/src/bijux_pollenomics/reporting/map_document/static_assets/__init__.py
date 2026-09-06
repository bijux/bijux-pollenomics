"""Deterministic, integrity-checked static atlas assets."""

from .budgets import (
    ATLAS_BOOTSTRAP_MAX_BYTES,
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_DOCUMENT_MAX_BYTES,
    ATLAS_FILTER_MAIN_THREAD_MAX_MS,
    ATLAS_INITIAL_MAX_BYTES,
    ATLAS_INITIAL_MAX_REQUESTS,
    ATLAS_INTERACTION_MAX_BYTES,
    ATLAS_INTERACTION_MAX_REQUESTS,
    ATLAS_STATIC_ASSETS_MAX_BYTES,
    ATLAS_STATIC_ASSETS_MAX_FILES,
)
from .budgets import (
    ATLAS_CHUNK_TARGET_BYTES as _ATLAS_CHUNK_TARGET_BYTES,
)
from .budgets import (
    ATLAS_DETAIL_CHUNK_TARGET_BYTES as _ATLAS_DETAIL_CHUNK_TARGET_BYTES,
)
from .models import StaticAtlasAssets, validate_atlas_release_id
from .validation import validate_static_atlas_assets, validate_static_atlas_document
from .writer import write_static_atlas_assets

# Preserve direct imports of the legacy module's non-``__all__`` tuning constants.
ATLAS_CHUNK_TARGET_BYTES = _ATLAS_CHUNK_TARGET_BYTES
ATLAS_DETAIL_CHUNK_TARGET_BYTES = _ATLAS_DETAIL_CHUNK_TARGET_BYTES

__all__ = [
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
