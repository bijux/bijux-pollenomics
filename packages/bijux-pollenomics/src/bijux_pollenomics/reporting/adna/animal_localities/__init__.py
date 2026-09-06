"""Traceable animal aDNA locality publication facade."""

from __future__ import annotations

from pathlib import Path

from ....adna import (
    AdnaLocalitySummary as AdnaLocalitySummary,
)
from ....adna import (
    build_species_support_matrix,
)
from ....adna.workflow.paths import adna_species_dir
from ...geography import GeographicScope, scope_contains_political_entity
from ...presentation.text import slugify
from ..atlas_evidence_rows import (
    AnimalAtlasCoordinateReview as AnimalAtlasCoordinateReview,
)
from ..atlas_evidence_rows import (
    AnimalAtlasEvidenceRow as AnimalAtlasEvidenceRow,
)
from ..atlas_evidence_rows import (
    build_tracked_animal_atlas_coordinate_review,
    build_tracked_animal_atlas_evidence_rows,
    load_tracked_animal_mappable_localities,
)
from . import features as _features
from . import layers as _layers
from . import publication as _publication
from . import review as _review
from .assembly import (
    _features_have_time_filter,
    _group_rows_by_species_and_scope,
    _partition_features,
    _select_evidence_rows,
    _select_localities,
)
from .model import AnimalAtlasBundle as AnimalAtlasBundle

_build_point_feature = _features._build_point_feature
_temporal_semantics_for = _features._temporal_semantics_for
_warning_rows_for = _features._warning_rows_for
_SPECIES_STYLES = _layers._SPECIES_STYLES
_alpha = _layers._alpha
_animal_scope_for = _layers._animal_scope_for
_layer_description_for = _layers._layer_description_for
_layer_group_for = _layers._layer_group_for
_layer_style_for = _layers._layer_style_for
_write_animal_atlas_evidence_csv = _publication._write_animal_atlas_evidence_csv
_write_animal_atlas_evidence_json = _publication._write_animal_atlas_evidence_json
_write_animal_point_traceability_json = (
    _publication._write_animal_point_traceability_json
)
_write_feature_collection = _publication._write_feature_collection
_load_dataset_review = _review._load_dataset_review
_load_review_lookup = _review._load_review_lookup
_optional_str = _review._optional_str

__all__ = [
    "AnimalAtlasBundle",
    "build_tracked_animal_atlas_bundle",
    "load_tracked_animal_localities",
]


def load_tracked_animal_localities(data_root: Path) -> tuple[AdnaLocalitySummary, ...]:
    """Load only the tracked non-human locality rows eligible for point publication."""
    return load_tracked_animal_mappable_localities(data_root)


def build_tracked_animal_atlas_bundle(
    *,
    data_root: Path,
    output_dir: Path,
    atlas_slug: str,
    geography_scope: GeographicScope | None = None,
) -> AnimalAtlasBundle:
    """Build staged atlas point layers from traceable animal atlas evidence rows."""
    species_dir = adna_species_dir(Path(data_root))
    evidence_rows = _select_evidence_rows(
        data_root,
        geography_scope,
        load_rows=build_tracked_animal_atlas_evidence_rows,
        scope_contains=scope_contains_political_entity,
    )
    coordinate_review = build_tracked_animal_atlas_coordinate_review(evidence_rows)
    visible_localities = _select_localities(
        data_root,
        geography_scope,
        load_localities=load_tracked_animal_mappable_localities,
        scope_contains=scope_contains_political_entity,
    )
    grouped_rows = _group_rows_by_species_and_scope(evidence_rows)
    species_slug_lookup = {
        species.latin_name: species.slug
        for species in build_species_support_matrix()
        if species.latin_name != "Homo sapiens"
    }

    point_layers: list[dict[str, object]] = []
    all_features: list[dict[str, object]] = []
    domesticated_features: list[dict[str, object]] = []
    comparator_features: list[dict[str, object]] = []
    progenitor_features: list[dict[str, object]] = []
    for (species_name, animal_scope), species_rows in sorted(grouped_rows.items()):
        species_slug = species_slug_lookup.get(species_name)
        if species_slug is None:
            continue
        species_root = species_dir / species_slug
        dataset_review = _load_dataset_review(species_root)
        review_lookup = _load_review_lookup(species_root)
        layer_key = f"animal-{slugify(species_slug)}"
        if animal_scope != _animal_scope_for(dataset_review):
            layer_key = f"{layer_key}-{slugify(animal_scope)}"
        layer_group = _layer_group_for(animal_scope)
        style = _layer_style_for(species_name)
        features = [
            _build_point_feature(
                row=row,
                dataset_review=dataset_review,
                review_lookup=review_lookup,
            )
            for row in species_rows
        ]
        features.sort(
            key=lambda feature: (
                not bool(feature.get("nordic_inclusion")),
                str(feature.get("title", "")),
            )
        )
        point_layers.append(
            {
                "key": layer_key,
                "label": (
                    f"{species_rows[0].species_common_name.title()} aDNA site evidence "
                    f"({animal_scope.replace('_', ' ')})"
                ),
                "count": len(features),
                "description": _layer_description_for(
                    species_common_name=species_rows[0].species_common_name,
                    dataset_review=dataset_review,
                    animal_scope=animal_scope,
                ),
                "group": layer_group,
                "atlas_layer_key": layer_key,
                "species_latin_name": species_rows[0].species_latin_name,
                "species_common_name": species_rows[0].species_common_name,
                "animal_scope": animal_scope,
                "contribution_role": "direct",
                "provenance_posture": "sample_backed_or_site_backed_atlas_evidence_rows",
                "source_name": "Tracked animal aDNA localities",
                "coverage_label": (
                    "Mapped animal features staged from traceable evidence rows built from "
                    "species-owned sample, site, coordinate, and citation surfaces."
                ),
                "geometry_label": "Point records",
                "default_enabled": True,
                "applies_country_filter": True,
                "applies_time_filter": _features_have_time_filter(features),
                "circle_enabled": True,
                "style": {
                    **style,
                    "circleStroke": _alpha(style["stroke"], 0.42),
                    "circleFill": _alpha(style["fill"], 0.10),
                },
                "features": features,
            }
        )
        all_features.extend(features)
        _partition_features(
            layer_group=layer_group,
            features=features,
            domesticated=domesticated_features,
            comparator=comparator_features,
            progenitor=progenitor_features,
        )

    _write_feature_collection(
        output_dir / f"{atlas_slug}_animal_localities.geojson",
        features=all_features,
        layer_key="animal-localities",
        layer_label="Animal aDNA atlas evidence",
        description="All traceable animal atlas evidence rows included in the atlas bundle.",
    )
    _write_feature_collection(
        output_dir / f"{atlas_slug}_domesticated_animal_localities.geojson",
        features=domesticated_features,
        layer_key="domesticated-animal-localities",
        layer_label="Domesticated-core animal aDNA atlas evidence",
        description="Domesticated-core animal atlas evidence rows included in the atlas bundle.",
    )
    _write_feature_collection(
        output_dir / f"{atlas_slug}_comparator_animal_localities.geojson",
        features=comparator_features,
        layer_key="comparator-animal-localities",
        layer_label="Comparator animal aDNA atlas evidence",
        description="Comparator animal atlas evidence rows included in the atlas bundle.",
    )
    _write_feature_collection(
        output_dir / f"{atlas_slug}_progenitor_animal_localities.geojson",
        features=progenitor_features,
        layer_key="progenitor-animal-localities",
        layer_label="Wild and progenitor animal aDNA atlas evidence",
        description=(
            "Wild or progenitor animal atlas evidence rows kept separate from "
            "domesticated-core and comparator products."
        ),
    )
    _write_animal_atlas_evidence_csv(
        output_dir / f"{atlas_slug}_animal_atlas_evidence.csv",
        evidence_rows,
    )
    _write_animal_atlas_evidence_json(
        output_dir / f"{atlas_slug}_animal_atlas_evidence.json",
        evidence_rows,
    )
    _write_animal_point_traceability_json(
        output_dir / f"{atlas_slug}_animal_point_traceability.json",
        evidence_rows,
    )
    return AnimalAtlasBundle(
        point_layers=tuple(point_layers),
        evidence_rows=evidence_rows,
        localities=visible_localities,
        coordinate_review=coordinate_review,
        extra_artifacts=(
            ("Animal locality GeoJSON", f"{atlas_slug}_animal_localities.geojson"),
            (
                "Domesticated-core animal locality GeoJSON",
                f"{atlas_slug}_domesticated_animal_localities.geojson",
            ),
            (
                "Comparator animal locality GeoJSON",
                f"{atlas_slug}_comparator_animal_localities.geojson",
            ),
            (
                "Wild and progenitor animal locality GeoJSON",
                f"{atlas_slug}_progenitor_animal_localities.geojson",
            ),
            ("Animal atlas evidence CSV", f"{atlas_slug}_animal_atlas_evidence.csv"),
            ("Animal atlas evidence JSON", f"{atlas_slug}_animal_atlas_evidence.json"),
            (
                "Animal point traceability JSON",
                f"{atlas_slug}_animal_point_traceability.json",
            ),
        ),
    )
