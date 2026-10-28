"""Animal atlas summaries retain source counts and visible scientific caveats."""

from __future__ import annotations

from typing import Any

from .....collection.contracts.cardinality import resolve_declared_count


def build_animal_atlas_summary(
    point_layers: list[dict[str, object]],
    animal_localities: tuple[Any, ...],
    animal_coordinate_review: Any,
    *,
    surface: Any,
) -> dict[str, object]:
    animal_layers = [
        layer
        for layer in point_layers
        if str(layer.get("group", "")).strip()
        in {
            "animal-domesticated-evidence",
            "animal-comparator-evidence",
            "animal-progenitor-evidence",
        }
    ]
    species_layers = [
        {
            "latin_name": str(layer.get("species_latin_name", "")),
            "common_name": str(layer.get("species_common_name", "")),
            "animal_scope": str(layer.get("animal_scope", "")),
            "locality_count": resolve_declared_count(
                layer,
                "count",
                field=(
                    "animal atlas layer "
                    f"{str(layer.get('key', '')).strip() or '<unknown>'} count"
                ),
                absent_default=len(surface._layer_features(layer)),
            ),
        }
        for layer in animal_layers
    ]
    temporal_windows = sorted(
        {
            str(feature.get("temporal_window_label", "")).strip()
            for layer in animal_layers
            for feature in surface._layer_features(layer)
            if str(feature.get("temporal_window_label", "")).strip()
        }
    )
    coordinate_confidence_counts: dict[str, int] = {}
    for layer in animal_layers:
        for feature in surface._layer_features(layer):
            confidence = str(feature.get("coordinate_confidence", "")).strip()
            if not confidence:
                continue
            coordinate_confidence_counts[confidence] = (
                coordinate_confidence_counts.get(confidence, 0) + 1
            )
    visible_caveats = [
        "Approximate or inferred coordinates remain visible with explicit warnings.",
        "Comparator-only evidence remains visible without being counted as domesticated-core support.",
        "Wild or progenitor evidence remains visible in its own scope and is not farming support.",
        "Weak or rejected support classes remain labeled in point popups instead of being silently hidden.",
        "Nordic relevance can remain regional rather than one exact named country.",
    ]
    return {
        "total_locality_points": len(animal_localities),
        "direct_coordinate_feature_count": animal_coordinate_review.direct_coordinate_feature_count,
        "named_site_geocoded_feature_count": animal_coordinate_review.named_site_geocoded_feature_count,
        "weaker_geography_feature_count": animal_coordinate_review.weaker_geography_feature_count,
        "total_species": len({row["latin_name"] for row in species_layers}),
        "domesticated_species_count": sum(
            1 for row in species_layers if row["animal_scope"] == "domesticated_core"
        ),
        "comparator_species_count": sum(
            1 for row in species_layers if row["animal_scope"] == "comparator"
        ),
        "wild_or_progenitor_species_count": sum(
            1
            for row in species_layers
            if row["animal_scope"] == "wild_or_progenitor_context"
        ),
        "layer_groups": [
            "Domesticated-core animal evidence",
            "Comparator animal evidence",
            "Wild and progenitor animal evidence",
        ]
        if species_layers
        else [],
        "filter_surfaces": [
            "Species focus",
            "Animal scope",
            "Coordinate confidence",
            "Temporal window",
            "Nordic animal leads only",
        ]
        if species_layers
        else [],
        "ui_surfaces": [
            "Animal evidence summary panel",
            "Citation-aware animal popups",
            "Species and confidence legend sections",
        ]
        if species_layers
        else [],
        "temporal_windows": temporal_windows,
        "coordinate_confidence_counts": coordinate_confidence_counts,
        "visible_caveats": visible_caveats if species_layers else [],
        "species_layers": species_layers,
    }
