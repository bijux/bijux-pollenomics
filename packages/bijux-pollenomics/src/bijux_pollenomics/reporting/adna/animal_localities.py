from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path

from ...adna import AdnaLocalitySummary, build_species_support_matrix
from ...adna.paths import adna_species_dir
from ..geography import (
    GeographicScope,
    NORDIC_COUNTRIES,
    scope_contains_political_entity,
)
from ..presentation.text import slugify
from .atlas_evidence_rows import (
    AnimalAtlasCoordinateReview,
    AnimalAtlasEvidenceRow,
    build_tracked_animal_atlas_coordinate_review,
    build_tracked_animal_atlas_evidence_rows,
    load_tracked_animal_mappable_localities,
)

__all__ = [
    "AnimalAtlasBundle",
    "build_tracked_animal_atlas_bundle",
    "load_tracked_animal_localities",
]

_SPECIES_STYLES = {
    "Equus caballus": {"fill": "#8b5e34", "stroke": "#5d3f21"},
    "Sus scrofa domesticus": {"fill": "#c2410c", "stroke": "#7c2d12"},
    "Ovis aries": {"fill": "#15803d", "stroke": "#14532d"},
    "Bos taurus": {"fill": "#92400e", "stroke": "#78350f"},
    "Capra hircus": {"fill": "#0f766e", "stroke": "#134e4a"},
    "Canis lupus familiaris": {"fill": "#1d4ed8", "stroke": "#1e3a8a"},
    "Felis catus": {"fill": "#9333ea", "stroke": "#6b21a8"},
    "Camelus dromedarius": {"fill": "#b45309", "stroke": "#78350f"},
    "Rangifer tarandus": {"fill": "#0369a1", "stroke": "#0c4a6e"},
    "Equus asinus": {"fill": "#6d28d9", "stroke": "#4c1d95"},
}


@dataclass(frozen=True)
class AnimalAtlasBundle:
    point_layers: tuple[dict[str, object], ...]
    evidence_rows: tuple[AnimalAtlasEvidenceRow, ...]
    localities: tuple[AdnaLocalitySummary, ...]
    coordinate_review: AnimalAtlasCoordinateReview
    extra_artifacts: tuple[tuple[str, str], ...]


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
    evidence_rows = tuple(
        row
        for row in build_tracked_animal_atlas_evidence_rows(data_root)
        if geography_scope is None
        or scope_contains_political_entity(geography_scope, row.political_entity)
    )
    coordinate_review = build_tracked_animal_atlas_coordinate_review(evidence_rows)
    visible_localities = tuple(
        locality
        for locality in load_tracked_animal_mappable_localities(data_root)
        if geography_scope is None
        or scope_contains_political_entity(
            geography_scope,
            str(locality.identity.political_entity or ""),
        )
    )
    grouped_rows: dict[str, list[AnimalAtlasEvidenceRow]] = {}
    for row in evidence_rows:
        grouped_rows.setdefault(row.species_latin_name, []).append(row)
    species_slug_lookup = {
        species.latin_name: species.slug
        for species in build_species_support_matrix()
        if species.latin_name != "Homo sapiens"
    }

    point_layers: list[dict[str, object]] = []
    all_features: list[dict[str, object]] = []
    domesticated_features: list[dict[str, object]] = []
    comparator_features: list[dict[str, object]] = []
    for species_name, species_rows in sorted(grouped_rows.items()):
        species_slug = species_slug_lookup.get(species_name)
        if species_slug is None:
            continue
        species_root = species_dir / species_slug
        dataset_review = _load_dataset_review(species_root)
        review_lookup = _load_review_lookup(species_root)
        layer_key = f"animal-{slugify(species_slug)}"
        layer_group = _layer_group_for(dataset_review.get("product_role"))
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
                "label": f"{species_rows[0].species_common_name.title()} aDNA site evidence",
                "count": len(features),
                "description": _layer_description_for(
                    species_common_name=species_rows[0].species_common_name,
                    dataset_review=dataset_review,
                ),
                "group": layer_group,
                "atlas_layer_key": layer_key,
                "species_latin_name": species_rows[0].species_latin_name,
                "species_common_name": species_rows[0].species_common_name,
                "animal_scope": _animal_scope_for(dataset_review),
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
                "applies_time_filter": any(
                    feature.get("time_start_bp") is not None
                    or feature.get("time_end_bp") is not None
                    or feature.get("time_mean_bp") is not None
                    for feature in features
                ),
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
        if layer_group == "animal-comparator-evidence":
            comparator_features.extend(features)
        else:
            domesticated_features.extend(features)

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
            ("Animal atlas evidence CSV", f"{atlas_slug}_animal_atlas_evidence.csv"),
            ("Animal atlas evidence JSON", f"{atlas_slug}_animal_atlas_evidence.json"),
            ("Animal point traceability JSON", f"{atlas_slug}_animal_point_traceability.json"),
        ),
    )


def _load_dataset_review(species_root: Path) -> dict[str, object]:
    payload = json.loads(
        (species_root / "reports" / "support_summary.json").read_text(encoding="utf-8")
    )
    review = payload.get("dataset_review", {})
    if not isinstance(review, dict):
        raise ValueError(f"Dataset review missing for {species_root}")
    return review


def _load_review_lookup(species_root: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(
        (species_root / "review" / "species_review.json").read_text(encoding="utf-8")
    )
    lookup: dict[str, dict[str, str]] = {}
    for key in (
        "accepted_projects",
        "rejected_projects",
        "too_weak_projects",
        "comparator_projects",
        "nordic_unmapped_leads",
    ):
        rows = payload.get(key, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            accession = str(row.get("project_accession", "")).strip()
            if accession:
                lookup[accession] = {
                    "support_class": str(row.get("support_class", "")),
                    "reason": str(row.get("reason", "")),
                    "paper_title": _optional_str(row.get("paper_title")) or "",
                    "paper_doi": _optional_str(row.get("paper_doi")) or "",
                    "nordic_relevance": str(row.get("nordic_relevance", "")),
                    "nordic_relevance_reason": str(row.get("nordic_relevance_reason", "")),
                }
    return lookup


def _build_point_feature(
    *,
    row: AnimalAtlasEvidenceRow,
    dataset_review: dict[str, object],
    review_lookup: dict[str, dict[str, str]],
) -> dict[str, object]:
    primary_accession = row.primary_project_accession
    review = review_lookup.get(primary_accession, {})
    warning_rows = _warning_rows_for(
        row=row,
        dataset_review=dataset_review,
        review=review,
    )
    scope = _animal_scope_for(dataset_review)
    temporal_semantics = _temporal_semantics_for(row)
    temporal_window_label = str(
        temporal_semantics.get("temporal_window_label", "")
    ).strip()
    popup_rows = [
        {"label": "Species", "value": row.species_latin_name},
        {"label": "Support class", "value": row.support_class},
        {"label": "Animal scope", "value": scope.replace("_", " ")},
        {"label": "Mapped sample count", "value": str(row.sample_count)},
        {"label": "Mapped sample identifiers", "value": ", ".join(row.sample_record_ids)},
        {"label": "Project accession", "value": ", ".join(row.project_accessions) or "No project accession"},
        {"label": "Paper title", "value": row.paper_title},
        {"label": "Paper DOI", "value": row.paper_doi},
        {"label": "Publication year", "value": row.publication_year},
        {"label": "Journal", "value": row.journal_title},
        {"label": "Chronology", "value": row.chronology.original_text},
        {"label": "Temporal window", "value": temporal_window_label},
        {
            "label": "Temporal comparison posture",
            "value": str(
                temporal_semantics.get("comparability_posture", "")
            ).replace("_", " "),
        },
        {
            "label": "Temporal comparison note",
            "value": str(temporal_semantics.get("comparison_note", "")).strip(),
        },
        {"label": "Support note", "value": row.support_note},
        {"label": "Coordinate basis", "value": row.coordinate_basis},
        {"label": "Coordinate confidence", "value": row.coordinate_confidence},
        {"label": "Coordinate method", "value": row.geocoding_method},
        {"label": "Coordinate gazetteer", "value": row.geocoder_or_gazetteer},
        {"label": "Original place text", "value": row.original_place_text},
        {"label": "Resolved place text", "value": row.resolved_place_text},
        {"label": "Supplementary location source", "value": ", ".join(row.supplementary_sources)},
        {"label": "Coordinate rationale", "value": row.confidence_rationale},
        {"label": "Source locator", "value": row.source_locator},
        {"label": "Source support status", "value": row.source_support_status},
        {"label": "Source evidence text", "value": row.exact_source_text},
        {
            "label": "Nordic relevance",
            "value": "nordic_lead" if row.nordic_inclusion else "non_nordic_or_comparator",
        },
        {"label": "Nordic note", "value": row.nordic_inclusion_reason},
        {"label": "Interpretation", "value": row.interpretation_note},
    ]
    popup_rows.extend(warning_rows)
    return {
        "feature_id": row.feature_id,
        "evidence_row_id": row.evidence_row_id,
        "site_record_id": row.site_record_id,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "country": row.political_entity,
        "title": row.locality,
        "subtitle": f"{row.species_common_name.title()} atlas evidence row",
        "species_latin_name": row.species_latin_name,
        "species_common_name": row.species_common_name,
        "evidence_role": "direct",
        "animal_scope": scope,
        "support_class": row.support_class,
        "temporal_semantics": temporal_semantics,
        "temporal_window_key": temporal_semantics["temporal_window_key"],
        "temporal_window_label": temporal_window_label,
        "temporal_comparability_posture": temporal_semantics[
            "comparability_posture"
        ],
        "temporal_comparison_note": temporal_semantics["comparison_note"],
        "nordic_inclusion": row.nordic_inclusion,
        "nordic_inclusion_reason": row.nordic_inclusion_reason,
        "coordinate_basis": row.coordinate_basis,
        "coordinate_confidence": row.coordinate_confidence,
        "sample_count": row.sample_count,
        "sample_record_ids": list(row.sample_record_ids),
        "sample_group_ids": list(row.sample_group_ids),
        "sample_namespace": row.sample_namespace,
        "paper_title": row.paper_title,
        "publication_year": row.publication_year,
        "paper_doi": row.paper_doi,
        "journal_title": row.journal_title,
        "supplementary_sources": list(row.supplementary_sources),
        "project_accessions": list(row.project_accessions),
        "primary_project_accession": row.primary_project_accession,
        "inclusion_statuses": list(row.inclusion_statuses),
        "inclusion_notes": list(row.inclusion_notes),
        "latitude_text": row.latitude_text,
        "longitude_text": row.longitude_text,
        "geocoding_method": row.geocoding_method,
        "geocoder_or_gazetteer": row.geocoder_or_gazetteer,
        "confidence_rationale": row.confidence_rationale,
        "original_place_text": row.original_place_text,
        "resolved_place_text": row.resolved_place_text,
        "source_artifact_path": row.source_artifact_path,
        "source_artifact_kind": row.source_artifact_kind,
        "source_locator": row.source_locator,
        "source_support_status": row.source_support_status,
        "exact_source_text": row.exact_source_text,
        "popup_rows": [item for item in popup_rows if item["value"]],
        "source_url": row.paper_url,
        "media_links": [],
        "time_start_bp": row.chronology.time_start_bp,
        "time_end_bp": row.chronology.time_end_bp,
        "time_mean_bp": row.chronology.time_mean_bp,
        "time_year_bp": row.chronology.time_mean_bp,
        "time_label": row.chronology.original_text,
    }


def _write_feature_collection(
    path: Path,
    *,
    features: list[dict[str, object]],
    layer_key: str,
    layer_label: str,
    description: str,
) -> None:
    geojson_features = []
    for feature in features:
        geojson_features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [feature["longitude"], feature["latitude"]],
                },
                "properties": {
                    "name": feature["title"],
                    "feature_id": feature["feature_id"],
                    "evidence_row_id": feature["evidence_row_id"],
                    "site_record_id": feature["site_record_id"],
                    "category": feature["subtitle"],
                    "country": feature["country"],
                    "layer_key": layer_key,
                    "layer_label": layer_label,
                    "source_url": feature["source_url"],
                    "popup_rows": feature["popup_rows"],
                    "species_latin_name": feature["species_latin_name"],
                    "species_common_name": feature["species_common_name"],
                    "animal_scope": feature["animal_scope"],
                    "support_class": feature["support_class"],
                    "temporal_semantics": feature["temporal_semantics"],
                    "temporal_window_key": feature["temporal_window_key"],
                    "temporal_window_label": feature["temporal_window_label"],
                    "temporal_comparability_posture": feature[
                        "temporal_comparability_posture"
                    ],
                    "temporal_comparison_note": feature["temporal_comparison_note"],
                    "nordic_inclusion": feature["nordic_inclusion"],
                    "nordic_inclusion_reason": feature["nordic_inclusion_reason"],
                    "coordinate_basis": feature["coordinate_basis"],
                    "coordinate_confidence": feature["coordinate_confidence"],
                    "sample_count": feature["sample_count"],
                    "sample_record_ids": feature["sample_record_ids"],
                    "sample_group_ids": feature["sample_group_ids"],
                    "sample_namespace": feature["sample_namespace"],
                    "inclusion_notes": feature["inclusion_notes"],
                    "latitude_text": feature["latitude_text"],
                    "longitude_text": feature["longitude_text"],
                    "geocoding_method": feature["geocoding_method"],
                    "geocoder_or_gazetteer": feature["geocoder_or_gazetteer"],
                    "confidence_rationale": feature["confidence_rationale"],
                    "original_place_text": feature["original_place_text"],
                    "resolved_place_text": feature["resolved_place_text"],
                    "paper_title": feature["paper_title"],
                    "paper_doi": feature["paper_doi"],
                    "journal_title": feature["journal_title"],
                    "publication_year": feature["publication_year"],
                    "supplementary_sources": feature["supplementary_sources"],
                    "project_accessions": feature["project_accessions"],
                    "primary_project_accession": feature["primary_project_accession"],
                    "inclusion_statuses": feature["inclusion_statuses"],
                    "source_artifact_path": feature["source_artifact_path"],
                    "source_artifact_kind": feature["source_artifact_kind"],
                    "source_locator": feature["source_locator"],
                    "source_support_status": feature["source_support_status"],
                    "exact_source_text": feature["exact_source_text"],
                    "time_start_bp": feature["time_start_bp"],
                    "time_end_bp": feature["time_end_bp"],
                    "time_mean_bp": feature["time_mean_bp"],
                    "time_year_bp": feature["time_year_bp"],
                    "time_label": feature["time_label"],
                },
            }
        )
    path.write_text(
        json.dumps(
            {
                "schema_version": "animal-atlas-locality-collection.v1",
                "type": "FeatureCollection",
                "layer_key": layer_key,
                "layer_label": layer_label,
                "subtitle": description,
                "features": geojson_features,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _warning_rows_for(
    *,
    row: AnimalAtlasEvidenceRow,
    dataset_review: dict[str, object],
    review: dict[str, str],
) -> list[dict[str, str]]:
    warnings: list[str] = []
    if row.coordinate_confidence in {"approximate", "inferred"}:
        warnings.append(
            f"Coordinates are {row.coordinate_confidence}, not excavation-grade exact points."
        )
    if dataset_review.get("product_role") == "comparator":
        warnings.append("Comparator-only evidence: use for comparison, not domesticated-core claims.")
    if not row.nordic_inclusion:
        warnings.append("This locality is outside the Nordic lead set and remains atlas context, not Nordic-localized support.")
    elif row.political_entity not in NORDIC_COUNTRIES:
        warnings.append("Nordic relevance is regional or transregional rather than one named Nordic country.")
    if row.support_class in {"too_weak", "rejected"}:
        warnings.append("This locality stays visible with an explicit weak or rejected support class.")
    if review.get("reason"):
        warnings.append(review["reason"])
    return [{"label": "Warning", "value": warning} for warning in warnings]


def _layer_group_for(product_role: object) -> str:
    return (
        "animal-comparator-evidence"
        if str(product_role) == "comparator"
        else "animal-domesticated-evidence"
    )


def _animal_scope_for(dataset_review: dict[str, object]) -> str:
    return (
        "comparator"
        if dataset_review.get("product_role") == "comparator"
        else "domesticated_core"
    )


def _layer_description_for(
    *, species_common_name: str, dataset_review: dict[str, object]
) -> str:
    role = _animal_scope_for(dataset_review).replace("_", " ")
    return (
        f"Tracked {species_common_name} aDNA locality leads staged from sample-backed "
        f"or site-backed atlas evidence rows. Current role: {role}."
    )


def _layer_style_for(species_latin_name: str) -> dict[str, str]:
    return _SPECIES_STYLES.get(
        species_latin_name,
        {"fill": "#475569", "stroke": "#1e293b"},
    )


def _temporal_semantics_for(row: AnimalAtlasEvidenceRow) -> dict[str, object]:
    return row.chronology.as_temporal_semantics(
        source_family="animal_adna",
        provenance_path=row.source_artifact_path,
        provenance_locator=row.source_locator,
        provenance_excerpt=row.exact_source_text,
    )


def _alpha(color: str, opacity: float) -> str:
    color = color.lstrip("#")
    if len(color) != 6:
        return color
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {opacity:.2f})"


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _write_animal_atlas_evidence_csv(
    path: Path,
    rows: tuple[AnimalAtlasEvidenceRow, ...],
) -> None:
    fieldnames = (
        "feature_id",
        "evidence_row_id",
        "site_record_id",
        "species_latin_name",
        "species_common_name",
        "animal_scope",
        "support_class",
        "locality",
        "political_entity",
        "latitude",
        "longitude",
        "coordinate_basis",
        "coordinate_confidence",
        "sample_count",
        "sample_record_ids",
        "project_accessions",
        "paper_doi",
        "supplementary_sources",
        "time_label",
        "nordic_inclusion",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "feature_id": row.feature_id,
                    "evidence_row_id": row.evidence_row_id,
                    "site_record_id": row.site_record_id,
                    "species_latin_name": row.species_latin_name,
                    "species_common_name": row.species_common_name,
                    "animal_scope": row.animal_scope,
                    "support_class": row.support_class,
                    "locality": row.locality,
                    "political_entity": row.political_entity,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "coordinate_basis": row.coordinate_basis,
                    "coordinate_confidence": row.coordinate_confidence,
                    "sample_count": row.sample_count,
                    "sample_record_ids": ";".join(row.sample_record_ids),
                    "project_accessions": ";".join(row.project_accessions),
                    "paper_doi": row.paper_doi,
                    "supplementary_sources": ";".join(row.supplementary_sources),
                    "time_label": row.chronology.original_text,
                    "nordic_inclusion": str(row.nordic_inclusion).lower(),
                }
            )


def _write_animal_atlas_evidence_json(
    path: Path,
    rows: tuple[AnimalAtlasEvidenceRow, ...],
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "animal-atlas-evidence-rows.v1",
                "rows": [row.as_dict() for row in rows],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_animal_point_traceability_json(
    path: Path,
    rows: tuple[AnimalAtlasEvidenceRow, ...],
) -> None:
    payload = {
        "schema_version": "animal-atlas-point-traceability.v1",
        "rows": [
            {
                "feature_id": row.feature_id,
                "evidence_row_id": row.evidence_row_id,
                "site_record_id": row.site_record_id,
                "species_latin_name": row.species_latin_name,
                "primary_project_accession": row.primary_project_accession,
                "sample_record_ids": list(row.sample_record_ids),
                "sample_group_ids": list(row.sample_group_ids),
                "sample_count": row.sample_count,
                "coordinate_basis": row.coordinate_basis,
                "coordinate_confidence": row.coordinate_confidence,
                "source_artifact_path": row.source_artifact_path,
                "source_locator": row.source_locator,
                "paper_doi": row.paper_doi,
                "supplementary_sources": list(row.supplementary_sources),
            }
            for row in rows
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
