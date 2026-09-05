"""Coordinated source-library cache invalidation."""

from __future__ import annotations

from .registries import (
    _build_paper_registry_cached,
    _build_project_registry_cached,
    _build_supplement_zip_member_registry_cached,
)
from .storage import (
    _build_source_artifact_index_cached,
    _reference_stash_records_cached,
)


def _clear_source_library_caches() -> None:
    _build_source_artifact_index_cached.cache_clear()
    _build_project_registry_cached.cache_clear()
    _build_paper_registry_cached.cache_clear()
    _build_supplement_zip_member_registry_cached.cache_clear()
    _reference_stash_records_cached.cache_clear()
