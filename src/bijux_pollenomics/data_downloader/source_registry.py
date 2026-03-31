from __future__ import annotations

from dataclasses import dataclass

from .landclim import collect_landclim_data
from .neotoma import collect_neotoma_data
from .raa import collect_raa_data
from .sead import collect_sead_data


@dataclass(frozen=True)
class ContextSourceSpec:
    name: str
    output_dir_name: str
    requires_bbox: bool
    count_attributes: tuple[tuple[str, str], ...]


CONTEXT_SOURCE_SPECS = {
    "landclim": ContextSourceSpec(
        name="landclim",
        output_dir_name="landclim",
        requires_bbox=True,
        count_attributes=(
            ("landclim_site_count", "site_count"),
            ("landclim_grid_cell_count", "grid_cell_count"),
        ),
    ),
    "neotoma": ContextSourceSpec(
        name="neotoma",
        output_dir_name="neotoma",
        requires_bbox=True,
        count_attributes=(("neotoma_point_count", "point_count"),),
    ),
    "raa": ContextSourceSpec(
        name="raa",
        output_dir_name="raa",
        requires_bbox=False,
        count_attributes=(
            ("raa_total_site_count", "total_site_count"),
            ("raa_heritage_site_count", "heritage_site_count"),
        ),
    ),
    "sead": ContextSourceSpec(
        name="sead",
        output_dir_name="sead",
        requires_bbox=True,
        count_attributes=(("sead_point_count", "point_count"),),
    ),
}

CONTEXT_COLLECT_FUNCTIONS = {
    "landclim": collect_landclim_data,
    "neotoma": collect_neotoma_data,
    "raa": collect_raa_data,
    "sead": collect_sead_data,
}


def resolve_context_collect_function(name: str):
    """Resolve a context-source collector function by tracked source name."""
    try:
        return CONTEXT_COLLECT_FUNCTIONS[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported context source: {name}") from exc
