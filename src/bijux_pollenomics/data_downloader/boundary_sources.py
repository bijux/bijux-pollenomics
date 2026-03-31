from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .source_registry import CONTEXT_SOURCE_SPECS


def resolve_country_boundaries(
    *,
    output_root: Path,
    selected_sources: tuple[str, ...],
    collect_boundaries_data: Callable[..., tuple[dict[str, dict[str, object]], object]],
    collect_into_staging_dir: Callable[..., object],
    fetch_country_boundaries: Callable[[], dict[str, dict[str, object]]],
    load_country_boundaries: Callable[[Path], dict[str, dict[str, object]] | None],
) -> tuple[dict[str, dict[str, object]] | None, str | None]:
    """Resolve the country-boundary set needed by context collectors."""
    need_boundaries = any(source in selected_sources for source in ("boundaries", *CONTEXT_SOURCE_SPECS))
    if not need_boundaries:
        return None, None
    if "boundaries" in selected_sources:
        country_boundaries, _ = collect_into_staging_dir(
            final_output_root=output_root / "boundaries",
            collect=collect_boundaries_data,
        )
        return country_boundaries, "collected"

    country_boundaries = load_country_boundaries(output_root / "boundaries")
    if country_boundaries is not None:
        return country_boundaries, "local"
    return fetch_country_boundaries(), "network"
