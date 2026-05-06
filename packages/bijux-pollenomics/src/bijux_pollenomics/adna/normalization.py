from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import re

from ..core.bp_time import (
    build_bp_interval_label,
    midpoint_bp_year,
    normalize_bp_interval,
    parse_bp_window_label,
)
from .curation import build_species_curation_manifest
from .ena import build_species_archive_projects, classify_archive_project_evidence
from .manifests import AdnaSpeciesManifest, build_species_manifest
from .models import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalitySummary,
    AdnaSampleRecord,
)
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
_BP_MEAN_STDDEV_RE = re.compile(
    r"(?P<mean>\d{1,5})\s*(?:±|\+/-)\s*(?P<stddev>\d{1,4})\s*BP",
    re.IGNORECASE,
)
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
    record_modality: str
    domestication_status: str
    comparator_status: bool
    normalized_breed_label: str | None
    sequencing_target: str | None
    material_basis: str | None
    dating_basis: str | None
    geographic_basis: str | None
    coordinate_policy: str
    chronology_policy: str
    paper_title: str | None
    paper_doi: str | None
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
            "record_modality": self.record_modality,
            "domestication_status": self.domestication_status,
            "comparator_status": self.comparator_status,
            "normalized_breed_label": self.normalized_breed_label,
            "sequencing_target": self.sequencing_target,
            "material_basis": self.material_basis,
            "dating_basis": self.dating_basis,
            "geographic_basis": self.geographic_basis,
            "coordinate_policy": self.coordinate_policy,
            "chronology_policy": self.chronology_policy,
            "paper_title": self.paper_title,
            "paper_doi": self.paper_doi,
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
            "sample_records": [record.__dict__ for record in self.sample_records],
            "locality_records": [record.__dict__ for record in self.locality_records],
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
    study_summaries = _build_study_summaries(project_summaries)
    lineage_records = _build_lineage_records(
        species_manifest.species,
        project_summaries,
        study_summaries,
    )
    return AdnaSpeciesNormalizationBundle(
        schema_version="adna-nonhuman-normalization-bundle.v1",
        species_manifest=species_manifest,
        sample_records=(),
        locality_records=(),
        project_summaries=project_summaries,
        study_summaries=study_summaries,
        lineage_records=lineage_records,
        refusals=project_refusals
        + (
            AdnaNormalizationRefusal(
                schema_version="adna-normalization-refusal.v1",
                species_latin_name=species_manifest.species.latin_name,
                source_token=species_manifest.root_slug,
                record_kind="sample_records",
                reason="sample_level_raw_metadata_unavailable",
                detail=(
                    "The current non-human program has project-level archive curation, "
                    "but not enough sample-level raw metadata to emit sample rows honestly."
                ),
            ),
            AdnaNormalizationRefusal(
                schema_version="adna-normalization-refusal.v1",
                species_latin_name=species_manifest.species.latin_name,
                source_token=species_manifest.root_slug,
                record_kind="locality_records",
                reason="locality_level_raw_metadata_unavailable",
                detail=(
                    "The current non-human program has project-level geographic review, "
                    "but not enough locality-level raw metadata to emit locality rows honestly."
                ),
            ),
        ),
        normalization_scope=(
            "Non-human normalization currently governs project and study summaries. "
            "Sample and locality rows stay empty until archive-backed sample metadata "
            "is curated into species-owned raw inputs."
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


def _build_project_summary(
    project,
    curation_class: str,
) -> AdnaProjectSummary:
    species = normalize_species_anchor(project.species_latin_name)
    paper_doi = None if project.paper_linkage is None else project.paper_linkage.doi
    paper_title = None if project.paper_linkage is None else project.paper_linkage.paper_title
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
        record_modality=_record_modality_for(project),
        domestication_status=_domestication_status_for(curation_class),
        comparator_status=curation_class == "comparator_only"
        or project.archive_status == "comparator_only",
        normalized_breed_label=normalize_breed_label(_breed_label_from_notes(project.notes)),
        sequencing_target=project.sequencing_target,
        material_basis=project.material_basis,
        dating_basis=project.dating_basis,
        geographic_basis=project.geographic_basis,
        coordinate_policy=_coordinate_policy_for(project.geographic_basis),
        chronology_policy=_chronology_policy_for(project.dating_basis),
        paper_title=paper_title,
        paper_doi=paper_doi,
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
    if "approximate" in basis or "site_level" in basis:
        return "approximate"
    if "inferred" in basis:
        return "inferred"
    if any(token in basis for token in ("country_only", "locality_text", "withheld")):
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
    root = f"data/adna/{species.slug}/raw"
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
