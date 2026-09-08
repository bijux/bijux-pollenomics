"""Evidence-bound pig-panel reconciliation and conservative master projection."""

from __future__ import annotations

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from ...models import AdnaProjectSampleMasterRow
from .models import PigPanelJoinAuditRow as PigPanelJoinAuditRow
from .site_coordinates import (
    PIG_SITE_COORDINATE_EVIDENCE_PATH as PIG_SITE_COORDINATE_EVIDENCE_PATH,
)
from .site_coordinates import (
    PigSiteCoordinateEvidence as PigSiteCoordinateEvidence,
)
from .site_coordinates import (
    load_pig_site_coordinate_evidence as load_pig_site_coordinate_evidence,
)
from .source_evidence import build_pig_panel_join_audit as build_pig_panel_join_audit


def _build_pig_panel_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
    modern_source_path: str,
    modern_rows: tuple[tuple[str, ...], ...],
    archive_source_path: str,
    archive_text: str,
    coordinate_evidence: tuple[PigSiteCoordinateEvidence, ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if species.latin_name != "Sus scrofa domesticus":
        raise ValueError("Pig-panel admission requires Sus scrofa domesticus")
    if project.project_accession != "PRJEB30282":
        raise ValueError("Pig-panel admission requires PRJEB30282")
    audit = build_pig_panel_join_audit(
        source_path=source_path,
        rows=rows,
        modern_source_path=modern_source_path,
        modern_rows=modern_rows,
        archive_source_path=archive_source_path,
        archive_text=archive_text,
        coordinate_evidence=coordinate_evidence,
    )
    return tuple(
        _master_row(species=species, project=project, audit=row) for row in audit
    )


def _master_row(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    audit: PigPanelJoinAuditRow,
) -> AdnaProjectSampleMasterRow:
    admitted_chronology = (
        audit.chronology_disposition == "admitted_existing_context_point"
    )
    return AdnaProjectSampleMasterRow(
        species_latin_name=species.latin_name,
        species_common_name=species.common_name,
        project_accession=project.project_accession,
        repo_stable_sample_id=(
            f"{project.project_accession}:{audit.archive_native_sample_id}".casefold()
        ),
        archive_native_sample_id=audit.archive_native_sample_id,
        paper_native_sample_label=audit.sample_label,
        supplementary_table_sample_label=audit.sample_label,
        preferred_sample_label=audit.sample_label,
        sample_basis=(
            "supplementary_table_and_archive_identity_join"
            if audit.source_sample_kind == "ancient_or_archaeological"
            else "supplementary_accession_and_archive_identity_join"
        ),
        sample_evidence_status="direct_table_extracted",
        sample_lineage_path=audit.workbook_source_path,
        sample_lineage_locator=(
            f"sample_accession:{audit.archive_native_sample_id} || "
            f"{audit.workbook_source_locator}"
        ),
        sample_lineage_excerpt=_source_excerpt(audit),
        sample_identity_resolution="final",
        sample_ambiguity_note="",
        locality_text=audit.locality_text,
        political_entity=audit.political_entity,
        latitude_text=audit.latitude_text,
        longitude_text=audit.longitude_text,
        chronology_text=audit.chronology_text,
        chronology_dating_basis=(
            "archaeological_context" if admitted_chronology else ""
        ),
        chronology_evidence_class=(
            "archaeological_context_date" if admitted_chronology else "unresolved"
        ),
        chronology_precision_posture=(
            "sample_approximate_or_modeled" if admitted_chronology else "unresolved"
        ),
    )


def _source_excerpt(audit: PigPanelJoinAuditRow) -> str:
    if audit.source_sample_kind == "modern":
        return (
            f"{audit.sample_label} | population={audit.modern_population} | "
            f"breed_or_country={audit.modern_breed_or_country} | "
            f"coverage={audit.modern_coverage_text} | doi={audit.modern_doi_text} | "
            "locality=not reported | chronology=not reported"
        )
    return (
        f"{audit.sample_label} | previous_extraction_code={audit.previous_extraction_code} | "
        f"mtdna_accession={audit.mtdna_accession_text} | source={audit.source_text} | "
        f"museum_or_sample_code={audit.museum_or_sample_code} | "
        f"additional_sample_information={audit.additional_sample_information} | "
        f"location={audit.locality_text} | country={audit.political_entity} | "
        f"radiocarbon_lab={audit.radiocarbon_lab_number} | "
        f"uncalibrated_date={audit.uncalibrated_date_text} | "
        f"uncalibrated_error={audit.uncalibrated_error_text} | "
        f"calibrated_from_bp={audit.calibrated_from_bp_text} | "
        f"calibrated_to_bp={audit.calibrated_to_bp_text} | "
        f"source_age={audit.source_age_text} | "
        f"source_mean_years_bp={audit.source_mean_age_text} | "
        f"period={audit.period_text} | group={audit.source_group_text} | "
        f"zooarch_status={audit.zooarchaeology_status} | "
        f"combined_status={audit.combined_genetic_zooarchaeology_status} | "
        f"secondary_zooarch_status={audit.secondary_zooarchaeology_status} | "
        f"published={audit.publication_status_text} | "
        f"chronology_disposition={audit.chronology_disposition} | "
        f"domestication_disposition={audit.disposition}"
    )
