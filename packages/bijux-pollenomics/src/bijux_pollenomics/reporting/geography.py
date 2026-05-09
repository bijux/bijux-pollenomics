from __future__ import annotations

from dataclasses import dataclass

from .presentation.text import slugify

__all__ = [
    "EUROPEAN_UNION_COUNTRIES",
    "EUROPE_PLUS_COUNTRIES",
    "NORDIC_COUNTRIES",
    "PUBLISHED_REPORT_COUNTRY_DIR",
    "PUBLISHED_REPORT_EUROPE_PLUS_DIR",
    "PUBLISHED_REPORT_NORDIC_DIR",
    "PUBLISHED_REPORT_WORLD_DIR",
    "GeographicScope",
    "PublishedGeographyPlan",
    "REGIONAL_COUNTRY_ASSIGNMENTS",
    "TERRITORY_COUNTRY_ASSIGNMENTS",
    "build_published_geography_plan",
    "filter_scope_countries",
    "geographic_parent_scope",
    "political_entity_countries",
    "render_geography_onboarding_contract_markdown",
    "render_geography_scope_registry_markdown",
    "render_geography_subset_validation_markdown",
    "scope_contains_country",
    "scope_contains_political_entity",
]

EUROPEAN_UNION_COUNTRIES: tuple[str, ...] = (
    "Austria",
    "Belgium",
    "Bulgaria",
    "Croatia",
    "Cyprus",
    "Czech Republic",
    "Denmark",
    "Estonia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hungary",
    "Ireland",
    "Italy",
    "Latvia",
    "Lithuania",
    "Luxembourg",
    "Malta",
    "Netherlands",
    "Poland",
    "Portugal",
    "Romania",
    "Slovakia",
    "Slovenia",
    "Spain",
    "Sweden",
)
EUROPE_PLUS_COUNTRIES: tuple[str, ...] = tuple(
    sorted({*EUROPEAN_UNION_COUNTRIES, "Norway", "Switzerland"})
)
NORDIC_COUNTRIES: tuple[str, ...] = (
    "Denmark",
    "Finland",
    "Iceland",
    "Norway",
    "Sweden",
)

PUBLISHED_REPORT_WORLD_DIR = ("world",)
PUBLISHED_REPORT_EUROPE_PLUS_DIR = ("regions", "europe-plus")
PUBLISHED_REPORT_NORDIC_DIR = ("regions", "nordic")
PUBLISHED_REPORT_COUNTRY_DIR = ("countries",)

REGIONAL_COUNTRY_ASSIGNMENTS: dict[str, tuple[str, ...]] = {
    "Baltic Sea Region": ("Sweden", "Denmark", "Finland"),
}
TERRITORY_COUNTRY_ASSIGNMENTS: dict[str, str] = {
    "Svalbard": "Norway",
}


@dataclass(frozen=True)
class GeographicScope:
    key: str
    kind: str
    label: str
    slug: str
    countries: tuple[str, ...]
    parent_key: str | None
    output_dir_parts: tuple[str, ...]
    map_title: str


@dataclass(frozen=True)
class PublishedGeographyPlan:
    world_scope: GeographicScope
    regional_scopes: tuple[GeographicScope, ...]
    country_scopes: tuple[GeographicScope, ...]

    def all_scopes(self) -> tuple[GeographicScope, ...]:
        return (self.world_scope, *self.regional_scopes, *self.country_scopes)


def filter_scope_countries(
    countries: tuple[str, ...],
    allowed_countries: tuple[str, ...],
) -> tuple[str, ...]:
    """Keep only the published countries that belong to one allowed country set."""
    allowed = set(allowed_countries)
    return tuple(country for country in countries if country in allowed)


def build_published_geography_plan(
    countries: tuple[str, ...],
) -> PublishedGeographyPlan:
    """Define the governed publication scopes derived from the published country roster."""
    world_scope = GeographicScope(
        key="world",
        kind="world",
        label="World",
        slug="world",
        countries=countries,
        parent_key=None,
        output_dir_parts=PUBLISHED_REPORT_WORLD_DIR,
        map_title="World Evidence Surface",
    )
    regional_scopes: list[GeographicScope] = []
    europe_plus_countries = filter_scope_countries(countries, EUROPE_PLUS_COUNTRIES)
    if europe_plus_countries:
        regional_scopes.append(
            GeographicScope(
                key="europe_plus",
                kind="region",
                label="Europe-plus",
                slug="europe-plus",
                countries=europe_plus_countries,
                parent_key="world",
                output_dir_parts=PUBLISHED_REPORT_EUROPE_PLUS_DIR,
                map_title="Europe-plus Evidence Surface",
            )
        )
    nordic_countries = filter_scope_countries(countries, NORDIC_COUNTRIES)
    if nordic_countries:
        regional_scopes.append(
            GeographicScope(
                key="nordic",
                kind="region",
                label="Nordic",
                slug="nordic",
                countries=nordic_countries,
                parent_key="europe_plus" if europe_plus_countries else "world",
                output_dir_parts=PUBLISHED_REPORT_NORDIC_DIR,
                map_title="Nordic Evidence Surface",
            )
        )
    country_scopes = tuple(
        GeographicScope(
            key=f"country:{slugify(country)}",
            kind="country",
            label=country,
            slug=slugify(country),
            countries=(country,),
            parent_key=geographic_parent_scope(country, has_europe_plus=bool(europe_plus_countries)),
            output_dir_parts=(*PUBLISHED_REPORT_COUNTRY_DIR, slugify(country)),
            map_title=f"{country} Evidence View",
        )
        for country in countries
    )
    return PublishedGeographyPlan(
        world_scope=world_scope,
        regional_scopes=tuple(regional_scopes),
        country_scopes=country_scopes,
    )


def geographic_parent_scope(country: str, *, has_europe_plus: bool) -> str:
    """Pick the nearest governed parent scope for one country output."""
    if country in NORDIC_COUNTRIES:
        return "nordic"
    if has_europe_plus and country in EUROPE_PLUS_COUNTRIES:
        return "europe_plus"
    return "world"


def scope_contains_country(scope: GeographicScope, country: str) -> bool:
    """Return whether one exact country belongs to a governed scope."""
    return scope.kind == "world" or country in scope.countries


def political_entity_countries(political_entity: str) -> tuple[str, ...]:
    """Resolve one site-facing political entity into explicit country ownership."""
    normalized = political_entity.strip()
    if not normalized:
        return ()
    territory_country = TERRITORY_COUNTRY_ASSIGNMENTS.get(normalized)
    if territory_country is not None:
        return (territory_country,)
    regional_countries = REGIONAL_COUNTRY_ASSIGNMENTS.get(normalized)
    if regional_countries is not None:
        return regional_countries
    return (normalized,)


def scope_contains_political_entity(
    scope: GeographicScope,
    political_entity: str,
) -> bool:
    """Return whether one political-entity label belongs inside a governed scope."""
    if scope.kind == "world":
        return True
    return any(
        scope_contains_country(scope, country)
        for country in political_entity_countries(political_entity)
    )


def render_geography_scope_registry_markdown(payload: dict[str, object]) -> str:
    """Render the governed publication-scope registry."""
    scope_rows = "\n".join(
        f"| {row['label']} | `{row['kind']}` | `{row['parent_key'] or '-'}` | `{row['directory']}` | `{row['country_count']}` |"
        for row in payload["scopes"]
    )
    return f"""# Publication Geography Registry

This registry defines the governed report scopes used by the checked-in
publication tree. Country and regional outputs are derived views, not separate
publication families with their own ad hoc rules.

## Scope Inventory

| Scope | Kind | Parent | Directory | Published countries |
| --- | --- | --- | --- | ---: |
{scope_rows}

## Europe-plus Definition

Europe-plus means EU countries plus Norway and Switzerland. The current report
tree only publishes subsets that have present data in the repository, but the
definition itself is stable and broader than the current Nordic release slice.
"""


def render_geography_subset_validation_markdown(payload: dict[str, object]) -> str:
    """Render the subset-validation report."""
    rows = "\n".join(
        f"| {row['scope']} | {row['parent_scope']} | `{str(row['country_subset_ok']).lower()}` | `{str(row['animal_subset_ok']).lower()}` | `{str(row['human_subset_ok']).lower()}` |"
        for row in payload["rows"]
    )
    return f"""# Publication Geography Subset Validation

This review proves that narrower publication scopes remain explainable subsets
of broader scopes instead of silently drifting into separate artifact families.

## Scope Checks

| Scope | Parent | Country subset | Animal subset | Human subset |
| --- | --- | --- | --- | --- |
{rows}
"""


def render_geography_onboarding_contract_markdown(payload: dict[str, object]) -> str:
    """Render the country-onboarding contract."""
    required_rows = "\n".join(
        f"- `{item}`" for item in payload["required_surfaces"]
    )
    return f"""# Country Onboarding Contract

Adding a new country should be mostly a matter of data presence and publication
configuration. It should not require one-off renderer surgery, file-tree churn,
or custom scope code.

## Required Surfaces

{required_rows}

## Current Configuration Points

- Published country roster: `packages/bijux-pollenomics/src/bijux_pollenomics/config.py`
- Geography scope plan: `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/geography.py`
- Country bundle generation: `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py`

## Example

The contract is satisfied when adding `Germany` only requires the country to be
present in the published country roster and the underlying data, while the
world, Europe-plus, and country outputs all derive automatically from the same
scope rules.
"""
