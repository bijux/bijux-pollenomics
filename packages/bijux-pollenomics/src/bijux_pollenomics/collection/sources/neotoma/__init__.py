"""Neotoma source collectors and normalization helpers."""

from __future__ import annotations

from importlib import import_module as _import_module
import typing as _typing

if _typing.TYPE_CHECKING:
    from .archive import (
        build_neotoma_download_archive_parts,
        write_neotoma_download_archive,
    )
    from .client import (
        build_neotoma_bbox_geojson,
        extract_neotoma_download_dataset_ids,
        fetch_neotoma_api_payload,
        fetch_neotoma_api_rows,
        fetch_neotoma_dataset_download_row,
        fetch_neotoma_dataset_download_rows,
        fetch_neotoma_dataset_inventory_rows,
        neotoma_download_dataset_id,
        validate_neotoma_download_coverage,
        validate_neotoma_selected_download,
    )
    from .context_points import normalize_neotoma_rows
    from .country import (
        build_neotoma_site_country_decisions,
        classify_neotoma_site_country,
        neotoma_site_raw_country,
    )
    from .materialization import materialize_neotoma_relational_snapshot
    from .relational import build_neotoma_relational_snapshot
    from .relational.chronology import require_neotoma_point_age
    from .relational.variables import is_native_pollen
    from .review import (
        build_neotoma_temporal_review,
        render_neotoma_temporal_review_markdown,
        write_neotoma_review_outputs,
    )
    from .site_inventory import (
        build_neotoma_site_rows_from_downloads,
        build_neotoma_site_snapshot_rows,
    )

__all__ = [
    "build_neotoma_bbox_geojson",
    "build_neotoma_download_archive_parts",
    "build_neotoma_relational_snapshot",
    "build_neotoma_site_country_decisions",
    "build_neotoma_site_rows_from_downloads",
    "build_neotoma_site_snapshot_rows",
    "build_neotoma_temporal_review",
    "classify_neotoma_site_country",
    "extract_neotoma_download_dataset_ids",
    "fetch_neotoma_api_payload",
    "fetch_neotoma_api_rows",
    "fetch_neotoma_dataset_download_row",
    "fetch_neotoma_dataset_download_rows",
    "fetch_neotoma_dataset_inventory_rows",
    "is_native_pollen",
    "materialize_neotoma_relational_snapshot",
    "neotoma_download_dataset_id",
    "neotoma_site_raw_country",
    "normalize_neotoma_rows",
    "require_neotoma_point_age",
    "render_neotoma_temporal_review_markdown",
    "validate_neotoma_download_coverage",
    "validate_neotoma_selected_download",
    "write_neotoma_download_archive",
    "write_neotoma_review_outputs",
]

_EXPORT_MODULES = {
    "build_neotoma_download_archive_parts": ".archive",
    "write_neotoma_download_archive": ".archive",
    "build_neotoma_bbox_geojson": ".client",
    "extract_neotoma_download_dataset_ids": ".client",
    "fetch_neotoma_api_payload": ".client",
    "fetch_neotoma_api_rows": ".client",
    "fetch_neotoma_dataset_download_row": ".client",
    "fetch_neotoma_dataset_download_rows": ".client",
    "fetch_neotoma_dataset_inventory_rows": ".client",
    "neotoma_download_dataset_id": ".client",
    "validate_neotoma_download_coverage": ".client",
    "validate_neotoma_selected_download": ".client",
    "require_neotoma_point_age": ".relational.chronology",
    "is_native_pollen": ".relational.variables",
    "normalize_neotoma_rows": ".context_points",
    "build_neotoma_site_country_decisions": ".country",
    "classify_neotoma_site_country": ".country",
    "neotoma_site_raw_country": ".country",
    "materialize_neotoma_relational_snapshot": ".materialization",
    "build_neotoma_relational_snapshot": ".relational",
    "build_neotoma_temporal_review": ".review",
    "render_neotoma_temporal_review_markdown": ".review",
    "write_neotoma_review_outputs": ".review",
    "build_neotoma_site_rows_from_downloads": ".site_inventory",
    "build_neotoma_site_snapshot_rows": ".site_inventory",
}
_SUBMODULES = frozenset(
    {
        "archive",
        "chronology",
        "client",
        "collection",
        "context_points",
        "country",
        "materialization",
        "production",
        "relational",
        "review",
        "site_inventory",
    }
)


if not _typing.TYPE_CHECKING:

    def __getattr__(name: str) -> _typing.Any:
        """Resolve the declared owner only when its public API is requested."""
        if name in globals():
            return globals()[name]
        owner = _EXPORT_MODULES.get(name)
        if owner is not None:
            value = getattr(_import_module(owner, __name__), name)
        elif name in _SUBMODULES:
            value = _import_module("." + name, __name__)
        else:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        return globals().setdefault(name, value)


def __dir__() -> list[str]:
    """Discover public exports and child modules without importing their owners."""
    return sorted(set(globals()) | set(__all__) | _SUBMODULES)
