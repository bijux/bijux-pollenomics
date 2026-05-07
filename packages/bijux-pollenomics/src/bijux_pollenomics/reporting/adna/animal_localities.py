from __future__ import annotations

from collections.abc import Iterable
import csv
from dataclasses import dataclass
import json
from pathlib import Path

from ...adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
    build_species_support_matrix,
)
from ..shared.text import slugify

__all__ = [
    "AnimalAtlasBundle",
    "build_tracked_animal_atlas_bundle",
    "load_tracked_animal_localities",
]

_NORDIC_COUNTRIES = {"Sweden", "Norway", "Finland", "Denmark", "Iceland"}
_ANIMAL_CHRONOLOGY_BUCKETS = (
    ("0-1000 BP", 0, 1000),
    ("1001-3000 BP", 1001, 3000),
    ("3001-6000 BP", 3001, 6000),
    ("6001+ BP", 6001, None),
)
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
    localities: tuple[AdnaLocalitySummary, ...]
    extra_artifacts: tuple[tuple[str, str], ...]


def load_tracked_animal_localities(data_root: Path) -> tuple[AdnaLocalitySummary, ...]:
    """Load tracked non-human locality summaries from the governed data tree."""
    localities: list[AdnaLocalitySummary] = []
    adna_root = Path(data_root) / "adna"
    for species in build_species_support_matrix():
        if species.latin_name == "Homo sapiens":
            continue
        locality_path = adna_root / species.slug / "normalized" / "locality_summaries.json"
        if not locality_path.is_file():
            continue
        payload = json.loads(locality_path.read_text(encoding="utf-8"))
        for row in payload.get("localities", []):
            if not isinstance(row, dict):
                continue
            localities.append(_parse_locality_summary(row))
    localities.sort(
        key=lambda locality: (
            locality.species_latin_name,
            not locality.nordic_inclusion,
            -(locality.time_mean_bp or 0),
            locality.locality or "",
        )
    )
    return tuple(localities)


def build_tracked_animal_atlas_bundle(
    *,
    data_root: Path,
    output_dir: Path,
    atlas_slug: str,
) -> AnimalAtlasBundle:
    """Build staged atlas point layers from tracked non-human locality artifacts."""
    adna_root = Path(data_root) / "adna"
    all_localities = load_tracked_animal_localities(data_root)
    grouped_by_species: dict[str, list[AdnaLocalitySummary]] = {}
    for locality in all_localities:
        grouped_by_species.setdefault(locality.species_latin_name, []).append(locality)

    point_layers: list[dict[str, object]] = []
    all_features: list[dict[str, object]] = []
    domesticated_features: list[dict[str, object]] = []
    comparator_features: list[dict[str, object]] = []
    for species in build_species_support_matrix():
        if species.latin_name == "Homo sapiens":
            continue
        species_localities = tuple(grouped_by_species.get(species.latin_name, ()))
        if not species_localities:
            continue
        species_root = adna_root / species.slug
        dataset_review = _load_dataset_review(species_root)
        review_lookup = _load_review_lookup(species_root)
        citation_lookup = _load_citation_lookup(species_root)
        layer_key = f"animal-{slugify(species.slug)}"
        layer_group = _layer_group_for(dataset_review.get("product_role"))
        style = _layer_style_for(species.latin_name)
        features = [
            _build_point_feature(
                locality=locality,
                citation_lookup=citation_lookup,
                dataset_review=dataset_review,
                review_lookup=review_lookup,
            )
            for locality in species_localities
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
                "label": f"{species.common_name.title()} aDNA locality leads",
                "count": len(features),
                "description": _layer_description_for(
                    species_common_name=species.common_name,
                    dataset_review=dataset_review,
                ),
                "group": layer_group,
                "atlas_layer_key": layer_key,
                "species_latin_name": species.latin_name,
                "species_common_name": species.common_name,
                "animal_scope": _animal_scope_for(dataset_review),
                "contribution_role": "direct",
                "provenance_posture": "tracked_species_locality_summaries",
                "source_name": "Tracked animal aDNA localities",
                "coverage_label": (
                    "Mapped species-owned locality leads staged from tracked "
                    "`data/adna/<latin_name>/normalized/locality_summaries.json`."
                ),
                "geometry_label": "Point records",
                "default_enabled": True,
                "applies_country_filter": False,
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
        layer_label="Animal aDNA locality leads",
        description="All tracked animal aDNA locality leads included in the atlas bundle.",
    )
    _write_feature_collection(
        output_dir / f"{atlas_slug}_domesticated_animal_localities.geojson",
        features=domesticated_features,
        layer_key="domesticated-animal-localities",
        layer_label="Domesticated-core animal aDNA locality leads",
        description="Domesticated-core animal aDNA locality leads included in the atlas bundle.",
    )
    _write_feature_collection(
        output_dir / f"{atlas_slug}_comparator_animal_localities.geojson",
        features=comparator_features,
        layer_key="comparator-animal-localities",
        layer_label="Comparator animal aDNA locality leads",
        description="Comparator animal aDNA locality leads included in the atlas bundle.",
    )
    return AnimalAtlasBundle(
        point_layers=tuple(point_layers),
        localities=all_localities,
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
        ),
    )


def _parse_locality_summary(payload: dict[str, object]) -> AdnaLocalitySummary:
    identity = payload.get("identity", {})
    coordinates = payload.get("coordinates", {})
    chronology = payload.get("chronology", {})
    if not isinstance(identity, dict) or not isinstance(coordinates, dict) or not isinstance(
        chronology, dict
    ):
        raise ValueError("Tracked locality summary must include identity, coordinates, and chronology")
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace=str(identity.get("namespace", "")),
            stable_token=str(identity.get("stable_token", "")),
            locality_text=str(identity.get("locality_text", "")),
            political_entity=_optional_str(identity.get("political_entity")),
            source_anchor_tokens=tuple(
                str(item) for item in identity.get("source_anchor_tokens", [])
            ),
        ),
        species_latin_name=str(payload.get("species_latin_name", "")),
        species_common_name=str(payload.get("species_common_name", "")),
        source_family=str(payload.get("source_family", "")),
        source_releases=tuple(str(item) for item in payload.get("source_releases", [])),
        record_modalities=tuple(
            str(item) for item in payload.get("record_modalities", [])
        ),
        review_strengths=tuple(
            str(item) for item in payload.get("review_strengths", [])
        ),
        provenance_qualities=tuple(
            str(item) for item in payload.get("provenance_qualities", [])
        ),
        locality=_optional_str(payload.get("locality")),
        coordinates=AdnaCoordinate(
            latitude=_optional_float(coordinates.get("latitude")),
            longitude=_optional_float(coordinates.get("longitude")),
            latitude_text=str(coordinates.get("latitude_text", "")),
            longitude_text=str(coordinates.get("longitude_text", "")),
            confidence=str(coordinates.get("confidence", "unknown")),
        ),
        sample_count=int(payload.get("sample_count", 0) or 0),
        sample_ids=tuple(str(item) for item in payload.get("sample_ids", [])),
        datasets=tuple(str(item) for item in payload.get("datasets", [])),
        chronology=AdnaChronology(
            original_text=str(chronology.get("original_text", "")),
            time_start_bp=_optional_int(chronology.get("time_start_bp")),
            time_end_bp=_optional_int(chronology.get("time_end_bp")),
            time_mean_bp=_optional_int(chronology.get("time_mean_bp")),
            date_stddev_bp=str(chronology.get("date_stddev_bp", "")),
            dating_basis=str(chronology.get("dating_basis", "unknown")),
        ),
        sample_namespace=str(payload.get("sample_namespace", "")),
        project_accessions=tuple(
            str(item) for item in payload.get("project_accessions", [])
        ),
        original_location_text=str(payload.get("original_location_text", "")),
        nordic_inclusion=bool(payload.get("nordic_inclusion", False)),
        nordic_inclusion_reason=str(payload.get("nordic_inclusion_reason", "")),
        interpretation_note=str(payload.get("interpretation_note", "")),
    )


def _load_dataset_review(species_root: Path) -> dict[str, object]:
    payload = json.loads((species_root / "reports" / "support_summary.json").read_text(encoding="utf-8"))
    review = payload.get("dataset_review", {})
    if not isinstance(review, dict):
        raise ValueError(f"Dataset review missing for {species_root}")
    return review


def _load_review_lookup(species_root: Path) -> dict[str, dict[str, str]]:
    payload = json.loads((species_root / "review" / "species_review.json").read_text(encoding="utf-8"))
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
                    "nordic_relevance_reason": str(
                        row.get("nordic_relevance_reason", "")
                    ),
                }
    return lookup


def _load_citation_lookup(species_root: Path) -> dict[str, dict[str, str]]:
    path = species_root / "manifests" / "citation_manifest.csv"
    lookup: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            accession = str(row.get("project_accession", "")).strip()
            if not accession:
                continue
            lookup[accession] = {
                "paper_title": str(row.get("paper_title", "")).strip(),
                "paper_doi": str(row.get("paper_doi", "")).strip(),
                "publication_year": str(row.get("publication_year", "")).strip(),
                "journal_title": str(row.get("journal_title", "")).strip(),
            }
    return lookup


def _build_point_feature(
    *,
    locality: AdnaLocalitySummary,
    citation_lookup: dict[str, dict[str, str]],
    dataset_review: dict[str, object],
    review_lookup: dict[str, dict[str, str]],
) -> dict[str, object]:
    primary_accession = locality.project_accessions[0] if locality.project_accessions else ""
    citation = citation_lookup.get(primary_accession, {})
    review = review_lookup.get(primary_accession, {})
    warning_rows = _warning_rows_for(
        locality=locality,
        dataset_review=dataset_review,
        review=review,
    )
    scope = _animal_scope_for(dataset_review)
    paper_doi = citation.get("paper_doi") or review.get("paper_doi", "")
    source_url = f"https://doi.org/{paper_doi}" if paper_doi else ""
    chronology_bucket = _chronology_bucket_for(locality)
    popup_rows = [
        {"label": "Species", "value": locality.species_latin_name},
        {"label": "Support class", "value": review.get("support_class", "mapped_locality")},
        {"label": "Animal scope", "value": scope.replace("_", " ")},
        {
            "label": "Project accession",
            "value": ", ".join(locality.project_accessions) or "No project accession",
        },
        {"label": "Paper title", "value": citation.get("paper_title", "") or review.get("paper_title", "")},
        {"label": "Publication year", "value": citation.get("publication_year", "")},
        {"label": "Chronology", "value": locality.time_label},
        {"label": "Chronology bucket", "value": chronology_bucket},
        {"label": "Support note", "value": review.get("reason", "")},
        {"label": "Coordinate confidence", "value": locality.coordinate_confidence},
        {
            "label": "Nordic relevance",
            "value": "nordic_lead" if locality.nordic_inclusion else "non_nordic_or_comparator",
        },
        {"label": "Nordic note", "value": locality.nordic_inclusion_reason},
        {"label": "Interpretation", "value": locality.interpretation_note},
    ]
    popup_rows.extend(warning_rows)
    return {
        "latitude": locality.latitude,
        "longitude": locality.longitude,
        "country": locality.identity.political_entity or "",
        "title": locality.locality or locality.identity.locality_text,
        "subtitle": f"{locality.species_common_name.title()} locality lead",
        "species_latin_name": locality.species_latin_name,
        "species_common_name": locality.species_common_name,
        "evidence_role": "direct",
        "animal_scope": scope,
        "support_class": review.get("support_class", "mapped_locality"),
        "chronology_bucket": chronology_bucket,
        "nordic_inclusion": locality.nordic_inclusion,
        "nordic_inclusion_reason": locality.nordic_inclusion_reason,
        "coordinate_confidence": locality.coordinate_confidence,
        "paper_title": citation.get("paper_title", "") or review.get("paper_title", ""),
        "publication_year": citation.get("publication_year", ""),
        "project_accessions": list(locality.project_accessions),
        "popup_rows": [row for row in popup_rows if row["value"]],
        "source_url": source_url,
        "media_links": [],
        "time_start_bp": locality.time_start_bp,
        "time_end_bp": locality.time_end_bp,
        "time_mean_bp": locality.time_mean_bp,
        "time_year_bp": locality.time_mean_bp,
        "time_label": locality.time_label,
    }


def _write_feature_collection(
    path: Path,
    *,
    features: Iterable[dict[str, object]],
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
                    "chronology_bucket": feature["chronology_bucket"],
                    "nordic_inclusion": feature["nordic_inclusion"],
                    "nordic_inclusion_reason": feature["nordic_inclusion_reason"],
                    "coordinate_confidence": feature["coordinate_confidence"],
                    "paper_title": feature["paper_title"],
                    "publication_year": feature["publication_year"],
                    "project_accessions": feature["project_accessions"],
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
    locality: AdnaLocalitySummary,
    dataset_review: dict[str, object],
    review: dict[str, str],
) -> list[dict[str, str]]:
    warnings: list[str] = []
    if locality.coordinate_confidence in {"approximate", "inferred"}:
        warnings.append(
            f"Coordinates are {locality.coordinate_confidence}, not excavation-grade exact points."
        )
    if dataset_review.get("product_role") == "comparator":
        warnings.append("Comparator-only evidence: use for comparison, not domesticated-core claims.")
    if not locality.nordic_inclusion:
        warnings.append("This locality is outside the Nordic lead set and remains atlas context, not Nordic-localized support.")
    elif locality.identity.political_entity not in _NORDIC_COUNTRIES:
        warnings.append("Nordic relevance is regional or transregional rather than one named Nordic country.")
    support_class = review.get("support_class", "")
    if support_class in {"too_weak", "rejected"}:
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
        f"Tracked {species_common_name} aDNA locality leads staged from species-owned "
        f"normalized artifacts. Current role: {role}."
    )


def _layer_style_for(species_latin_name: str) -> dict[str, str]:
    return _SPECIES_STYLES.get(
        species_latin_name,
        {"fill": "#475569", "stroke": "#1e293b"},
    )


def _chronology_bucket_for(locality: AdnaLocalitySummary) -> str:
    mean_bp = locality.time_mean_bp
    if mean_bp is None:
        return "undated"
    for label, start, end in _ANIMAL_CHRONOLOGY_BUCKETS:
        if end is None and mean_bp >= start:
            return label
        if end is not None and start <= mean_bp <= end:
            return label
    return "undated"


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


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)
