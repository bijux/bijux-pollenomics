"""Fail-closed workbook-to-archive reconciliation for progenitor cattle."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)
from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from .evidence import (
    ARCHIVE_IDENTITIES,
    AUROCHS_NATURAL_HISTORY_ARCHIVE_TEXT_SHA256,
    AUROCHS_NATURAL_HISTORY_PROJECT_ACCESSION,
    AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256,
    PAPER_ONLY_SAMPLE_LABEL,
)
from .source_evidence import (
    AurochsArchiveEvidence,
    AurochsWorkbookEvidence,
    _parse_archive_evidence,
    _parse_workbook_evidence,
)


@dataclass(frozen=True)
class AurochsNaturalHistoryReconciliationRow:
    """One joined sequence or explicitly refused paper-only aurochs identity."""

    workbook: AurochsWorkbookEvidence
    archive: AurochsArchiveEvidence | None
    reconciliation_status: str
    sequencing_status: str
    refusal_reason: str

    def to_sample_master_row(
        self,
        *,
        species: AdnaSpeciesDefinition,
        project: AdnaArchiveProject,
        workbook_source_path: str,
        archive_source_path: str,
    ) -> AdnaProjectSampleMasterRow:
        """Preserve source claims while refusing domestication or accession inference."""
        source = self.workbook
        archive = self.archive
        accession = "" if archive is None else archive.sample_accession
        chronology_basis, chronology_class, chronology_precision = {
            "calibrated_radiocarbon_interval": (
                "radiocarbon",
                "direct_radiocarbon_date",
                "sample_precise_interval",
            ),
            "mitochondrial_beast_interval": (
                "mitochondrial_phylogenetic_model",
                "modeled_sample_date",
                "sample_approximate_or_modeled",
            ),
            "source_chronology_unavailable": (
                "unknown",
                "unresolved",
                "unresolved",
            ),
        }[source.chronology_kind]
        lineage_paths = [workbook_source_path]
        lineage_locators = [source.source_locator]
        if archive is not None:
            lineage_paths.append(archive_source_path)
            lineage_locators.append(archive.source_locator)
        interval_text = (
            ""
            if source.younger_bp is None or source.older_bp is None
            else f"canonical BP interval [{source.younger_bp}, {source.older_bp}]"
        )
        mean_text = (
            ""
            if source.mean_bp is None
            else f"published analysis mean {source.analysis_mean_text} BP"
        )
        rounded_mean_text = (
            ""
            if source.mean_bp is None or source.mean_bp.is_integer()
            else (
                f"normalized integer mean {round(source.mean_bp)} BP; "
                "source decimal precision retained in the published analysis mean"
            )
        )
        excerpt_parts = (
            f"workbook sample {source.sample_label}",
            (
                f"specimen {source.original_specimen_id}"
                if source.original_specimen_id
                else "source specimen ID unavailable"
            ),
            f"locality {source.locality_text}, {source.political_entity}",
            (
                "source proximal coordinates "
                f"{source.latitude_text}, {source.longitude_text}"
            ),
            (
                f"source BP claim {source.source_bp_text}"
                if source.source_bp_text
                else "source chronology unavailable: workbook date fields are empty"
            ),
            interval_text,
            mean_text,
            rounded_mean_text,
            f"source taxonomy {source.source_native_scientific_name}",
            f'population label "{source.population_label}"',
            "admitted only as explicit wild/progenitor context",
            self.refusal_reason,
        )
        return AdnaProjectSampleMasterRow(
            species_latin_name=species.latin_name,
            species_common_name=species.common_name,
            project_accession=project.project_accession,
            repo_stable_sample_id=(
                f"{project.project_accession}:{accession}".casefold()
                if accession
                else (
                    f"{project.project_accession}:supplement:{source.sample_label}"
                ).casefold()
            ),
            archive_native_sample_id=accession,
            paper_native_sample_label=source.sample_label,
            supplementary_table_sample_label=source.sample_label,
            preferred_sample_label=source.sample_label,
            sample_basis=(
                "supplementary_table_archive_primary_source_join"
                if archive is not None
                else "supplementary_table_paper_only_sequence_refusal"
            ),
            sample_evidence_status="direct_table_extracted",
            sample_lineage_path=" || ".join(lineage_paths),
            sample_lineage_locator=" || ".join(lineage_locators),
            sample_lineage_excerpt=" | ".join(
                value for value in excerpt_parts if value
            )[:1000],
            sample_identity_resolution="final"
            if archive is not None
            else "provisional",
            sample_ambiguity_note=self.refusal_reason,
            locality_text=source.locality_text,
            political_entity=source.political_entity,
            latitude_text=(
                "" if source.latitude_text == "Unknown" else source.latitude_text
            ),
            longitude_text=(
                "" if source.longitude_text == "Unknown" else source.longitude_text
            ),
            chronology_text=(
                ""
                if source.younger_bp is None or source.older_bp is None
                else f"{source.younger_bp}-{source.older_bp} BP"
            ),
            chronology_dating_basis=chronology_basis,
            chronology_evidence_class=chronology_class,
            chronology_precision_posture=chronology_precision,
            source_native_tax_id=(
                "" if archive is None else archive.source_native_tax_id
            ),
            source_native_scientific_name=source.source_native_scientific_name,
            taxon_alignment_status="project_species_mismatch",
            source_native_identity_kind=(
                "biological_sample_accession"
                if archive is not None
                else "supplementary_sample_label"
            ),
            chronology_time_mean_bp=(
                None if source.mean_bp is None else round(source.mean_bp)
            ),
        )


def _build_aurochs_natural_history_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    workbook_source_path: str,
    workbook_rows: tuple[tuple[str, ...], ...],
    workbook_sha256: str,
    archive_source_path: str,
    archive_text: str,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Build explicit progenitor archive joins and the Fre1 paper-only refusal."""
    if species.latin_name != "Bos taurus":
        raise ValueError("aurochs natural-history adapter requires Bos taurus scope")
    if project.project_accession != AUROCHS_NATURAL_HISTORY_PROJECT_ACCESSION:
        raise ValueError("aurochs natural-history adapter requires PRJEB75467")
    if project.domestication_scope != "wild_or_progenitor_context":
        raise ValueError("PRJEB75467 wild/progenitor scope contract drift")
    reconciled = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_sha256,
        archive_text=archive_text,
    )
    return tuple(
        row.to_sample_master_row(
            species=species,
            project=project,
            workbook_source_path=workbook_source_path,
            archive_source_path=archive_source_path,
        )
        for row in reconciled
    )


def _reconcile_aurochs_natural_history(
    *,
    workbook_rows: tuple[tuple[str, ...], ...],
    workbook_sha256: str,
    archive_text: str,
) -> tuple[AurochsNaturalHistoryReconciliationRow, ...]:
    """Reconcile the hash-bound sources with no heuristic accession assignment."""
    if workbook_sha256 != AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256:
        raise ValueError("PRJEB75467 supplementary workbook sha256 drift")
    if (
        sha256(archive_text.encode("utf-8")).hexdigest()
        != AUROCHS_NATURAL_HISTORY_ARCHIVE_TEXT_SHA256
    ):
        raise ValueError("PRJEB75467 decompressed archive sha256 drift")
    workbook = _parse_workbook_evidence(workbook_rows)
    archive = _parse_archive_evidence(archive_text)
    reconciled = tuple(
        AurochsNaturalHistoryReconciliationRow(
            workbook=workbook[identity.sample_label],
            archive=archive[identity.sample_label],
            reconciliation_status="workbook_archive_literal_join",
            sequencing_status="archive_sequence_available",
            refusal_reason="",
        )
        for identity in ARCHIVE_IDENTITIES
    )
    fre1 = workbook[PAPER_ONLY_SAMPLE_LABEL]
    return (
        *reconciled,
        AurochsNaturalHistoryReconciliationRow(
            workbook=fre1,
            archive=None,
            reconciliation_status="paper_only_no_archive_accession",
            sequencing_status="archive_sequence_identity_not_evidenced",
            refusal_reason=(
                "Fre1 is paper-only: the workbook reports UDG treatment 'No' and "
                "0.0 genomic coverage, while the pinned PRJEB75467 archive has no "
                "Fre1 filename or BioSample identity; an accession is not inferred."
            ),
        ),
    )


__all__ = [
    "AurochsArchiveEvidence",
    "AurochsNaturalHistoryReconciliationRow",
    "AurochsWorkbookEvidence",
    "_build_aurochs_natural_history_rows",
    "_parse_archive_evidence",
    "_parse_workbook_evidence",
    "_reconcile_aurochs_natural_history",
]
