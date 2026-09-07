"""Presentation policy for governed map publication scopes."""

from __future__ import annotations

from dataclasses import dataclass

from .geography import GeographicScope


@dataclass(frozen=True)
class MapScopePolicy:
    key: str
    label: str
    eyebrow_label: str
    summary: str
    bounds_summary: str
    default_basemap: str
    initial_diameter_km: int
    minimum_bounds: tuple[tuple[float, float], tuple[float, float]]
    filter_surfaces: tuple[str, ...]
    legend_sections: tuple[str, ...]
    visible_caveats: tuple[str, ...]
    engine_summary: str
    chronology_playback_href: str | None = None


_COMMON_FILTER_SURFACES = (
    "Country filters",
    "Layer toggles",
    "Search",
    "Time window",
    "Distance circles",
    "Basemap switch",
)
_COMMON_LEGEND_SECTIONS = (
    "Human evidence markers",
    "Animal evidence markers when present",
    "Context overlay symbols",
    "Density ramp when archaeology density is visible",
)
_COMMON_ENGINE_SUMMARY = (
    "One shared map document engine serves every published scope. Scope differences "
    "must be encoded in governed bounds, layer eligibility, default basemap, and "
    "reader caveats rather than hidden in separate renderer forks."
)
ALL_SCOPE_KEYS = ("world", "europe_plus", "nordic", "custom")
NORDIC_SCOPE_KEYS = ("nordic",)

MAP_SCOPE_POLICIES: dict[str, MapScopePolicy] = {
    "world": MapScopePolicy(
        key="world",
        label="World",
        eyebrow_label="World Surface",
        summary=(
            "World is the governing publication surface. It keeps every published "
            "country inside one shared map and excludes Nordic-only context overlays "
            "that would look more complete than they really are at broader scale."
        ),
        bounds_summary=(
            "The opening extent keeps a broad trans-Atlantic and Eurasian frame so the "
            "root publication surface reads as a parent scope rather than a Nordic "
            "detail page with a bigger title."
        ),
        default_basemap="street",
        initial_diameter_km=40,
        minimum_bounds=((-20.0, -165.0), (82.0, 180.0)),
        filter_surfaces=_COMMON_FILTER_SURFACES,
        legend_sections=_COMMON_LEGEND_SECTIONS,
        visible_caveats=(
            "World is the parent publication scope, not a claim that worldwide contextual coverage is already complete.",
            "Nordic environmental and archaeology overlays are withheld here until broader equivalents exist.",
            "Country counts still describe Homo sapiens AADR rows even when animal layers are also visible.",
        ),
        engine_summary=_COMMON_ENGINE_SUMMARY,
    ),
    "europe_plus": MapScopePolicy(
        key="europe_plus",
        label="Europe-plus",
        eyebrow_label="Europe-plus Surface",
        summary=(
            "Europe-plus is a governed regional filter view. It keeps only Europe-plus "
            "countries from the broader publication surface and still withholds "
            "Nordic-only overlays that would overstate regional context coverage."
        ),
        bounds_summary=(
            "The opening extent centers the European frame while keeping enough margin "
            "for future expansion into non-Nordic Europe-plus countries."
        ),
        default_basemap="street",
        initial_diameter_km=30,
        minimum_bounds=((34.0, -16.0), (72.0, 42.0)),
        filter_surfaces=_COMMON_FILTER_SURFACES,
        legend_sections=_COMMON_LEGEND_SECTIONS,
        visible_caveats=(
            "Europe-plus is derived from the world publication surface by governed country filtering, not by a second evidence pipeline.",
            "Nordic-only pollen, archaeology, and fieldwork overlays remain absent here on purpose.",
            "Future non-Nordic Europe-plus additions should arrive by country onboarding, not by custom one-off bundle logic.",
        ),
        engine_summary=_COMMON_ENGINE_SUMMARY,
    ),
    "nordic": MapScopePolicy(
        key="nordic",
        label="Nordic",
        eyebrow_label="Nordic Surface",
        summary=(
            "Nordic is the regional detail surface. It keeps the shared human and "
            "animal evidence layers, then adds Nordic-only environmental, archaeology, "
            "boundary, and fieldwork overlays that remain interpretable at this scale."
        ),
        bounds_summary=(
            "The opening extent stays tight on Nordic countries so lake, site, and "
            "archaeology context reads as map content rather than background noise."
        ),
        default_basemap="street",
        initial_diameter_km=20,
        minimum_bounds=((54.0, 4.0), (72.0, 35.0)),
        filter_surfaces=(
            *_COMMON_FILTER_SURFACES,
            "Accepted scientific comparison when qualified classifications are available",
            "Neotoma source-sample, literal-code, and exact-label chronology",
            "Oldest-to-present BP window navigation and playback",
            "PANGAEA 937075 exact-window modeled context",
            "Modeled-context visible-frame export",
            "Animal species focus when animal layers are present",
            "Animal scope when animal layers are present",
            "Animal coordinate confidence when animal layers are present",
            "Animal temporal windows when animal layers are present",
            "Nordic animal leads only when animal layers are present",
        ),
        legend_sections=(
            *_COMMON_LEGEND_SECTIONS,
            "Nordic environmental context markers",
            "Nordic boundary and archaeology overlays",
            "Fieldwork documentation marker when checked-in gallery media is present",
        ),
        visible_caveats=(
            "Nordic-specific overlays describe the current Nordic recovery slice and must not be generalized outward.",
            "Animal points can remain visible even when their Nordic relevance is regional rather than one exact country.",
            "Approximate or inferred coordinates remain visible with explicit warnings instead of being silently dropped.",
        ),
        engine_summary=_COMMON_ENGINE_SUMMARY,
        chronology_playback_href="../../../public/nordic-atlas/chronology-playback/",
    ),
    "custom": MapScopePolicy(
        key="custom",
        label="Custom",
        eyebrow_label="Evidence Surface",
        summary=(
            "This is a direct generated map bundle outside the governed world, "
            "Europe-plus, and Nordic publication tree."
        ),
        bounds_summary=(
            "The opening extent follows the visible points because no governed scope "
            "bounds were supplied."
        ),
        default_basemap="street",
        initial_diameter_km=20,
        minimum_bounds=((54.0, 4.0), (72.0, 35.0)),
        filter_surfaces=_COMMON_FILTER_SURFACES,
        legend_sections=_COMMON_LEGEND_SECTIONS,
        visible_caveats=(
            "Custom bundles are convenience outputs and do not define new public geography policy.",
        ),
        engine_summary=_COMMON_ENGINE_SUMMARY,
    ),
}


def resolve_map_scope_policy(
    geography_scope: GeographicScope | None,
) -> MapScopePolicy:
    """Resolve the governed map presentation policy for one publication scope."""
    if geography_scope is None:
        return MAP_SCOPE_POLICIES["custom"]
    return MAP_SCOPE_POLICIES.get(geography_scope.key, MAP_SCOPE_POLICIES["custom"])


__all__ = [
    "ALL_SCOPE_KEYS",
    "MAP_SCOPE_POLICIES",
    "NORDIC_SCOPE_KEYS",
    "MapScopePolicy",
    "resolve_map_scope_policy",
]
