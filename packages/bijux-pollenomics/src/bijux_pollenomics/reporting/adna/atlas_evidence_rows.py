from __future__ import annotations

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
from ...adna.paths import adna_species_dir
from ..shared.text import slugify

__all__ = [
    "AnimalAtlasCoordinateReview",
    "AnimalAtlasEvidenceRow",
    "build_tracked_animal_atlas_coordinate_review",
    "build_tracked_animal_atlas_evidence_rows",
    "load_tracked_animal_mappable_localities",
]

_DIRECT_COORDINATE_BASES = {
    "direct_published_coordinates",
    "supplementary_table_coordinates",
    "archive_coordinates",
}


@dataclass(frozen=True)
class AnimalAtlasEvidenceRow:
    """One traceable animal atlas evidence row eligible for point publication."""

    feature_id: str
    evidence_row_id: str
    site_record_id: str
    species_latin_name: str
    species_common_name: str
    animal_scope: str
    support_class: str
    support_note: str
    locality: str
    political_entity: str
    latitude: float
    longitude: float
    latitude_text: str
    longitude_text: str
    coordinate_basis: str
    coordinate_confidence: str
    geocoding_method: str
    geocoder_or_gazetteer: str
    confidence_rationale: str
    original_place_text: str
    resolved_place_text: str
    coordinate_source_artifact_path: str
    coordinate_source_locator: str
    coordinate_supplementary_source: str
    coordinate_support_gap_note: str
    chronology: AdnaChronology
    project_accessions: tuple[str, ...]
    primary_project_accession: str
    sample_record_ids: tuple[str, ...]
    sample_group_ids: tuple[str, ...]
    sample_count: int
    sample_namespace: str
    inclusion_statuses: tuple[str, ...]
    inclusion_notes: tuple[str, ...]
    paper_title: str
    paper_doi: str
    publication_year: str
    journal_title: str
    paper_url: str
    supplementary_sources: tuple[str, ...]
    source_artifact_path: str
    source_artifact_kind: str
    source_locator: str
    source_support_status: str
    exact_source_text: str
    nordic_inclusion: bool
    nordic_inclusion_reason: str
    interpretation_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "feature_id": self.feature_id,
            "evidence_row_id": self.evidence_row_id,
            "site_record_id": self.site_record_id,
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "animal_scope": self.animal_scope,
            "support_class": self.support_class,
            "support_note": self.support_note,
            "locality": self.locality,
            "political_entity": self.political_entity,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "latitude_text": self.latitude_text,
            "longitude_text": self.longitude_text,
            "coordinate_basis": self.coordinate_basis,
            "coordinate_confidence": self.coordinate_confidence,
            "geocoding_method": self.geocoding_method,
            "geocoder_or_gazetteer": self.geocoder_or_gazetteer,
            "confidence_rationale": self.confidence_rationale,
            "original_place_text": self.original_place_text,
            "resolved_place_text": self.resolved_place_text,
            "coordinate_source_artifact_path": self.coordinate_source_artifact_path,
            "coordinate_source_locator": self.coordinate_source_locator,
            "coordinate_supplementary_source": self.coordinate_supplementary_source,
            "coordinate_support_gap_note": self.coordinate_support_gap_note,
            "chronology": self.chronology.as_dict(),
            "project_accessions": list(self.project_accessions),
            "primary_project_accession": self.primary_project_accession,
            "sample_record_ids": list(self.sample_record_ids),
            "sample_group_ids": list(self.sample_group_ids),
            "sample_count": self.sample_count,
            "sample_namespace": self.sample_namespace,
            "inclusion_statuses": list(self.inclusion_statuses),
            "inclusion_notes": list(self.inclusion_notes),
            "paper_title": self.paper_title,
            "paper_doi": self.paper_doi,
            "publication_year": self.publication_year,
            "journal_title": self.journal_title,
            "paper_url": self.paper_url,
            "supplementary_sources": list(self.supplementary_sources),
            "source_artifact_path": self.source_artifact_path,
            "source_artifact_kind": self.source_artifact_kind,
            "source_locator": self.source_locator,
            "source_support_status": self.source_support_status,
            "exact_source_text": self.exact_source_text,
            "nordic_inclusion": self.nordic_inclusion,
            "nordic_inclusion_reason": self.nordic_inclusion_reason,
            "interpretation_note": self.interpretation_note,
        }


@dataclass(frozen=True)
class AnimalAtlasCoordinateReview:
    """Visible coordinate-basis counts for one animal atlas bundle."""

    direct_coordinate_feature_count: int
    named_site_geocoded_feature_count: int
    weaker_geography_feature_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "direct_coordinate_feature_count": self.direct_coordinate_feature_count,
            "named_site_geocoded_feature_count": self.named_site_geocoded_feature_count,
            "weaker_geography_feature_count": self.weaker_geography_feature_count,
        }


def build_tracked_animal_atlas_evidence_rows(
    data_root: Path,
) -> tuple[AnimalAtlasEvidenceRow, ...]:
    """Build the exact set of animal rows eligible for atlas point publication."""
    rows: list[AnimalAtlasEvidenceRow] = []
    species_dir = adna_species_dir(Path(data_root))
    for species in build_species_support_matrix():
        if species.latin_name == "Homo sapiens":
            continue
        species_root = species_dir / species.slug
        if not species_root.is_dir():
            continue
        locality_rows = _load_locality_rows(species_root)
        sample_rows = _load_sample_rows(species_root)
        provenance_lookup = _load_coordinate_provenance_lookup(species_root)
        site_evidence_lookup = _load_site_evidence_lookup(species_root)
        citation_lookup = _load_citation_lookup(species_root)
        review_lookup = _load_review_lookup(species_root)
        animal_scope = _animal_scope_for(species_root)
        for locality in locality_rows:
            project_accessions = tuple(
                str(item) for item in locality.get("project_accessions", []) if str(item).strip()
            )
            if not project_accessions:
                continue
            primary_project_accession = project_accessions[0]
            site_identity = locality.get("identity", {})
            if not isinstance(site_identity, dict):
                continue
            locality_label = str(locality.get("locality") or site_identity.get("locality_text", ""))
            provenance = _lookup_project_locality_row(
                provenance_lookup,
                project_accession=primary_project_accession,
                locality_text=locality_label,
            )
            if provenance is None:
                continue
            if str(provenance.get("mapping_posture", "")) != "mappable_point":
                continue
            coordinates = locality.get("coordinates", {})
            if not isinstance(coordinates, dict):
                continue
            latitude = _optional_float(coordinates.get("latitude"))
            longitude = _optional_float(coordinates.get("longitude"))
            if latitude is None or longitude is None:
                continue
            site_record_id = str(site_identity.get("stable_token", "")).strip()
            if not site_record_id:
                continue
            matched_sample_rows = tuple(
                row
                for row in sample_rows
                if str(row.get("project_accession", "")).strip() in project_accessions
                and _sample_locality_token(row) == site_record_id
            )
            _assert_no_project_level_flattening(
                primary_project_accession=primary_project_accession,
                site_record_id=site_record_id,
                sample_rows=matched_sample_rows,
            )
            site_evidence = _lookup_project_locality_row(
                site_evidence_lookup,
                project_accession=primary_project_accession,
                locality_text=locality_label,
            ) or {}
            citation = citation_lookup.get(primary_project_accession, {})
            review = review_lookup.get(primary_project_accession, {})
            feature_token = slugify(site_record_id)
            evidence_token = slugify(
                ":".join((species.slug, primary_project_accession, site_record_id))
            )
            rows.append(
                AnimalAtlasEvidenceRow(
                    feature_id=f"animal-atlas-feature:{feature_token}",
                    evidence_row_id=f"animal-atlas-row:{evidence_token}",
                    site_record_id=site_record_id,
                    species_latin_name=str(locality.get("species_latin_name", "")),
                    species_common_name=str(locality.get("species_common_name", "")),
                    animal_scope=animal_scope,
                    support_class=str(review.get("support_class", "mapped_locality")),
                    support_note=str(review.get("reason", "")),
                    locality=str(locality.get("locality") or site_identity.get("locality_text", "")),
                    political_entity=str(
                        locality.get("political_entity")
                        or site_identity.get("political_entity", "")
                    ),
                    latitude=latitude,
                    longitude=longitude,
                    latitude_text=str(coordinates.get("latitude_text", "")),
                    longitude_text=str(coordinates.get("longitude_text", "")),
                    coordinate_basis=str(provenance.get("coordinate_basis", "")),
                    coordinate_confidence=str(provenance.get("coordinate_confidence", "")),
                    geocoding_method=str(provenance.get("geocoding_method", "")),
                    geocoder_or_gazetteer=str(provenance.get("geocoder_or_gazetteer", "")),
                    confidence_rationale=str(provenance.get("confidence_rationale", "")),
                    original_place_text=str(provenance.get("original_place_text", "")),
                    resolved_place_text=str(provenance.get("resolved_place_text", "")),
                    coordinate_source_artifact_path=str(
                        provenance.get("source_artifact_path", "")
                    ),
                    coordinate_source_locator=str(provenance.get("source_locator", "")),
                    coordinate_supplementary_source=str(
                        provenance.get("supplementary_source", "")
                    ),
                    coordinate_support_gap_note=str(
                        provenance.get("support_gap_note", "")
                    ),
                    chronology=_atlas_public_chronology(
                        _parse_chronology(locality.get("chronology", {}))
                    ),
                    project_accessions=project_accessions,
                    primary_project_accession=primary_project_accession,
                    sample_record_ids=_sample_record_ids_for(
                        matched_sample_rows,
                        fallback=tuple(
                            str(item)
                            for item in locality.get("sample_ids", [])
                            if str(item).strip()
                        ),
                    ),
                    sample_group_ids=_sample_group_ids_for(matched_sample_rows),
                    sample_count=int(locality.get("sample_count", 0) or 0),
                    sample_namespace=str(locality.get("sample_namespace", "")),
                    inclusion_statuses=_inclusion_statuses_for(matched_sample_rows),
                    inclusion_notes=_inclusion_notes_for(matched_sample_rows),
                    paper_title=str(
                        citation.get("paper_title") or review.get("paper_title", "")
                    ),
                    paper_doi=str(citation.get("paper_doi") or review.get("paper_doi", "")),
                    publication_year=str(citation.get("publication_year", "")),
                    journal_title=str(citation.get("journal_title", "")),
                    paper_url=_paper_url_for(
                        str(citation.get("paper_doi") or review.get("paper_doi", ""))
                    ),
                    supplementary_sources=_supplementary_sources_for(
                        matched_sample_rows,
                        provenance,
                        site_evidence,
                    ),
                    source_artifact_path=str(site_evidence.get("source_artifact_path", "")),
                    source_artifact_kind=str(site_evidence.get("source_artifact_kind", "")),
                    source_locator=str(site_evidence.get("source_locator", "")),
                    source_support_status=str(site_evidence.get("source_support_status", "")),
                    exact_source_text=str(site_evidence.get("exact_source_text", "")),
                    nordic_inclusion=bool(locality.get("nordic_inclusion", False)),
                    nordic_inclusion_reason=str(locality.get("nordic_inclusion_reason", "")),
                    interpretation_note=str(locality.get("interpretation_note", "")),
                )
            )
    rows.sort(
        key=lambda row: (
            row.species_latin_name,
            not row.nordic_inclusion,
            row.primary_project_accession,
            row.site_record_id,
        )
    )
    return tuple(rows)


def load_tracked_animal_mappable_localities(
    data_root: Path,
) -> tuple[AdnaLocalitySummary, ...]:
    """Load only the locality rows that are actually eligible for point publication."""
    visible_site_ids = {
        row.site_record_id for row in build_tracked_animal_atlas_evidence_rows(data_root)
    }
    localities: list[AdnaLocalitySummary] = []
    species_dir = adna_species_dir(Path(data_root))
    for species in build_species_support_matrix():
        if species.latin_name == "Homo sapiens":
            continue
        locality_path = species_dir / species.slug / "normalized" / "locality_summaries.json"
        if not locality_path.is_file():
            continue
        payload = json.loads(locality_path.read_text(encoding="utf-8"))
        for row in payload.get("localities", []):
            if not isinstance(row, dict):
                continue
            identity = row.get("identity", {})
            if not isinstance(identity, dict):
                continue
            if str(identity.get("stable_token", "")).strip() not in visible_site_ids:
                continue
            localities.append(_parse_locality_summary(row))
    localities.sort(
        key=lambda locality: (
            locality.species_latin_name,
            not locality.nordic_inclusion,
            locality.locality or "",
        )
    )
    return tuple(localities)


def build_tracked_animal_atlas_coordinate_review(
    evidence_rows: tuple[AnimalAtlasEvidenceRow, ...],
) -> AnimalAtlasCoordinateReview:
    """Summarize visible animal-feature counts by coordinate basis strength."""
    direct_coordinate_feature_count = sum(
        1 for row in evidence_rows if row.coordinate_basis in _DIRECT_COORDINATE_BASES
    )
    named_site_geocoded_feature_count = sum(
        1 for row in evidence_rows if row.coordinate_basis == "named_site_geocoding"
    )
    weaker_geography_feature_count = sum(
        1
        for row in evidence_rows
        if row.coordinate_basis not in _DIRECT_COORDINATE_BASES
        and row.coordinate_basis != "named_site_geocoding"
    )
    return AnimalAtlasCoordinateReview(
        direct_coordinate_feature_count=direct_coordinate_feature_count,
        named_site_geocoded_feature_count=named_site_geocoded_feature_count,
        weaker_geography_feature_count=weaker_geography_feature_count,
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
        chronology=_atlas_public_chronology(_parse_chronology(chronology)),
        sample_namespace=str(payload.get("sample_namespace", "")),
        project_accessions=tuple(
            str(item) for item in payload.get("project_accessions", [])
        ),
        original_location_text=str(payload.get("original_location_text", "")),
        nordic_inclusion=bool(payload.get("nordic_inclusion", False)),
        nordic_inclusion_reason=str(payload.get("nordic_inclusion_reason", "")),
        interpretation_note=str(payload.get("interpretation_note", "")),
    )


def _parse_chronology(payload: object) -> AdnaChronology:
    if not isinstance(payload, dict):
        raise ValueError("Chronology payload must be a dict")
    return AdnaChronology(
        original_text=str(payload.get("original_text", "")),
        time_start_bp=_optional_int(payload.get("time_start_bp")),
        time_end_bp=_optional_int(payload.get("time_end_bp")),
        time_mean_bp=_optional_int(payload.get("time_mean_bp")),
        date_stddev_bp=str(payload.get("date_stddev_bp", "")),
        dating_basis=str(payload.get("dating_basis", "unknown")),
        evidence_class=str(payload.get("evidence_class", "unresolved")),
        precision_posture=str(payload.get("precision_posture", "unresolved")),
    )


def _atlas_public_chronology(chronology: AdnaChronology) -> AdnaChronology:
    if chronology.precision_posture in {"sample_precise_point", "sample_precise_interval"}:
        return chronology
    return AdnaChronology(
        original_text=chronology.original_text,
        time_start_bp=None,
        time_end_bp=None,
        time_mean_bp=None,
        date_stddev_bp=chronology.date_stddev_bp,
        dating_basis=chronology.dating_basis,
        evidence_class=chronology.evidence_class,
        precision_posture=chronology.precision_posture,
    )


def _load_locality_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "locality_summaries.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("localities", [])
    return [row for row in rows if isinstance(row, dict)]


def _load_sample_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "sample_records.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("samples", [])
    return [row for row in rows if isinstance(row, dict)]


def _load_coordinate_provenance_lookup(
    species_root: Path,
) -> dict[tuple[str, str], dict[str, object]]:
    path = species_root / "normalized" / "coordinate_provenance.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("coordinate_provenance", [])
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        project_accession = str(row.get("project_accession", "")).strip()
        if not project_accession:
            continue
        site_label = str(row.get("site_label", "")).strip()
        lookup[(project_accession, site_label)] = row
        lookup.setdefault((project_accession, ""), row)
    return lookup


def _load_site_evidence_lookup(
    species_root: Path,
) -> dict[tuple[str, str], dict[str, object]]:
    path = species_root / "normalized" / "site_evidence.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("site_evidence", [])
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        project_accession = str(row.get("project_accession", "")).strip()
        if not project_accession:
            continue
        site_label = str(row.get("site_label", "")).strip()
        lookup[(project_accession, site_label)] = row
        lookup.setdefault((project_accession, ""), row)
    return lookup


def _lookup_project_locality_row(
    lookup: dict[tuple[str, str], dict[str, object]],
    *,
    project_accession: str,
    locality_text: str,
) -> dict[str, object] | None:
    return lookup.get((project_accession, locality_text)) or lookup.get((project_accession, ""))


def _sample_locality_token(row: dict[str, object]) -> str:
    locality_identity = row.get("locality_identity", {})
    if not isinstance(locality_identity, dict):
        return ""
    return str(locality_identity.get("stable_token", "")).strip()


def _load_citation_lookup(species_root: Path) -> dict[str, dict[str, str]]:
    path = species_root / "manifests" / "citation_manifest.csv"
    if not path.is_file():
        return {}
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


def _load_review_lookup(species_root: Path) -> dict[str, dict[str, str]]:
    path = species_root / "review" / "species_review.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
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
                    "paper_title": str(row.get("paper_title", "")),
                    "paper_doi": str(row.get("paper_doi", "")),
                }
    return lookup


def _animal_scope_for(species_root: Path) -> str:
    payload = json.loads(
        (species_root / "reports" / "support_summary.json").read_text(encoding="utf-8")
    )
    dataset_review = payload.get("dataset_review", {})
    return (
        "comparator"
        if isinstance(dataset_review, dict)
        and str(dataset_review.get("product_role", "")).strip() == "comparator"
        else "domesticated_core"
    )


def _sample_record_ids_for(
    sample_rows: tuple[dict[str, object], ...],
    *,
    fallback: tuple[str, ...],
) -> tuple[str, ...]:
    identifiers = sorted(
        {
            str(row.get("identity", {}).get("stable_token", "")).strip()
            for row in sample_rows
            if isinstance(row.get("identity"), dict)
            and str(row.get("identity", {}).get("stable_token", "")).strip()
        }
    )
    return tuple(identifiers) if identifiers else fallback


def _sample_group_ids_for(sample_rows: tuple[dict[str, object], ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(row.get("group_id", "")).strip()
                for row in sample_rows
                if str(row.get("group_id", "")).strip()
            }
        )
    )


def _inclusion_statuses_for(
    sample_rows: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    statuses = sorted(
        {
            str(row.get("inclusion_status", "")).strip()
            for row in sample_rows
            if str(row.get("inclusion_status", "")).strip()
        }
    )
    return tuple(statuses)


def _inclusion_notes_for(sample_rows: tuple[dict[str, object], ...]) -> tuple[str, ...]:
    notes = sorted(
        {
            str(row.get("inclusion_note", "")).strip()
            for row in sample_rows
            if str(row.get("inclusion_note", "")).strip()
        }
    )
    return tuple(notes)


def _supplementary_sources_for(
    sample_rows: tuple[dict[str, object], ...],
    provenance: dict[str, object],
    site_evidence: dict[str, object],
) -> tuple[str, ...]:
    sources = {
        str(row.get("supplementary_source", "")).strip()
        for row in sample_rows
        if str(row.get("supplementary_source", "")).strip()
    }
    for row in (provenance, site_evidence):
        value = str(row.get("supplementary_source", "")).strip()
        if value:
            sources.add(value)
    return tuple(sorted(sources))


def _assert_no_project_level_flattening(
    *,
    primary_project_accession: str,
    site_record_id: str,
    sample_rows: tuple[dict[str, object], ...],
) -> None:
    retained_rows = tuple(
        row
        for row in sample_rows
        if str(row.get("inclusion_status", "")).strip() != "sample_context_blocked"
    )
    locality_tokens = {
        str(row.get("locality_identity", {}).get("stable_token", "")).strip()
        for row in retained_rows
        if isinstance(row.get("locality_identity"), dict)
        and str(row.get("locality_identity", {}).get("stable_token", "")).strip()
    }
    locality_texts = {
        _normalize_locality_text(
            str(row.get("locality_identity", {}).get("locality_text", "")).strip()
        )
        for row in retained_rows
        if isinstance(row.get("locality_identity"), dict)
        and str(row.get("locality_identity", {}).get("locality_text", "")).strip()
    }
    if len(locality_tokens) <= 1 and len(locality_texts) <= 1:
        return
    raise ValueError(
        "Project-level flattening detected for "
        f"{primary_project_accession}: one locality summary would collapse "
        f"multiple sample-site identities {sorted(locality_tokens)} and "
        f"locality labels {sorted(locality_texts)} into {site_record_id}."
    )


def _paper_url_for(doi: str) -> str:
    return f"https://doi.org/{doi}" if doi else ""


def _normalize_locality_text(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


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
