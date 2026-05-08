from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re

from ..core.bp_time import (
    build_bp_interval_label,
    midpoint_bp_year,
    normalize_bp_interval,
    parse_bp_window_label,
)
from .coordinate_provenance import build_species_coordinate_provenance_rows
from .curation import build_species_curation_manifest
from .ena import build_species_archive_projects, classify_archive_project_evidence
from .manifests import AdnaSpeciesManifest, build_species_manifest
from .models import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaCoordinateProvenanceRecord,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
    AdnaSampleIdentity,
    AdnaSampleRecord,
    AdnaSiteEvidenceRecord,
)
from .paths import ADNA_SPECIES_DIR
from .project_sample_chronology import build_project_sample_chronology_rows
from .project_context import resolve_project_context
from .project_localities import build_species_project_locality_leads
from .sample_registry import build_species_curated_sample_rows
from .site_evidence import build_species_site_evidence_rows
from .species import AdnaSpeciesDefinition, resolve_species_definition

__all__ = [
    "ADNA_DOMESTICATION_STATUSES",
    "AdnaCoordinateResolution",
    "AdnaNormalizationLineage",
    "AdnaNormalizationRefusal",
    "AdnaProjectSummary",
    "AdnaSpeciesNormalizationBundle",
    "AdnaStudySummary",
    "build_species_normalization_bundle",
    "build_species_project_locality_records",
    "normalize_chronology_text",
    "normalize_coordinate_resolution",
    "normalize_explicit_bp_window",
    "normalize_breed_label",
    "normalize_species_anchor",
]

ADNA_DOMESTICATION_STATUSES = (
    "domesticated_core",
    "comparator_only",
    "thin_evidence",
    "unsupported",
)
ADNA_PROJECT_SUPPORT_CLASSES = (
    "domesticated_core_curated",
    "archive_pending_paper_linkage",
    "wild_or_progenitor_context",
    "comparator_only",
    "rejected_or_out_of_scope",
)
_BP_MEAN_STDDEV_RE = re.compile(
    r"(?P<mean>\d{1,5})\s*(?:±|\+/-)\s*(?P<stddev>\d{1,4})\s*BP",
    re.IGNORECASE,
)
_BP_SINGLE_RE = re.compile(r"(?P<mean>\d{1,5})\s*BP", re.IGNORECASE)
_BCE_RANGE_RE = re.compile(
    r"(?P<start>\d{1,5})\s*-\s*(?P<end>\d{1,5})\s*(?:cal\s*)?BCE",
    re.IGNORECASE,
)
_BCE_SINGLE_RE = re.compile(r"(?P<year>\d{1,5})\s*(?:cal\s*)?BCE", re.IGNORECASE)
_CE_RANGE_RE = re.compile(
    r"(?P<start>\d{1,4})\s*-\s*(?P<end>\d{1,4})\s*CE",
    re.IGNORECASE,
)
_CE_SINGLE_RE = re.compile(r"(?P<year>\d{1,4})\s*CE", re.IGNORECASE)


@dataclass(frozen=True)
class AdnaCoordinateResolution:
    """Coordinate normalization result that can keep locations honestly withheld."""

    coordinate: AdnaCoordinate | None
    confidence: str
    source_basis: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "coordinate": None if self.coordinate is None else self.coordinate.__dict__,
            "confidence": self.confidence,
            "source_basis": self.source_basis,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class AdnaNormalizationLineage:
    """Trace one normalized output back to one governed raw-source expectation."""

    schema_version: str
    output_record_kind: str
    output_record_token: str
    source_artifact_path: str
    source_accessions: tuple[str, ...]
    lineage_tokens: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "output_record_kind": self.output_record_kind,
            "output_record_token": self.output_record_token,
            "source_artifact_path": self.source_artifact_path,
            "source_accessions": list(self.source_accessions),
            "lineage_tokens": list(self.lineage_tokens),
        }


@dataclass(frozen=True)
class AdnaNormalizationRefusal:
    """Explicit refusal row for non-human normalization that would overclaim support."""

    schema_version: str
    species_latin_name: str
    source_token: str
    record_kind: str
    reason: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_latin_name": self.species_latin_name,
            "source_token": self.source_token,
            "record_kind": self.record_kind,
            "reason": self.reason,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AdnaProjectSummary:
    """Normalized project-level summary for non-human ancient-DNA support."""

    schema_version: str
    summary_token: str
    species_latin_name: str
    species_common_name: str
    project_accession: str
    study_token: str
    source_family: str
    source_release: str
    result_kind: str
    archive_status: str
    evidence_strength: str
    review_strength: str
    support_class: str
    record_modality: str
    domestication_status: str
    domestication_scope: str
    comparator_status: bool
    normalized_breed_label: str | None
    sequencing_target: str | None
    material_basis: str | None
    chronology_basis: str | None
    dating_basis: str | None
    geographic_basis: str | None
    coordinate_policy: str
    chronology_policy: str
    paper_title: str | None
    paper_doi: str | None
    paper_url: str | None
    nordic_relevance: str
    nordic_relevance_reason: str
    interpretation_caveat: str
    notes: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "summary_token": self.summary_token,
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "project_accession": self.project_accession,
            "study_token": self.study_token,
            "source_family": self.source_family,
            "source_release": self.source_release,
            "result_kind": self.result_kind,
            "archive_status": self.archive_status,
            "evidence_strength": self.evidence_strength,
            "review_strength": self.review_strength,
            "support_class": self.support_class,
            "record_modality": self.record_modality,
            "domestication_status": self.domestication_status,
            "domestication_scope": self.domestication_scope,
            "comparator_status": self.comparator_status,
            "normalized_breed_label": self.normalized_breed_label,
            "sequencing_target": self.sequencing_target,
            "material_basis": self.material_basis,
            "chronology_basis": self.chronology_basis,
            "dating_basis": self.dating_basis,
            "geographic_basis": self.geographic_basis,
            "coordinate_policy": self.coordinate_policy,
            "chronology_policy": self.chronology_policy,
            "paper_title": self.paper_title,
            "paper_doi": self.paper_doi,
            "paper_url": self.paper_url,
            "nordic_relevance": self.nordic_relevance,
            "nordic_relevance_reason": self.nordic_relevance_reason,
            "interpretation_caveat": self.interpretation_caveat,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class AdnaStudySummary:
    """Normalized study-level grouping across one or more project summaries."""

    schema_version: str
    summary_token: str
    species_latin_name: str
    species_common_name: str
    project_accessions: tuple[str, ...]
    source_families: tuple[str, ...]
    archive_statuses: tuple[str, ...]
    evidence_strengths: tuple[str, ...]
    domestication_status: str
    paper_title: str | None
    paper_doi: str | None
    sequencing_targets: tuple[str, ...]
    material_bases: tuple[str, ...]
    dating_bases: tuple[str, ...]
    geographic_bases: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "summary_token": self.summary_token,
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "project_accessions": list(self.project_accessions),
            "source_families": list(self.source_families),
            "archive_statuses": list(self.archive_statuses),
            "evidence_strengths": list(self.evidence_strengths),
            "domestication_status": self.domestication_status,
            "paper_title": self.paper_title,
            "paper_doi": self.paper_doi,
            "sequencing_targets": list(self.sequencing_targets),
            "material_bases": list(self.material_bases),
            "dating_bases": list(self.dating_bases),
            "geographic_bases": list(self.geographic_bases),
        }


@dataclass(frozen=True)
class AdnaSpeciesNormalizationBundle:
    """Normalized non-human aDNA bundle for project and study review."""

    schema_version: str
    species_manifest: AdnaSpeciesManifest
    sample_records: tuple[AdnaSampleRecord, ...]
    coordinate_provenance_records: tuple[AdnaCoordinateProvenanceRecord, ...]
    site_evidence_records: tuple[AdnaSiteEvidenceRecord, ...]
    locality_records: tuple[AdnaLocalitySummary, ...]
    project_summaries: tuple[AdnaProjectSummary, ...]
    study_summaries: tuple[AdnaStudySummary, ...]
    lineage_records: tuple[AdnaNormalizationLineage, ...]
    refusals: tuple[AdnaNormalizationRefusal, ...]
    normalization_scope: str

    @property
    def species(self) -> AdnaSpeciesDefinition:
        return self.species_manifest.species

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_manifest": self.species_manifest.as_dict(),
            "sample_records": [record.as_dict() for record in self.sample_records],
            "coordinate_provenance_records": [
                record.as_dict() for record in self.coordinate_provenance_records
            ],
            "site_evidence_records": [
                record.as_dict() for record in self.site_evidence_records
            ],
            "locality_records": [record.as_dict() for record in self.locality_records],
            "project_summaries": [summary.as_dict() for summary in self.project_summaries],
            "study_summaries": [summary.as_dict() for summary in self.study_summaries],
            "lineage_records": [row.as_dict() for row in self.lineage_records],
            "refusals": [row.as_dict() for row in self.refusals],
            "normalization_scope": self.normalization_scope,
        }


def build_species_normalization_bundle(species_name: str) -> AdnaSpeciesNormalizationBundle:
    """Build the deterministic non-human normalization bundle for one species."""
    species_manifest = build_species_manifest(species_name)
    if species_manifest.species.latin_name == "Homo sapiens":
        raise ValueError(
            "Homo sapiens normalization is owned by the governed AADR metadata runtime"
        )
    curation_manifest = build_species_curation_manifest(species_name)
    project_summaries, project_refusals = _normalize_project_summaries(
        species_name,
        curation_manifest.curation_class,
    )
    sample_records = _build_sample_records(species_name, project_summaries)
    coordinate_provenance_records = build_species_coordinate_provenance_rows(
        tuple(project.project_accession for project in project_summaries)
    )
    site_evidence_records = build_species_site_evidence_rows(
        tuple(project.project_accession for project in project_summaries)
    )
    locality_records, locality_refusals = build_species_project_locality_records(
        species_name,
        project_summaries,
    )
    study_summaries = _build_study_summaries(project_summaries)
    lineage_records = _build_lineage_records(
        species_manifest.species,
        project_summaries,
        study_summaries,
    )
    return AdnaSpeciesNormalizationBundle(
        schema_version="adna-nonhuman-normalization-bundle.v1",
        species_manifest=species_manifest,
        sample_records=sample_records,
        coordinate_provenance_records=coordinate_provenance_records,
        site_evidence_records=site_evidence_records,
        locality_records=locality_records,
        project_summaries=project_summaries,
        study_summaries=study_summaries,
        lineage_records=lineage_records,
        refusals=project_refusals
        + locality_refusals,
        normalization_scope=(
            "Non-human normalization currently governs accession-backed sample master rows, "
            "project summaries, study summaries, and curated locality summaries. "
            "Site and chronology extraction still vary by accession and remain explicit in "
            "sample inclusion status rather than being silently flattened."
        ),
    )


def normalize_species_anchor(
    value: str,
    *,
    expected_species_name: str | None = None,
) -> AdnaSpeciesDefinition:
    """Normalize one species anchor and optionally enforce one expected identity."""
    species = resolve_species_definition(value)
    if (
        expected_species_name is not None
        and species.latin_name != resolve_species_definition(expected_species_name).latin_name
    ):
        raise ValueError(
            f"Species anchor mismatch: expected {expected_species_name}, got {value}"
        )
    return species


def normalize_breed_label(value: str | None) -> str | None:
    """Normalize a breed-like label without inventing unsupported precision."""
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value.strip())
    if not cleaned:
        return None
    if cleaned.casefold() in {"unknown", "n/a", "na", "not yet curated"}:
        return None
    return cleaned.casefold().replace("_", " ")


def normalize_coordinate_resolution(
    *,
    latitude_text: str,
    longitude_text: str,
    geographic_basis: str | None,
) -> AdnaCoordinateResolution:
    """Normalize a latitude/longitude pair while allowing honest withholding."""
    basis = geographic_basis or ""
    lat_clean = latitude_text.strip()
    lon_clean = longitude_text.strip()
    confidence = _coordinate_confidence_for(basis)
    if not lat_clean and not lon_clean:
        return AdnaCoordinateResolution(
            coordinate=None,
            confidence=confidence,
            source_basis=basis,
            reason="coordinates_withheld_by_source_policy",
        )
    if not lat_clean or not lon_clean:
        raise ValueError("Coordinate normalization requires both latitude and longitude")
    latitude = float(lat_clean)
    longitude = float(lon_clean)
    if not -90.0 <= latitude <= 90.0:
        raise ValueError(f"Latitude out of range: {latitude_text}")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError(f"Longitude out of range: {longitude_text}")
    return AdnaCoordinateResolution(
        coordinate=AdnaCoordinate(
            latitude=latitude,
            longitude=longitude,
            latitude_text=lat_clean,
            longitude_text=lon_clean,
            confidence=confidence,
        ),
        confidence=confidence,
        source_basis=basis,
        reason="parsed_coordinate_pair",
    )


def normalize_chronology_text(
    value: str,
    *,
    dating_basis: str = "unknown",
) -> AdnaChronology:
    """Normalize common non-human chronology expressions without overclaiming precision."""
    text = value.strip()
    basis = dating_basis or "unknown"
    if not text:
        return AdnaChronology(
            original_text="",
            time_start_bp=None,
            time_end_bp=None,
            time_mean_bp=None,
            dating_basis=basis,
        )
    if bp_window := parse_bp_window_label(text):
        return AdnaChronology(
            original_text=text,
            time_start_bp=bp_window[0],
            time_end_bp=bp_window[1],
            time_mean_bp=midpoint_bp_year(bp_window[0], bp_window[1]),
            dating_basis=basis,
        )
    if bce_range := _BCE_RANGE_RE.search(text):
        older_bp = _bce_to_bp(int(bce_range.group("start")))
        younger_bp = _bce_to_bp(int(bce_range.group("end")))
        interval = normalize_bp_interval(older_bp, younger_bp)
        assert interval is not None
        return AdnaChronology(
            original_text=text,
            time_start_bp=interval[0],
            time_end_bp=interval[1],
            time_mean_bp=midpoint_bp_year(interval[0], interval[1]),
            dating_basis=basis,
        )
    if ce_range := _CE_RANGE_RE.search(text):
        first_bp = _ce_to_bp(int(ce_range.group("start")))
        second_bp = _ce_to_bp(int(ce_range.group("end")))
        interval = normalize_bp_interval(first_bp, second_bp)
        assert interval is not None
        return AdnaChronology(
            original_text=text,
            time_start_bp=interval[0],
            time_end_bp=interval[1],
            time_mean_bp=midpoint_bp_year(interval[0], interval[1]),
            dating_basis=basis,
        )
    if bce_single := _BCE_SINGLE_RE.search(text):
        year_bp = _bce_to_bp(int(bce_single.group("year")))
        return AdnaChronology(
            original_text=text,
            time_start_bp=year_bp,
            time_end_bp=year_bp,
            time_mean_bp=year_bp,
            dating_basis=basis,
        )
    if ce_single := _CE_SINGLE_RE.search(text):
        year_bp = _ce_to_bp(int(ce_single.group("year")))
        return AdnaChronology(
            original_text=text,
            time_start_bp=year_bp,
            time_end_bp=year_bp,
            time_mean_bp=year_bp,
            dating_basis=basis,
        )
    if mean_match := _BP_MEAN_STDDEV_RE.search(text):
        mean_bp = int(mean_match.group("mean"))
        stddev_bp = mean_match.group("stddev")
        return AdnaChronology(
            original_text=text,
            time_start_bp=mean_bp,
            time_end_bp=mean_bp,
            time_mean_bp=mean_bp,
            date_stddev_bp=stddev_bp,
            dating_basis=basis,
        )
    if point_match := _BP_SINGLE_RE.search(text):
        mean_bp = int(point_match.group("mean"))
        return AdnaChronology(
            original_text=text,
            time_start_bp=mean_bp,
            time_end_bp=mean_bp,
            time_mean_bp=mean_bp,
            dating_basis=basis,
        )
    return AdnaChronology(
        original_text=text,
        time_start_bp=None,
        time_end_bp=None,
        time_mean_bp=None,
        dating_basis=basis,
    )


def normalize_explicit_bp_window(
    start_bp: int | None,
    end_bp: int | None,
    *,
    original_text: str = "",
    dating_basis: str = "bp_window",
) -> AdnaChronology:
    """Normalize an explicit structured BP interval while refusing inverted input."""
    if start_bp is None or end_bp is None:
        raise ValueError("Structured BP windows require both start and end values")
    if start_bp > end_bp:
        raise ValueError("Structured BP windows must be ordered younger-to-older")
    return AdnaChronology(
        original_text=original_text or build_bp_interval_label(start_bp, end_bp),
        time_start_bp=start_bp,
        time_end_bp=end_bp,
        time_mean_bp=midpoint_bp_year(start_bp, end_bp),
        dating_basis=dating_basis,
    )


def _build_sample_records(
    species_name: str,
    project_summaries: tuple[AdnaProjectSummary, ...],
) -> tuple[AdnaSampleRecord, ...]:
    species = resolve_species_definition(species_name)
    project_index = {project.project_accession: project for project in project_summaries}
    chronology_index = {
        project_accession: {
            chronology_row.repo_stable_sample_id: chronology_row
            for chronology_row in build_project_sample_chronology_rows(
                _default_data_root(),
                project_accession,
            )
        }
        for project_accession in project_index
    }
    sample_records: list[AdnaSampleRecord] = []

    for row in build_species_curated_sample_rows(species_name):
        project = project_index[row.project_accession]
        chronology_row = chronology_index.get(row.project_accession, {}).get(
            row.stable_sample_id
        )
        coordinate_resolution = normalize_coordinate_resolution(
            latitude_text=row.latitude_text,
            longitude_text=row.longitude_text,
            geographic_basis=row.coordinate_basis,
        )
        chronology = (
            normalize_explicit_bp_window(
                chronology_row.time_start_bp if chronology_row is not None else row.time_start_bp,
                chronology_row.time_end_bp if chronology_row is not None else row.time_end_bp,
                original_text=(
                    chronology_row.chronology_text if chronology_row is not None else row.chronology_text
                ),
                dating_basis=chronology_row.dating_basis if chronology_row is not None else row.dating_basis,
            )
            if (
                chronology_row is not None
                and chronology_row.time_start_bp is not None
                and chronology_row.time_end_bp is not None
            )
            or (chronology_row is None and row.time_start_bp is not None and row.time_end_bp is not None)
            else normalize_chronology_text(
                chronology_row.chronology_text if chronology_row is not None else row.chronology_text,
                dating_basis=chronology_row.dating_basis if chronology_row is not None else row.dating_basis,
            )
        )
        locality_text = row.site_label
        sample_records.append(
            AdnaSampleRecord(
                identity=AdnaSampleIdentity(
                    namespace=f"{species.slug}:curated_sample",
                    stable_token=(
                        f"{species.slug}:sample:{row.stable_sample_id.casefold()}"
                    ),
                    accession_lineage=(
                        f"species:{species.latin_name}",
                        f"source:{row.source_family}",
                        f"project:{row.project_accession}",
                        f"sample:{row.stable_sample_id}",
                    ),
                ),
                locality_identity=AdnaLocalityIdentity(
                    namespace=f"{species.slug}:sample_locality",
                    stable_token=(
                        f"{species.slug}:sample-site:{row.project_accession.casefold()}"
                    ),
                    locality_text=locality_text,
                    political_entity=row.political_entity,
                    source_anchor_tokens=(row.project_accession, row.sample_basis),
                ),
                species_latin_name=row.species_latin_name,
                species_common_name=row.species_common_name,
                source_family=row.source_family,
                source_release=row.source_release,
                record_modality=row.record_modality,
                review_strength=project.review_strength,
                provenance_quality=row.provenance_quality,
                master_id=row.stable_sample_id,
                group_id=row.project_accession,
                locality=(
                    None
                    if row.political_entity is None
                    and "not yet extracted" in locality_text
                    else locality_text
                ),
                political_entity=row.political_entity,
                coordinates=AdnaCoordinate(
                    latitude=coordinate_resolution.coordinate.latitude
                    if coordinate_resolution.coordinate is not None
                    else None,
                    longitude=coordinate_resolution.coordinate.longitude
                    if coordinate_resolution.coordinate is not None
                    else None,
                    latitude_text=row.latitude_text,
                    longitude_text=row.longitude_text,
                    confidence=coordinate_resolution.confidence,
                ),
                publication=row.publication,
                year_first_published=row.publication_year,
                full_date=row.chronology_text,
                chronology=chronology,
                data_type=row.data_type,
                molecular_sex="",
                datasets=(project.summary_token,),
                project_accession=row.project_accession,
                paper_doi=row.paper_doi,
                paper_url=row.paper_url,
                supplementary_source=row.supplementary_source,
                inclusion_status=row.inclusion_status,
                inclusion_note=row.inclusion_note,
                chronology_strength=(
                    chronology_row.chronology_strength
                    if chronology_row is not None
                    else "project_context_interval"
                    if chronology.time_start_bp is not None and chronology.time_end_bp is not None
                    else "project_context_text_only"
                    if chronology.original_text
                    else "unresolved"
                ),
                chronology_normalization_status=(
                    chronology_row.chronology_normalization_status
                    if chronology_row is not None
                    else "normalized_point"
                    if chronology.time_start_bp is not None
                    and chronology.time_end_bp is not None
                    and chronology.time_start_bp == chronology.time_end_bp
                    else "normalized_interval"
                    if chronology.time_start_bp is not None and chronology.time_end_bp is not None
                    else "text_only_unparsed"
                    if chronology.original_text
                    else "unresolved"
                ),
                chronology_provenance_path=(
                    chronology_row.chronology_provenance_path if chronology_row is not None else ""
                ),
                chronology_provenance_kind=(
                    chronology_row.chronology_provenance_kind if chronology_row is not None else ""
                ),
                chronology_provenance_locator=(
                    chronology_row.chronology_provenance_locator if chronology_row is not None else ""
                ),
                chronology_provenance_text=(
                    chronology_row.chronology_provenance_text if chronology_row is not None else ""
                ),
                chronology_conflict_note=(
                    chronology_row.chronology_conflict_note if chronology_row is not None else ""
                ),
                sample_basis=row.sample_basis,
                archive_native_sample_id=row.archive_native_sample_id,
                paper_native_sample_label=row.paper_native_sample_label,
                supplementary_table_sample_label=row.supplementary_table_sample_label,
                sample_evidence_status=row.sample_evidence_status,
                sample_lineage_path=row.sample_lineage_path,
                sample_lineage_locator=row.sample_lineage_locator,
                sample_lineage_excerpt=row.sample_lineage_excerpt,
                sample_identity_resolution=row.sample_identity_resolution,
                sample_ambiguity_note=row.sample_ambiguity_note,
            )
        )

    sample_records.sort(key=lambda item: (item.project_accession, item.genetic_id))
    return tuple(sample_records)


def _default_data_root() -> Path:
    return Path(__file__).resolve().parents[5] / "data"


def build_species_project_locality_records(
    species_name: str,
    project_summaries: tuple[AdnaProjectSummary, ...],
) -> tuple[tuple[AdnaLocalitySummary, ...], tuple[AdnaNormalizationRefusal, ...]]:
    """Build curated non-human project locality rows and explicit locality refusals."""
    species = resolve_species_definition(species_name)
    project_index = {summary.project_accession: summary for summary in project_summaries}
    archive_index = {
        project.project_accession: project
        for project in build_species_archive_projects(species_name)
    }
    locality_records: list[AdnaLocalitySummary] = []
    refusals: list[AdnaNormalizationRefusal] = []

    leads = build_species_project_locality_leads(tuple(project_index))
    covered_accessions = {lead.project_accession for lead in leads}

    for lead in leads:
        project = project_index.get(lead.project_accession)
        if project is None:
            continue
        project_context = resolve_project_context(archive_index[lead.project_accession])
        coordinate_resolution = normalize_coordinate_resolution(
            latitude_text=lead.latitude_text,
            longitude_text=lead.longitude_text,
            geographic_basis=lead.coordinate_basis,
        )
        chronology = (
            normalize_explicit_bp_window(
                lead.time_start_bp,
                lead.time_end_bp,
                original_text=lead.chronology_text,
                dating_basis=project.chronology_basis or project.dating_basis or "bp_window",
            )
            if lead.time_start_bp is not None and lead.time_end_bp is not None
            else normalize_chronology_text(
                lead.chronology_text,
                dating_basis=project.chronology_basis or project.dating_basis or "unknown",
            )
        )
        identity = AdnaLocalityIdentity(
            namespace=f"{species.slug}:project_locality",
            stable_token=(
                f"{species.slug}:project-locality:{lead.project_accession.casefold()}"
            ),
            locality_text=lead.locality_text,
            political_entity=lead.political_entity,
            source_anchor_tokens=(
                lead.project_accession,
                lead.latitude_text,
                lead.longitude_text,
            ),
        )
        locality_records.append(
            AdnaLocalitySummary(
                identity=identity,
                species_latin_name=project.species_latin_name,
                species_common_name=project.species_common_name,
                source_family=project.source_family,
                source_releases=(project.source_release,),
                record_modalities=(project.record_modality,),
                review_strengths=(project.review_strength,),
                provenance_qualities=(project.evidence_strength,),
                locality=lead.locality_text,
                coordinates=AdnaCoordinate(
                    latitude=coordinate_resolution.coordinate.latitude
                    if coordinate_resolution.coordinate is not None
                    else None,
                    longitude=coordinate_resolution.coordinate.longitude
                    if coordinate_resolution.coordinate is not None
                    else None,
                    latitude_text=lead.latitude_text,
                    longitude_text=lead.longitude_text,
                    confidence=coordinate_resolution.confidence,
                ),
                sample_count=1,
                sample_ids=(lead.project_accession,),
                datasets=(project.summary_token,),
                chronology=chronology,
                sample_namespace=f"{species.slug}:project_locality",
                project_accessions=(lead.project_accession,),
                original_location_text=lead.locality_text,
                nordic_inclusion=project_context.nordic_relevance
                == "nordic_relevant_unmapped",
                nordic_inclusion_reason=project_context.nordic_relevance_reason,
                interpretation_note=lead.interpretation_note,
            )
        )

    for project in project_summaries:
        if project.project_accession in covered_accessions:
            continue
        refusals.append(
            AdnaNormalizationRefusal(
                schema_version="adna-normalization-refusal.v1",
                species_latin_name=species.latin_name,
                source_token=project.project_accession,
                record_kind="locality_records",
                reason="locality_lead_not_yet_curated",
                detail=(
                    "This project already ships project-level interpretation, but a defensible locality lead "
                    "has not yet been curated into the species-owned locality artifact."
                ),
            )
        )

    locality_records.sort(
        key=lambda item: (
            item.project_accessions[0] if item.project_accessions else item.locality_token,
            item.locality_token,
        )
    )
    refusals.sort(key=lambda item: item.source_token)
    return tuple(locality_records), tuple(refusals)


def _build_project_summary(
    project,
    curation_class: str,
) -> AdnaProjectSummary:
    species = normalize_species_anchor(project.species_latin_name)
    project_context = resolve_project_context(project)
    paper_doi = None if project.paper_linkage is None else project.paper_linkage.doi
    paper_title = None if project.paper_linkage is None else project.paper_linkage.paper_title
    support_class = _support_class_for(project, curation_class)
    return AdnaProjectSummary(
        schema_version="adna-project-summary.v1",
        summary_token=f"{species.slug}:project:{project.project_accession}",
        species_latin_name=species.latin_name,
        species_common_name=species.common_name,
        project_accession=project.project_accession,
        study_token=_study_token_for(project.project_accession, paper_doi),
        source_family=project.source_family,
        source_release=project.project_accession,
        result_kind=project.result_kind,
        archive_status=project.archive_status,
        evidence_strength=classify_archive_project_evidence(project),
        review_strength=_review_strength_for(project.archive_status, curation_class, paper_doi),
        support_class=support_class,
        record_modality=_record_modality_for(project),
        domestication_status=_domestication_status_for(curation_class),
        domestication_scope=project.domestication_scope,
        comparator_status=curation_class == "comparator_only"
        or project.archive_status == "comparator_only",
        normalized_breed_label=normalize_breed_label(_breed_label_from_notes(project.notes)),
        sequencing_target=project.sequencing_target,
        material_basis=project.material_basis,
        chronology_basis=project.dating_basis,
        dating_basis=project.dating_basis,
        geographic_basis=project.geographic_basis,
        coordinate_policy=_coordinate_policy_for(project.geographic_basis),
        chronology_policy=_chronology_policy_for(project.dating_basis),
        paper_title=paper_title,
        paper_doi=paper_doi,
        paper_url=_paper_url_for(project),
        nordic_relevance=project_context.nordic_relevance,
        nordic_relevance_reason=project_context.nordic_relevance_reason,
        interpretation_caveat=_interpretation_caveat_for(
            project=project,
            support_class=support_class,
            project_context=project_context,
        ),
        notes=project.notes,
    )


def _normalize_project_summaries(
    species_name: str,
    curation_class: str,
) -> tuple[tuple[AdnaProjectSummary, ...], tuple[AdnaNormalizationRefusal, ...]]:
    project_summaries: list[AdnaProjectSummary] = []
    refusals: list[AdnaNormalizationRefusal] = []
    for project in build_species_archive_projects(species_name):
        try:
            project_summaries.append(_build_project_summary(project, curation_class))
        except ValueError as exc:
            refusals.append(
                AdnaNormalizationRefusal(
                    schema_version="adna-normalization-refusal.v1",
                    species_latin_name=resolve_species_definition(species_name).latin_name,
                    source_token=project.project_accession,
                    record_kind="project_summary",
                    reason="defensible_species_anchor_missing",
                    detail=str(exc),
                )
            )
    normalized = _deduplicate_project_summaries(
        tuple(sorted(project_summaries, key=lambda item: item.summary_token))
    )
    return normalized, tuple(refusals)


def _deduplicate_project_summaries(
    summaries: tuple[AdnaProjectSummary, ...],
) -> tuple[AdnaProjectSummary, ...]:
    deduplicated: dict[str, AdnaProjectSummary] = {}
    for summary in summaries:
        previous = deduplicated.get(summary.summary_token)
        if previous is None:
            deduplicated[summary.summary_token] = summary
            continue
        if previous.as_dict() != summary.as_dict():
            raise ValueError(
                f"Conflicting non-human project normalization for {summary.summary_token}"
            )
    return tuple(deduplicated[token] for token in sorted(deduplicated))


def _build_study_summaries(
    project_summaries: tuple[AdnaProjectSummary, ...],
) -> tuple[AdnaStudySummary, ...]:
    grouped: dict[str, list[AdnaProjectSummary]] = defaultdict(list)
    for summary in project_summaries:
        grouped[summary.study_token].append(summary)

    study_summaries: list[AdnaStudySummary] = []
    for study_token, group in grouped.items():
        ordered = tuple(sorted(group, key=lambda item: item.project_accession))
        lead = ordered[0]
        study_summaries.append(
            AdnaStudySummary(
                schema_version="adna-study-summary.v1",
                summary_token=study_token,
                species_latin_name=lead.species_latin_name,
                species_common_name=lead.species_common_name,
                project_accessions=tuple(item.project_accession for item in ordered),
                source_families=tuple(sorted({item.source_family for item in ordered})),
                archive_statuses=tuple(sorted({item.archive_status for item in ordered})),
                evidence_strengths=tuple(
                    sorted({item.evidence_strength for item in ordered})
                ),
                domestication_status=lead.domestication_status,
                paper_title=lead.paper_title,
                paper_doi=lead.paper_doi,
                sequencing_targets=tuple(
                    sorted(
                        {
                            item.sequencing_target
                            for item in ordered
                            if item.sequencing_target is not None
                        }
                    )
                ),
                material_bases=tuple(
                    sorted(
                        {
                            item.material_basis
                            for item in ordered
                            if item.material_basis is not None
                        }
                    )
                ),
                dating_bases=tuple(
                    sorted(
                        {
                            item.dating_basis
                            for item in ordered
                            if item.dating_basis is not None
                        }
                    )
                ),
                geographic_bases=tuple(
                    sorted(
                        {
                            item.geographic_basis
                            for item in ordered
                            if item.geographic_basis is not None
                        }
                    )
                ),
            )
        )
    return tuple(sorted(study_summaries, key=lambda item: item.summary_token))


def _build_lineage_records(
    species: AdnaSpeciesDefinition,
    project_summaries: tuple[AdnaProjectSummary, ...],
    study_summaries: tuple[AdnaStudySummary, ...],
) -> tuple[AdnaNormalizationLineage, ...]:
    lineages: list[AdnaNormalizationLineage] = []
    project_by_token = {project.summary_token: project for project in project_summaries}
    for project in project_summaries:
        lineages.append(
            AdnaNormalizationLineage(
                schema_version="adna-normalization-lineage.v1",
                output_record_kind="project_summary",
                output_record_token=project.summary_token,
                source_artifact_path=_source_artifact_path(species, project),
                source_accessions=(project.project_accession,),
                lineage_tokens=(
                    f"species:{species.latin_name}",
                    f"source_family:{project.source_family}",
                    f"project_accession:{project.project_accession}",
                    f"archive_status:{project.archive_status}",
                ),
            )
        )
    for study in study_summaries:
        first_project = project_by_token.get(
            f"{species.slug}:project:{study.project_accessions[0]}"
        )
        assert first_project is not None
        lineages.append(
            AdnaNormalizationLineage(
                schema_version="adna-normalization-lineage.v1",
                output_record_kind="study_summary",
                output_record_token=study.summary_token,
                source_artifact_path=_source_artifact_path(species, first_project),
                source_accessions=study.project_accessions,
                lineage_tokens=(
                    f"species:{species.latin_name}",
                    f"study_token:{study.summary_token}",
                    *(f"project_accession:{accession}" for accession in study.project_accessions),
                ),
            )
        )
    return tuple(sorted(lineages, key=lambda item: (item.output_record_kind, item.output_record_token)))


def _study_token_for(project_accession: str, paper_doi: str | None) -> str:
    if paper_doi:
        return "study:" + re.sub(r"[^a-z0-9]+", "-", paper_doi.casefold()).strip("-")
    return f"study:project:{project_accession.casefold()}"


def _review_strength_for(
    archive_status: str,
    curation_class: str,
    paper_doi: str | None,
) -> str:
    if curation_class == "comparator_only" or archive_status == "comparator_only":
        return "comparator_only"
    if paper_doi:
        return "primary_paper_pinned"
    return "archive_verified_needs_paper_pinning"


def _record_modality_for(project) -> str:
    sequencing_target = (project.sequencing_target or "").casefold()
    if "mitogenome" in sequencing_target:
        return "mitogenome_only"
    if project.source_family == "GenBank":
        return "paper_only"
    return "archive_reads"


def _domestication_status_for(curation_class: str) -> str:
    if curation_class == "paper_pinned_core":
        return "domesticated_core"
    if curation_class == "comparator_only":
        return "comparator_only"
    if curation_class in {
        "genbank_only_or_non_project_archive",
        "weak_or_precuration",
    }:
        return "thin_evidence"
    return "unsupported"


def _support_class_for(project, curation_class: str) -> str:
    if project.archive_status == "reject_or_out_of_scope":
        return "rejected_or_out_of_scope"
    if curation_class == "comparator_only" or project.archive_status == "comparator_only":
        return "comparator_only"
    if project.domestication_scope == "wild_or_progenitor_context":
        return "wild_or_progenitor_context"
    if project.archive_status == "paper_pinned_core":
        return "domesticated_core_curated"
    return "archive_pending_paper_linkage"


def _paper_url_for(project) -> str | None:
    if project.paper_linkage is None:
        return None
    if project.paper_linkage.doi:
        return f"https://doi.org/{project.paper_linkage.doi}"
    if project.paper_linkage.pmc_id:
        return f"https://pmc.ncbi.nlm.nih.gov/articles/{project.paper_linkage.pmc_id}/"
    if project.paper_linkage.pubmed_id:
        return f"https://pubmed.ncbi.nlm.nih.gov/{project.paper_linkage.pubmed_id}/"
    return None


def _interpretation_caveat_for(
    *,
    project,
    support_class: str,
    project_context,
) -> str:
    caveats = [project.notes.strip()]

    if support_class == "archive_pending_paper_linkage":
        caveats.append(
            "Keep this project out of strong pollenomics interpretation until the primary paper linkage is encoded explicitly."
        )
    if support_class == "wild_or_progenitor_context":
        caveats.append(
            "Treat this as wild or progenitor context, not as direct domesticated-animal support."
        )
    if support_class == "comparator_only":
        caveats.append(
            "Use this only as comparator context and do not count it toward domesticated-core support."
        )
    if support_class == "rejected_or_out_of_scope":
        caveats.append(
            "Keep this row visible as a reject so archive presence does not masquerade as curated support."
        )

    if project_context.nordic_relevance == "nordic_relevant_unmapped":
        caveats.append("Nordic-relevant lead remains unmapped in the shipped public atlas.")
    elif project_context.nordic_relevance == "nordic_adjacent":
        caveats.append(
            "Nordic-adjacent context does not justify a Nordic-localized project claim."
        )
    elif project_context.nordic_relevance == "non_nordic":
        caveats.append(
            "This project stays in the evidence base for comparative context, not as shipped Nordic evidence."
        )

    return " ".join(dict.fromkeys(part for part in caveats if part))


def _coordinate_policy_for(geographic_basis: str | None) -> str:
    basis = (geographic_basis or "").casefold()
    if "site_level" in basis:
        return "site_level_coordinates_expected"
    if "locality_text" in basis:
        return "locality_text_without_coordinates_allowed"
    if "country_only" in basis:
        return "country_only_withheld_coordinates_allowed"
    return "manual_coordinate_review_required"


def _coordinate_confidence_for(geographic_basis: str) -> str:
    basis = geographic_basis.casefold()
    if "exact" in basis:
        return "exact"
    if "named_site_geocoding" in basis:
        return "approximate"
    if any(
        token in basis
        for token in (
            "direct_published_coordinates",
            "supplementary_table_coordinates",
            "archive_coordinates",
        )
    ):
        return "exact"
    if "approximate" in basis or "site_level" in basis:
        return "approximate"
    if "inferred" in basis:
        return "inferred"
    if any(
        token in basis
        for token in (
            "country_only",
            "locality_text",
            "withheld",
            "region_centroid_fallback",
            "unresolved_location_state",
        )
    ):
        return "withheld"
    return "unknown"


def _chronology_policy_for(dating_basis: str | None) -> str:
    basis = (dating_basis or "").casefold()
    if "radiocarbon" in basis:
        return "bp_interval_expected"
    if "historical" in basis:
        return "historical_interval_or_label_allowed"
    if "archaeological" in basis:
        return "archaeological_period_label_allowed"
    if "mixed" in basis:
        return "mixed_chronology_review_required"
    return "manual_chronology_review_required"


def _breed_label_from_notes(notes: str) -> str | None:
    lowered = notes.casefold()
    if "przewalski" in lowered:
        return "przewalski-associated"
    if "dromedary" in lowered:
        return "dromedary-associated"
    return None


def _source_artifact_path(
    species: AdnaSpeciesDefinition,
    project: AdnaProjectSummary,
) -> str:
    root = f"{ADNA_SPECIES_DIR}/{species.slug}/raw"
    family = project.source_family.casefold()
    suffix = "filereport.tsv"
    if family == "genbank":
        suffix = "summary.tsv"
    if family == "manual_curation":
        suffix = "review.md"
    return f"{root}/{family}/{project.project_accession}.{suffix}"


def _bce_to_bp(year_bce: int) -> int:
    return year_bce + 1949


def _ce_to_bp(year_ce: int) -> int:
    return max(0, 1950 - year_ce)
