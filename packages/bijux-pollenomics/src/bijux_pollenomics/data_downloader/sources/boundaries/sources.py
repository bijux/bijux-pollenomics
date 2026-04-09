from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

from ...pipeline.source_registry import CONTEXT_SOURCE_SPECS

__all__ = ["resolve_country_boundaries"]

CountryBoundaries: TypeAlias = dict[str, dict[str, object]]


def resolve_country_boundaries(
    *,
    output_root: Path,
    selected_sources: tuple[str, ...],
    collect_boundaries_data: Callable[[Path], tuple[CountryBoundaries, object]],
    collect_into_staging_dir: Callable[
        ..., tuple[CountryBoundaries, object]
    ],
    fetch_country_boundaries: Callable[[], CountryBoundaries],
    load_country_boundaries: Callable[[Path], CountryBoundaries | None],
) -> tuple[CountryBoundaries | None, str | None]:
    """Resolve the country-boundary set needed by context collectors."""
    need_boundaries = any(
        source in selected_sources for source in ("boundaries", *CONTEXT_SOURCE_SPECS)
    )
    if not need_boundaries:
        return None, None
    if "boundaries" in selected_sources:
        country_boundaries, _ = collect_into_staging_dir(
            final_output_root=output_root / "boundaries",
            collect=collect_boundaries_data,
        )
        return country_boundaries, "collected"

    loaded_boundaries = load_country_boundaries(output_root / "boundaries")
    if loaded_boundaries is not None:
        return loaded_boundaries, "local"
    return fetch_country_boundaries(), "network"
