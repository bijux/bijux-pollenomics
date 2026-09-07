"""Display-only atlas projection for animal source-sample chronology."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from ....core.temporal_semantics import build_temporal_semantics
from ...geography import GeographicScope, scope_contains_political_entity
from .contracts import (
    AnimalSampleChronologyContextProjection,
    AnimalSampleChronologyCorpus,
    AnimalSampleChronologyNode,
    JsonObject,
)

_GOVERNED_COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
_SPECIES_STYLES = {
    "Bos taurus": ("#92400e", "#78350f"),
    "Capra hircus": ("#0f766e", "#134e4a"),
    "Equus caballus": ("#8b5e34", "#5d3f21"),
    "Felis catus": ("#9333ea", "#6b21a8"),
    "Ovis aries": ("#15803d", "#14532d"),
    "Sus scrofa domesticus": ("#c2410c", "#7c2d12"),
}


def project_animal_sample_chronology_context(
    corpus: AnimalSampleChronologyCorpus,
    *,
    geography_scope: GeographicScope | None,
) -> AnimalSampleChronologyContextProjection:
    """Project source nodes without granting analytical or classification authority."""
    visible = tuple(
        node
        for node in corpus.nodes
        if geography_scope is None
        or scope_contains_political_entity(geography_scope, node.country_name or "")
    )
    visible_ids = {node.feature_id for node in visible}
    if len(visible_ids) != len(visible):
        raise ValueError("animal source chronology feature identities are not unique")
    point_layers = tuple(
        _species_layer(species, corpus.nodes, visible)
        for species in sorted(
            {node.project_species_latin_name for node in corpus.nodes}
        )
    )
    if len(point_layers) != 6:
        raise ValueError(
            "animal source chronology requires the six grounded species layers"
        )
    accountability = _accountability(corpus, visible, geography_scope)
    return AnimalSampleChronologyContextProjection(
        point_layers=point_layers,
        accountability=accountability,
        refusals=corpus.refusals,
        input_identity=corpus.input_identity,
    )


def _species_layer(
    species: str,
    global_nodes: Iterable[AnimalSampleChronologyNode],
    visible_nodes: Iterable[AnimalSampleChronologyNode],
) -> JsonObject:
    all_species_nodes = tuple(
        node for node in global_nodes if node.project_species_latin_name == species
    )
    nodes = tuple(
        node for node in visible_nodes if node.project_species_latin_name == species
    )
    if not all_species_nodes:
        raise ValueError(f"empty global animal chronology species layer: {species}")
    fill, stroke = _SPECIES_STYLES.get(species, ("#475569", "#1e293b"))
    common_name = all_species_nodes[0].project_species_common_name
    return {
        "key": f"animal-source-chronology-{_slug(species)}",
        "label": f"{common_name.title()} source-sample chronology",
        "count": len(nodes),
        "description": (
            "Display-only sample chronology joined from governed animal project "
            "sample identity, chronology, and site artifacts."
        ),
        "group": "animal-chronology-context",
        "semantic_role": "animal_source_chronology_context",
        "contribution_role": "display_only",
        "candidate_ranking_eligible": False,
        "scientific_classification_eligible": False,
        "scientific_selection_enabled": False,
        "propagation_status": "refused",
        "propagation_reason_code": "display_only_source_chronology",
        "edge_count": 0,
        "project_species_latin_name": species,
        "project_species_common_name": common_name,
        "species_attribution_basis": "governed_project_registry",
        "source_name": "Governed animal project sample chronology",
        "provenance_posture": "exact_project_sample_identity_join",
        "geometry_label": "Sample chronology points",
        "default_enabled": False,
        "applies_country_filter": True,
        "applies_time_filter": True,
        "circle_enabled": False,
        "style": {"fill": fill, "stroke": stroke},
        "features": [_feature(node) for node in nodes],
    }


def _feature(node: AnimalSampleChronologyNode) -> JsonObject:
    taxonomy_name = node.source_native_scientific_name or "Unavailable"
    comparability_posture = (
        "numeric_interval"
        if node.chronology_precision_posture
        in {"sample_precise_interval", "sample_precise_point"}
        else "numeric_interval_with_caveat"
    )
    comparison_note = (
        "This source-sample chronology supports interval filtering without "
        "implying direction, succession, or causation. Its time-window category "
        "is assigned from the source-normalized interval mean."
    )
    uncertainty_notes = (
        (
            (
                "The numeric interval remains displayable, but its source precision "
                "posture requires caution."
            ),
        )
        if comparability_posture == "numeric_interval_with_caveat"
        else ()
    )
    temporal_semantics = build_temporal_semantics(
        source_family="animal_adna_project_sample",
        evidence_class=node.chronology_evidence_class,
        precision_posture=node.chronology_precision_posture,
        comparability_posture=comparability_posture,
        time_start_bp=node.younger_bp,
        time_end_bp=node.older_bp,
        time_mean_bp=node.mean_bp,
        summary_label=node.chronology_text,
        comparison_note=comparison_note,
        provenance_path=node.chronology_provenance_path,
        provenance_locator=node.chronology_provenance_locator,
        provenance_excerpt=node.chronology_provenance_text,
        original_labels=(node.chronology_text,),
        normalized_labels=(f"{node.younger_bp}-{node.older_bp} BP",),
        uncertainty_notes=uncertainty_notes,
    ).as_dict()
    window_key = str(temporal_semantics["temporal_window_key"])
    window_label = str(temporal_semantics["temporal_window_label"])
    nordic_inclusion = node.country_name in _GOVERNED_COUNTRIES
    nordic_reason = _nordic_inclusion_reason(node.country_name)
    popup_rows: list[JsonObject] = [
        {"label": "Sample", "value": node.preferred_sample_label},
        {"label": "Project", "value": node.project_accession},
        {
            "label": "Project species attribution",
            "value": node.project_species_latin_name,
        },
        {"label": "Source-native taxonomy", "value": taxonomy_name},
        {"label": "Locality", "value": node.locality_text},
        {"label": "Chronology", "value": node.chronology_text},
        {
            "label": "Chronology precision",
            "value": node.chronology_precision_posture.replace("_", " "),
        },
        {"label": "Coordinate basis", "value": node.coordinate_basis},
        {"label": "Coordinate confidence", "value": node.coordinate_confidence},
        {
            "label": "Chronology source",
            "value": node.chronology_provenance_path,
        },
        {
            "label": "Chronology locator",
            "value": node.chronology_provenance_locator,
        },
        {"label": "Location source", "value": node.location_evidence_artifact_path},
        {"label": "Location locator", "value": node.location_evidence_locator},
        {
            "label": "Interpretation",
            "value": (
                "Display-only source chronology; not candidate-ranking, accepted "
                "classification, migration, or propagation evidence."
            ),
        },
    ]
    return {
        "feature_id": node.feature_id,
        "evidence_row_id": node.feature_id,
        "record_id": node.feature_id,
        "repo_stable_sample_id": node.repo_stable_sample_id,
        "project_accession": node.project_accession,
        "title": node.preferred_sample_label,
        "subtitle": "Animal source-sample chronology",
        "semantic_role": "animal_source_chronology_context",
        "contribution_role": "display_only",
        "candidate_ranking_eligible": False,
        "scientific_classification_eligible": False,
        "scientific_selection_enabled": False,
        "propagation_status": "refused",
        "propagation_reason_code": "display_only_source_chronology",
        "edge_count": 0,
        "latitude": node.latitude,
        "longitude": node.longitude,
        "latitude_text": node.latitude_text,
        "longitude_text": node.longitude_text,
        "country": node.country_name or "",
        "country_status": "assigned" if node.country_name else "unassigned",
        "nordic_inclusion": nordic_inclusion,
        "nordic_inclusion_reason": nordic_reason,
        "locality_text": node.locality_text,
        "site_name": node.site_name,
        "broader_geography": node.broader_geography,
        "project_species_latin_name": node.project_species_latin_name,
        "project_species_common_name": node.project_species_common_name,
        "species_attribution_basis": "governed_project_registry",
        "source_native_identity_kind": node.source_native_identity_kind,
        "source_native_tax_id": node.source_native_tax_id,
        "source_native_scientific_name": node.source_native_scientific_name,
        "source_native_taxonomy_status": node.source_native_taxonomy_status,
        "coordinate_basis": node.coordinate_basis,
        "coordinate_confidence": node.coordinate_confidence,
        "time_start_bp": node.younger_bp,
        "time_end_bp": node.older_bp,
        "time_mean_bp": node.mean_bp,
        "time_year_bp": node.mean_bp,
        "time_label": node.chronology_text,
        "temporal_window_key": window_key,
        "temporal_window_label": window_label,
        "temporal_comparability_posture": comparability_posture,
        "temporal_comparison_note": comparison_note,
        "temporal_window_assignment_policy": "source_normalized_interval_mean",
        "chronology_strength": node.chronology_strength,
        "chronology_evidence_class": node.chronology_evidence_class,
        "chronology_precision_posture": node.chronology_precision_posture,
        "chronology_normalization_status": node.chronology_normalization_status,
        "chronology_scope": "source_sample_interval",
        "dating_basis": node.dating_basis,
        "temporal_semantics": temporal_semantics,
        "sample_lineage_path": node.sample_lineage_path,
        "sample_lineage_locator": node.sample_lineage_locator,
        "sample_lineage_excerpt": node.sample_lineage_excerpt,
        "chronology_provenance_path": node.chronology_provenance_path,
        "chronology_provenance_kind": node.chronology_provenance_kind,
        "chronology_provenance_locator": node.chronology_provenance_locator,
        "chronology_provenance_text": node.chronology_provenance_text,
        "location_evidence_artifact_path": node.location_evidence_artifact_path,
        "location_evidence_artifact_kind": node.location_evidence_artifact_kind,
        "location_evidence_locator": node.location_evidence_locator,
        "location_evidence_text": node.location_evidence_text,
        "source_url": node.source_url,
        "popup_rows": popup_rows,
        "media_links": [],
    }


def _accountability(
    corpus: AnimalSampleChronologyCorpus,
    visible: tuple[AnimalSampleChronologyNode, ...],
    geography_scope: GeographicScope | None,
) -> JsonObject:
    countries = sorted(
        {node.country_name for node in corpus.nodes if node.country_name}
    )
    country_rows = [_country_row(country, corpus.nodes) for country in countries]
    unknown = tuple(node for node in corpus.nodes if node.country_name is None)
    country_rows.append(
        {
            "country_name": None,
            "node_count": len(unknown),
            "time_min_bp": min((node.younger_bp for node in unknown), default=None),
            "time_max_bp": max((node.older_bp for node in unknown), default=None),
        }
    )
    species_counts = Counter(node.project_species_latin_name for node in visible)
    project_counts = Counter(node.project_accession for node in visible)
    precision_counts = Counter(node.chronology_precision_posture for node in visible)
    coordinate_basis_counts = Counter(node.coordinate_basis for node in visible)
    coordinate_confidence_counts = Counter(
        node.coordinate_confidence for node in visible
    )
    native_available = sum(
        node.source_native_taxonomy_status == "available" for node in visible
    )
    return {
        "schema_version": "animal-sample-chronology-context-accountability.v1",
        "status": "reconciled",
        "scope": {
            "key": "global" if geography_scope is None else geography_scope.key,
            "kind": "world" if geography_scope is None else geography_scope.kind,
            "countries": []
            if geography_scope is None
            else list(geography_scope.countries),
        },
        "input_identity": corpus.input_identity.as_dict(),
        "source_counts": dict(corpus.source_counts),
        "refusal_counts": dict(corpus.refusal_counts),
        "refusal_count": len(corpus.refusals),
        "global_admitted_node_count": len(corpus.nodes),
        "projected_node_count": len(visible),
        "excluded_by_scope_count": len(corpus.nodes) - len(visible),
        "species_counts": dict(sorted(species_counts.items())),
        "project_counts": dict(sorted(project_counts.items())),
        "precision_counts": dict(sorted(precision_counts.items())),
        "coordinate_basis_counts": dict(sorted(coordinate_basis_counts.items())),
        "coordinate_confidence_counts": dict(
            sorted(coordinate_confidence_counts.items())
        ),
        "source_native_taxonomy": {
            "available_count": native_available,
            "unavailable_count": len(visible) - native_available,
            "denominator": len(visible),
        },
        "time_min_bp": min((node.younger_bp for node in visible), default=None),
        "time_max_bp": max((node.older_bp for node in visible), default=None),
        "country_rows": country_rows,
        "governed_country_rows": [
            _country_row(country, corpus.nodes) for country in _GOVERNED_COUNTRIES
        ],
        "analysis_policy": {
            "candidate_ranking_eligible": False,
            "scientific_classification_eligible": False,
            "propagation_status": "refused",
            "propagation_reason_code": "display_only_source_chronology",
            "edge_count": 0,
            "temporal_window_assignment_policy": "source_normalized_interval_mean",
        },
    }


def _country_row(
    country: str, nodes: Iterable[AnimalSampleChronologyNode]
) -> JsonObject:
    selected = tuple(node for node in nodes if node.country_name == country)
    return {
        "country_name": country,
        "node_count": len(selected),
        "time_min_bp": min((node.younger_bp for node in selected), default=None),
        "time_max_bp": max((node.older_bp for node in selected), default=None),
    }


def _nordic_inclusion_reason(country_name: str | None) -> str:
    if country_name in _GOVERNED_COUNTRIES:
        return "Source-sample country is one of Denmark, Finland, Norway, or Sweden."
    if country_name is None:
        return "Source-sample country is unassigned; Nordic inclusion is not inferred."
    return "Source-sample country is outside Denmark, Finland, Norway, and Sweden."


def _slug(value: str) -> str:
    slug = "-".join(
        "".join(
            character.casefold() if character.isalnum() else " " for character in value
        ).split()
    )
    if not slug:
        raise ValueError("animal chronology species slug is empty")
    return slug


__all__ = ["project_animal_sample_chronology_context"]
