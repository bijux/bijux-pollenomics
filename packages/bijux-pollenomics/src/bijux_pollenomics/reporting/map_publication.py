from __future__ import annotations

from dataclasses import dataclass

from ..collection.contracts.cardinality import resolve_declared_count
from .geography import GeographicScope
from .models import MultiCountryMapReport
from .presentation.text import escape_pipes

__all__ = [
    "MapScopePolicy",
    "build_map_point_traceability",
    "build_map_publication_contract",
    "map_allows_context_layer",
    "map_allows_fieldwork_layer",
    "render_map_point_traceability_markdown",
    "render_map_publication_contract_markdown",
    "resolve_map_scope_policy",
]


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
_ALL_SCOPE_KEYS = ("world", "europe_plus", "nordic", "custom")
_NORDIC_SCOPE_KEYS = ("nordic",)

_MAP_SCOPE_POLICIES: dict[str, MapScopePolicy] = {
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

_NORDIC_AND_CUSTOM_SCOPE_KEYS = set(_NORDIC_SCOPE_KEYS) | {"custom"}

_LAYER_SCOPE_RULES = {
    "aadr": _ALL_SCOPE_KEYS,
    "country-boundaries": _ALL_SCOPE_KEYS,
    "fieldwork-documentation": _NORDIC_AND_CUSTOM_SCOPE_KEYS,
    "landclim-sites": _NORDIC_SCOPE_KEYS,
    "neotoma-pollen": _NORDIC_SCOPE_KEYS,
    "sead-sites": _NORDIC_SCOPE_KEYS,
    "sead-temporal-evidence": _NORDIC_SCOPE_KEYS,
    "sweden-archaeology-site-discovery": _NORDIC_SCOPE_KEYS,
    "landclim-reveals-grid": _NORDIC_SCOPE_KEYS,
    "landclim-reveals-temporal-grid": _NORDIC_SCOPE_KEYS,
    "raa-archaeology": _NORDIC_SCOPE_KEYS,
    "raa-layer-metadata": _NORDIC_SCOPE_KEYS,
}

_SHARED_LAYER_KEYS = {"aadr"}
_REGION_FILTERED_LAYER_KEYS = {"country-boundaries"}
_SHARED_ANIMAL_LAYER_GROUPS = {
    "animal-domesticated-evidence",
    "animal-comparator-evidence",
    "animal-progenitor-evidence",
    "animal-chronology-context",
}
_ANIMAL_CHRONOLOGY_CONTEXT_POSTURE: dict[str, object] = {
    "group": "animal-chronology-context",
    "semantic_role": "animal_source_chronology_context",
    "contribution_role": "display_only",
    "default_enabled": False,
    "applies_country_filter": True,
    "applies_time_filter": True,
    "candidate_ranking_eligible": False,
    "scientific_classification_eligible": False,
    "scientific_selection_enabled": False,
    "propagation_status": "refused",
    "propagation_reason_code": "display_only_source_chronology",
    "edge_count": 0,
    "circle_enabled": False,
}
_ANIMAL_CHRONOLOGY_FEATURE_POSTURE = {
    field: _ANIMAL_CHRONOLOGY_CONTEXT_POSTURE[field]
    for field in (
        "semantic_role",
        "contribution_role",
        "candidate_ranking_eligible",
        "scientific_classification_eligible",
        "scientific_selection_enabled",
        "propagation_status",
        "propagation_reason_code",
        "edge_count",
    )
}
_ANIMAL_CHRONOLOGY_LAYER_FORBIDDEN_FIELDS = (
    "animal_scope",
    "classification_id",
    "classification_status",
    "scientific_signal_ids",
    "species_common_name",
    "species_latin_name",
    "taxon_alignment_status",
    "taxon_alignment_statuses",
)
_ANIMAL_CHRONOLOGY_FEATURE_FORBIDDEN_FIELDS = (
    "animal_scope",
    "classification_id",
    "classification_status",
    "scientific_signal_ids",
    "species_common_name",
    "species_latin_name",
    "taxon_alignment_status",
    "taxon_alignment_statuses",
)


def resolve_map_scope_policy(
    geography_scope: GeographicScope | None,
) -> MapScopePolicy:
    """Resolve the governed map presentation policy for one publication scope."""
    if geography_scope is None:
        return _MAP_SCOPE_POLICIES["custom"]
    return _MAP_SCOPE_POLICIES.get(geography_scope.key, _MAP_SCOPE_POLICIES["custom"])


def map_allows_context_layer(*, scope_key: str, layer_key: str) -> bool:
    """Return whether one external context layer belongs in the active map scope."""
    allowed_scope_keys = _LAYER_SCOPE_RULES.get(layer_key, _ALL_SCOPE_KEYS)
    return scope_key in allowed_scope_keys


def map_allows_fieldwork_layer(*, scope_key: str) -> bool:
    """Return whether the checked-in fieldwork overlay belongs in the active scope."""
    return map_allows_context_layer(
        scope_key=scope_key, layer_key="fieldwork-documentation"
    )


def build_map_publication_contract(
    *,
    report: MultiCountryMapReport,
    policy: MapScopePolicy,
    point_layers: list[dict[str, object]],
    polygon_layers: list[dict[str, object]],
    countries: tuple[str, ...],
    map_html_name: str,
    summary_json_name: str,
    traceability_json_name: str,
) -> dict[str, object]:
    """Build the governed publication contract for one shared map bundle."""
    layer_rows = [
        _serialize_layer_contract_row(layer, policy=policy)
        for layer in (*point_layers, *polygon_layers)
    ]
    role_counts = {
        role: sum(1 for row in layer_rows if row["publication_role"] == role)
        for role in (
            "shared_world_scale_layer",
            "region_filtered_layer",
            "scope_specific_overlay",
        )
    }
    return {
        "schema_version": "map-publication-contract.v1",
        "title": report.title,
        "scope_key": report.scope_key,
        "scope_label": report.scope_label or policy.label,
        "scope_kind": report.scope_kind,
        "parent_scope_key": report.parent_scope_key,
        "countries": list(countries),
        "default_basemap": policy.default_basemap,
        "initial_diameter_km": policy.initial_diameter_km,
        "minimum_bounds": [
            [policy.minimum_bounds[0][0], policy.minimum_bounds[0][1]],
            [policy.minimum_bounds[1][0], policy.minimum_bounds[1][1]],
        ],
        "scope_summary": policy.summary,
        "bounds_summary": policy.bounds_summary,
        "engine_summary": policy.engine_summary,
        "filter_surfaces": list(policy.filter_surfaces),
        "legend_sections": list(policy.legend_sections),
        "visible_caveats": list(policy.visible_caveats),
        "artifacts": {
            "map_html": map_html_name,
            "summary_json": summary_json_name,
            "point_traceability_json": traceability_json_name,
        },
        "role_counts": role_counts,
        "layer_rows": layer_rows,
    }


def render_map_publication_contract_markdown(payload: dict[str, object]) -> str:
    """Render a human-facing publication contract for one map bundle."""
    rows = (
        "\n".join(
            f"| {escape_pipes(str(row['label']))} | `{row['publication_role']}` | {escape_pipes(str(row['source_name']))} | {escape_pipes(str(row['coverage_label']))} | `{row['count']}` |"
            for row in payload["layer_rows"]
        )
        or "| No visible layers | `-` | - | - | `0` |"
    )
    filter_lines = (
        "\n".join(
            f"- {escape_pipes(str(label))}" for label in payload["filter_surfaces"]
        )
        or "- No governed filter surfaces"
    )
    legend_lines = (
        "\n".join(
            f"- {escape_pipes(str(label))}" for label in payload["legend_sections"]
        )
        or "- No governed legend sections"
    )
    caveat_lines = (
        "\n".join(
            f"- {escape_pipes(str(label))}" for label in payload["visible_caveats"]
        )
        or "- No governed caveats"
    )
    return f"""# {payload["title"]} Map Publication Contract

{payload["scope_summary"]}

## Engine Decision

{payload["engine_summary"]}

## Scope Posture

- Scope key: `{payload["scope_key"]}`
- Scope kind: `{payload["scope_kind"]}`
- Parent scope: `{payload["parent_scope_key"] or "-"}`
- Default basemap: `{payload["default_basemap"]}`
- Default distance circle diameter: `{payload["initial_diameter_km"]} km`

{payload["bounds_summary"]}

## Layer Inventory

| Layer | Publication role | Source | Coverage posture | Visible records |
| --- | --- | --- | --- | ---: |
{rows}

## Filter Surfaces

{filter_lines}

## Legend Sections

{legend_lines}

## Caveats

{caveat_lines}
"""


def build_map_point_traceability(
    *,
    report: MultiCountryMapReport,
    point_layers: list[dict[str, object]],
) -> dict[str, object]:
    """Build one scope-aware traceability ledger for every visible point layer."""
    rows: list[dict[str, object]] = []
    for layer in point_layers:
        layer_key = str(layer.get("key", "")).strip()
        layer_label = str(layer.get("label", "")).strip()
        source_name = str(layer.get("source_name", "")).strip()
        group = str(layer.get("group", "")).strip()
        source_artifact = str(layer.get("traceability_artifact", "")).strip()
        source_reference = str(layer.get("traceability_reference", "")).strip()
        features = layer.get("features")
        if not isinstance(features, list):
            continue
        for index, feature in enumerate(features, start=1):
            if not isinstance(feature, dict):
                continue
            record_id = (
                str(feature.get("evidence_row_id", "")).strip()
                or str(feature.get("title", "")).strip()
                or f"{layer_key}:{index}"
            )
            rows.append(
                {
                    "scope_key": report.scope_key,
                    "scope_label": report.scope_label or report.title,
                    "layer_key": layer_key,
                    "layer_label": layer_label,
                    "group": group,
                    "source_name": source_name,
                    "source_artifact": source_artifact,
                    "source_reference": source_reference,
                    "record_id": record_id,
                    "title": str(feature.get("title", "")).strip(),
                    "country": str(feature.get("country", "")).strip(),
                    "source_url": str(feature.get("source_url", "")).strip(),
                    "species_latin_name": str(
                        feature.get("species_latin_name", "")
                    ).strip(),
                    "animal_scope": str(feature.get("animal_scope", "")).strip(),
                    "coordinate_confidence": str(
                        feature.get("coordinate_confidence", "")
                    ).strip(),
                }
            )
    layer_counts = {
        layer_key: sum(1 for row in rows if row["layer_key"] == layer_key)
        for layer_key in sorted({row["layer_key"] for row in rows})
    }
    return {
        "schema_version": "map-point-traceability.v1",
        "title": report.title,
        "scope_key": report.scope_key,
        "scope_label": report.scope_label or report.title,
        "row_count": len(rows),
        "layer_counts": layer_counts,
        "rows": rows,
    }


def render_map_point_traceability_markdown(payload: dict[str, object]) -> str:
    """Render a compact human-facing summary of bundle point traceability."""
    rows = (
        "\n".join(
            f"| {escape_pipes(str(row['layer_label']))} | {escape_pipes(str(row['record_id']))} | {escape_pipes(str(row['country'] or '-'))} | {escape_pipes(str(row['source_artifact'] or row['source_reference'] or '-'))} |"
            for row in payload["rows"][:40]
        )
        or "| No visible point rows | - | - | - |"
    )
    return f"""# {payload["title"]} Point Traceability

This ledger keeps one governed traceability chain for every visible point layer in
the map bundle. It is a publication-facing inspection surface, not a replacement
for deeper source-family review files.

## Summary

- Scope key: `{payload["scope_key"]}`
- Visible point rows: `{payload["row_count"]}`
- Visible point layers: `{len(payload["layer_counts"])}`

## Example Rows

| Layer | Record ID | Country | Traceability surface |
| --- | --- | --- | --- |
{rows}
"""


def _serialize_layer_contract_row(
    layer: dict[str, object],
    *,
    policy: MapScopePolicy,
) -> dict[str, object]:
    layer_key = str(layer.get("key", "")).strip()
    layer_group = str(layer.get("group", "")).strip()
    animal_chronology_context = _animal_chronology_context_posture(layer)
    features = layer.get("features")
    feature_count = len(features) if isinstance(features, list) else 0
    count = resolve_declared_count(
        layer,
        "count",
        field=f"map layer {layer_key or '<unknown>'} count",
        absent_default=feature_count,
    )
    if isinstance(features, list) and count != feature_count:
        raise ValueError(
            f"map layer {layer_key or '<unknown>'} count does not match its features"
        )
    row: dict[str, object] = {
        "key": layer_key,
        "label": str(layer.get("label", "")).strip(),
        "source_name": str(layer.get("source_name", "")).strip(),
        "coverage_label": str(layer.get("coverage_label", "")).strip(),
        "count": count,
        "publication_role": _publication_role_for(layer_key, layer_group=layer_group),
        "scope_visibility": "scope_owned"
        if layer_key in _LAYER_SCOPE_RULES
        else "shared_default",
        "default_enabled": bool(layer.get("default_enabled", False)),
        "applies_country_filter": bool(layer.get("applies_country_filter", False)),
        "applies_time_filter": bool(layer.get("applies_time_filter", False)),
        "scope_caveat": _scope_caveat_for(
            layer_key,
            layer_group=layer_group,
            policy=policy,
        ),
    }
    if animal_chronology_context is not None:
        row.update(animal_chronology_context)
    return row


def _animal_chronology_context_posture(
    layer: dict[str, object],
) -> dict[str, object] | None:
    """Return the exact display-only posture or reject a contradictory layer."""
    identified = (
        layer.get("group") == "animal-chronology-context"
        or layer.get("semantic_role") == "animal_source_chronology_context"
    )
    if not identified:
        return None
    differing = sorted(
        field
        for field, expected in _ANIMAL_CHRONOLOGY_CONTEXT_POSTURE.items()
        if layer.get(field) != expected
    )
    if differing:
        raise ValueError(
            "animal source chronology context posture differs: " + ", ".join(differing)
        )
    species_fields = (
        "project_species_latin_name",
        "project_species_common_name",
        "species_attribution_basis",
    )
    if any(
        not isinstance(layer.get(field), str) or not str(layer[field]).strip()
        for field in species_fields
    ):
        raise ValueError("animal source chronology project species posture differs")
    if layer["species_attribution_basis"] != "governed_project_registry":
        raise ValueError("animal source chronology project species posture differs")
    forbidden_layer_fields = sorted(
        field for field in _ANIMAL_CHRONOLOGY_LAYER_FORBIDDEN_FIELDS if field in layer
    )
    if forbidden_layer_fields:
        raise ValueError(
            "animal source chronology layer exposes forbidden scientific fields: "
            + ", ".join(forbidden_layer_fields)
        )
    features = layer.get("features")
    if not isinstance(features, list):
        raise ValueError("animal source chronology features are invalid")
    seen_feature_ids: set[str] = set()
    seen_sample_identities: set[tuple[str, str]] = set()
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError("animal source chronology feature is invalid")
        feature_differences = sorted(
            field
            for field, expected in _ANIMAL_CHRONOLOGY_FEATURE_POSTURE.items()
            if feature.get(field) != expected
        )
        if feature_differences:
            raise ValueError(
                "animal source chronology feature posture differs: "
                + ", ".join(feature_differences)
            )
        forbidden_feature_fields = sorted(
            field
            for field in _ANIMAL_CHRONOLOGY_FEATURE_FORBIDDEN_FIELDS
            if field in feature
        )
        if forbidden_feature_fields:
            raise ValueError(
                "animal source chronology feature exposes forbidden scientific fields: "
                + ", ".join(forbidden_feature_fields)
            )
        if any(feature.get(field) != layer.get(field) for field in species_fields):
            raise ValueError("animal source chronology feature species differs")
        feature_id = feature.get("feature_id")
        project_accession = feature.get("project_accession")
        sample_id = feature.get("repo_stable_sample_id")
        if (
            not isinstance(feature_id, str)
            or not feature_id.strip()
            or not isinstance(project_accession, str)
            or not project_accession.strip()
            or not isinstance(sample_id, str)
            or not sample_id.strip()
        ):
            raise ValueError("animal source chronology feature identity is invalid")
        sample_identity = (project_accession, sample_id)
        if feature_id in seen_feature_ids or sample_identity in seen_sample_identities:
            raise ValueError("animal source chronology feature identity is duplicated")
        seen_feature_ids.add(feature_id)
        seen_sample_identities.add(sample_identity)
    return {
        **_ANIMAL_CHRONOLOGY_CONTEXT_POSTURE,
        **{field: layer[field] for field in species_fields},
    }


def _publication_role_for(layer_key: str, *, layer_group: str) -> str:
    if layer_key in _SHARED_LAYER_KEYS or layer_group in _SHARED_ANIMAL_LAYER_GROUPS:
        return "shared_world_scale_layer"
    if layer_key in _REGION_FILTERED_LAYER_KEYS:
        return "region_filtered_layer"
    return "scope_specific_overlay"


def _scope_caveat_for(
    layer_key: str,
    *,
    layer_group: str,
    policy: MapScopePolicy,
) -> str:
    if layer_group == "animal-chronology-context":
        return (
            "Shared display-only source chronology across governed scopes; excluded "
            "from candidate ranking, accepted classification, and propagation."
        )
    if layer_key in _SHARED_LAYER_KEYS or layer_group in _SHARED_ANIMAL_LAYER_GROUPS:
        return "Shared evidence layer across every governed scope."
    if layer_key in _REGION_FILTERED_LAYER_KEYS:
        return (
            "Derived filter framing layer that follows the active scope country roster."
        )
    if policy.key != "nordic":
        return "This overlay is intentionally withheld outside Nordic scope."
    return "This overlay is visible only in Nordic scope because its source family is still Nordic-specific."
