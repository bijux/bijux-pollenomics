"""Orchestrate lossless Neotoma relational snapshot construction."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .country import CountryAttributionInput, country_attribution
from .projection.site_hierarchy import project_download_row
from .reconciliation import build_snapshot_payload
from .state import RelationalBuildState


def build_neotoma_relational_snapshot(
    download_rows: Iterable[Mapping[str, object]],
    *,
    source_snapshot_id: str,
    build_id: str,
    country_by_site_id: Mapping[object, CountryAttributionInput] | None = None,
) -> dict[str, object]:
    """Preserve joined detail with governed country decisions on every site.

    String country values remain accepted only as review-blocked legacy evidence.
    """
    if not source_snapshot_id.strip():
        raise ValueError("source_snapshot_id must not be empty")
    if not build_id.strip():
        raise ValueError("build_id must not be empty")

    country_by_source_site_id = {
        str(site_id): country_attribution(value)
        for site_id, value in (country_by_site_id or {}).items()
    }
    state = RelationalBuildState.create(
        source_snapshot_id=source_snapshot_id,
        build_id=build_id,
    )
    for download_row in download_rows:
        project_download_row(
            state,
            download_row,
            country_attribution=country_by_source_site_id,
        )
    return build_snapshot_payload(state)


__all__ = ["build_neotoma_relational_snapshot"]
