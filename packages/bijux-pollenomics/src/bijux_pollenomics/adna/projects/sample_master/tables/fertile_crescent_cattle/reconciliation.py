"""Fail-closed reconciliation for the PRJEB31621 ancient-cattle panel."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from typing import Final

from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)
from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from .evidence import (
    APPROXIMATE_BP_BY_SAMPLE,
    ARCHIVE_ONLY_IDENTITIES,
    ARCHIVE_TEXT_SHA256,
    CANONICAL_BP_INTERVAL_BY_SAMPLE,
    CHRONOLOGY_CONFLICT_BY_SAMPLE,
    DARIALI_SOURCE_COORDINATE,
    EXPLICIT_ARCHIVE_ALIASES,
    FERTILE_CRESCENT_CATTLE_SUPPLEMENT_SHA256,
    SOURCE_INTERVAL_BY_SAMPLE,
    CattleSiteEvidence,
)
from .source_evidence import (
    ArchiveSample,
    parse_archive,
    site_by_sample,
    validate_supplement,
)

FERTILE_CRESCENT_CATTLE_PROJECT_ACCESSION: Final = "PRJEB31621"


@dataclass(frozen=True)
class FertileCrescentCattleReconciliationRow:
    """One source-owned ancient, archive-only, or supplement-only identity."""

    sample_id: str
    archive_native_sample_id: str
    archive_native_experiment_ids: tuple[str, ...]
    archive_submitted_basenames: tuple[str, ...]
    source_native_tax_id: str
    source_native_scientific_name: str
    reconciliation_status: str
    locality_text: str
    political_entity: str
    site_source_locator: str
    approximate_bp: int | None
    source_chronology_text: str
    chronology_source_locator: str
    chronology_conflict_note: str
    source_coordinate_text: str
    coordinate_admission_status: str

    def to_sample_master_row(
        self,
        *,
        species: AdnaSpeciesDefinition,
        project: AdnaArchiveProject,
        archive_source_path: str,
        supplement_source_path: str,
    ) -> AdnaProjectSampleMasterRow:
        """Project evidence without inventing coordinates or temporal precision."""
        joined = self.reconciliation_status in {
            "archive_supplement_literal_join",
            "archive_supplement_explicit_alias_join",
        }
        supplement_only = self.reconciliation_status == "supplement_only"
        has_supplement = joined or supplement_only
        source_path = supplement_source_path if has_supplement else archive_source_path
        locator_parts = []
        if self.archive_native_sample_id:
            locator_parts.append(f"sample_accession:{self.archive_native_sample_id}")
        if has_supplement:
            locator_parts.extend(
                value
                for value in (
                    f"Table S1 sample ID:{self.sample_id}",
                    self.site_source_locator,
                    self.chronology_source_locator,
                )
                if value
            )
        chronology_text = ""
        chronology_basis = "unknown"
        chronology_class = "unresolved"
        chronology_precision = "unresolved"
        canonical_interval = CANONICAL_BP_INTERVAL_BY_SAMPLE.get(self.sample_id)
        if self.approximate_bp is not None:
            chronology_text = f"approx. {self.approximate_bp} BP"
            chronology_basis = "archaeological_period"
            chronology_class = "archaeological_context_date"
            chronology_precision = "sample_approximate_or_modeled"
        elif canonical_interval is not None and not self.chronology_conflict_note:
            younger_bp, older_bp = canonical_interval
            chronology_text = f"{younger_bp}-{older_bp} BP"
            chronology_basis = "archaeological_period"
            chronology_class = "archaeological_context_date"
            chronology_precision = "contextual_interval"
        excerpt_parts = [
            value
            for value in (
                (
                    f"Archive taxonomy {self.source_native_scientific_name} "
                    f"(tax_id {self.source_native_tax_id})"
                    if self.archive_native_sample_id
                    else "No PRJEB31621 archive identity was found"
                ),
                f"supplement sample {self.sample_id}" if has_supplement else "",
                self.locality_text,
                self.source_chronology_text,
                self.chronology_conflict_note,
                self.source_coordinate_text,
            )
            if value
        ]
        return AdnaProjectSampleMasterRow(
            species_latin_name=species.latin_name,
            species_common_name=species.common_name,
            project_accession=project.project_accession,
            repo_stable_sample_id=(
                f"{project.project_accession}:{self.archive_native_sample_id}".casefold()
                if self.archive_native_sample_id
                else f"{project.project_accession}:supplement:{self.sample_id}".casefold()
            ),
            archive_native_sample_id=self.archive_native_sample_id,
            paper_native_sample_label=self.sample_id if has_supplement else "",
            supplementary_table_sample_label=self.sample_id if has_supplement else "",
            preferred_sample_label=(
                self.sample_id if has_supplement else self.archive_native_sample_id
            ),
            sample_basis=(
                "supplementary_table_sample_without_archive_join"
                if supplement_only
                else (
                    "archive_supplement_primary_source_join"
                    if joined
                    else "archive_project_sample_accession_anchor"
                )
            ),
            sample_evidence_status=(
                "direct_table_extracted" if has_supplement else "archive_native"
            ),
            sample_lineage_path=source_path,
            sample_lineage_locator=" || ".join(locator_parts),
            sample_lineage_excerpt=" | ".join(excerpt_parts)[:500],
            sample_identity_resolution=("provisional" if supplement_only else "final"),
            sample_ambiguity_note=(
                "Supplementary individual Men1 has no matching PRJEB31621 archive sample accession."
                if supplement_only
                else ""
            ),
            locality_text=self.locality_text,
            political_entity=self.political_entity,
            latitude_text="",
            longitude_text="",
            chronology_text=chronology_text,
            chronology_dating_basis=chronology_basis,
            chronology_evidence_class=chronology_class,
            chronology_precision_posture=chronology_precision,
            source_native_tax_id=self.source_native_tax_id,
            source_native_scientific_name=self.source_native_scientific_name,
            taxon_alignment_status=(
                "not_reported"
                if not self.source_native_scientific_name
                else (
                    "project_species_match"
                    if self.source_native_scientific_name.casefold()
                    == species.latin_name.casefold()
                    else "project_species_mismatch"
                )
            ),
            archive_native_experiment_id="",
            source_native_identity_kind=(
                "supplementary_sample_label"
                if supplement_only
                else "biological_sample_accession"
            ),
        )


def _build_fertile_crescent_cattle_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    archive_source_path: str,
    archive_text: str,
    supplement_source_path: str,
    supplement_sha256: str,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Build the 78-row union of archive and primary-supplement identities."""
    if project.project_accession != FERTILE_CRESCENT_CATTLE_PROJECT_ACCESSION:
        raise ValueError("fertile-crescent cattle adapter requires PRJEB31621")
    return tuple(
        row.to_sample_master_row(
            species=species,
            project=project,
            archive_source_path=archive_source_path,
            supplement_source_path=supplement_source_path,
        )
        for row in _reconcile_fertile_crescent_cattle_panel(
            archive_text=archive_text,
            supplement_sha256=supplement_sha256,
        )
    )


def _reconcile_fertile_crescent_cattle_panel(
    *,
    archive_text: str,
    supplement_sha256: str,
    supplement_text: str | None = None,
) -> tuple[FertileCrescentCattleReconciliationRow, ...]:
    """Reconcile the hash-bound sources with explicit, non-heuristic aliases."""
    if sha256(archive_text.encode()).hexdigest() != ARCHIVE_TEXT_SHA256:
        raise ValueError("PRJEB31621 decompressed archive sha256 drift")
    if supplement_sha256 != FERTILE_CRESCENT_CATTLE_SUPPLEMENT_SHA256:
        raise ValueError("PRJEB31621 supplement sha256 drift")
    archive = parse_archive(archive_text)
    ancient_ids = validate_supplement(supplement_text)
    sites = site_by_sample()
    rows: list[FertileCrescentCattleReconciliationRow] = []
    claimed_archive_ids: set[str] = set()
    for sample_id in ancient_ids:
        site = sites[sample_id]
        exact_matches = tuple(
            sample
            for sample in archive.values()
            if any(
                re.match(rf"^{re.escape(sample_id)}(?:_|-|\.|$)", basename)
                for basename in sample.submitted_basenames
            )
        )
        status = "archive_supplement_literal_join"
        if not exact_matches and sample_id in EXPLICIT_ARCHIVE_ALIASES:
            expected_accession, prefixes = EXPLICIT_ARCHIVE_ALIASES[sample_id]
            candidate = archive.get(expected_accession)
            alias_matches = tuple(
                sample
                for sample in archive.values()
                if any(
                    basename.startswith(prefixes)
                    for basename in sample.submitted_basenames
                )
            )
            if candidate is None or alias_matches != (candidate,):
                raise ValueError(f"explicit archive alias drift for {sample_id}")
            exact_matches = (candidate,)
            status = "archive_supplement_explicit_alias_join"
        if not exact_matches:
            if sample_id != "Men1":
                raise ValueError(f"ancient sample lost its archive join: {sample_id}")
            rows.append(_supplement_only_row(sample_id, site))
            continue
        if len(exact_matches) != 1:
            raise ValueError(f"ancient sample has multiple archive joins: {sample_id}")
        archive_sample = exact_matches[0]
        if archive_sample.accession in claimed_archive_ids:
            raise ValueError("one archive sample joined multiple ancient individuals")
        claimed_archive_ids.add(archive_sample.accession)
        rows.append(_ancient_row(sample_id, site, archive_sample, status))

    archive_only_ids = set(archive) - claimed_archive_ids
    if archive_only_ids != set(ARCHIVE_ONLY_IDENTITIES):
        raise ValueError("archive-only PRJEB31621 identity set drift")
    rows.extend(
        _archive_only_row(archive[accession]) for accession in sorted(archive_only_ids)
    )
    rows.sort(
        key=lambda row: (
            not bool(row.archive_native_sample_id),
            row.archive_native_sample_id,
            row.sample_id,
        )
    )
    _validate_reconciliation(rows)
    return tuple(rows)


def _ancient_row(
    sample_id: str,
    site: CattleSiteEvidence,
    archive: ArchiveSample,
    status: str,
) -> FertileCrescentCattleReconciliationRow:
    approximate_bp = APPROXIMATE_BP_BY_SAMPLE.get(sample_id)
    source_interval = SOURCE_INTERVAL_BY_SAMPLE.get(sample_id, "")
    chronology_locator = (
        f"Table S2 (PDF pages 58-60), Test ID {sample_id}, Approximate Date BP"
        if approximate_bp is not None
        else site.locator
    )
    coordinate_text = DARIALI_SOURCE_COORDINATE if sample_id.startswith("Kaz") else ""
    return FertileCrescentCattleReconciliationRow(
        sample_id=sample_id,
        archive_native_sample_id=archive.accession,
        archive_native_experiment_ids=archive.experiment_ids,
        archive_submitted_basenames=archive.submitted_basenames,
        source_native_tax_id=archive.tax_id,
        source_native_scientific_name=archive.scientific_name,
        reconciliation_status=status,
        locality_text=site.locality_text,
        political_entity=site.political_entity,
        site_source_locator=site.locator,
        approximate_bp=approximate_bp,
        source_chronology_text=(
            f"Approximate Date BP: {approximate_bp}"
            if approximate_bp is not None
            else source_interval
        ),
        chronology_source_locator=chronology_locator,
        chronology_conflict_note=CHRONOLOGY_CONFLICT_BY_SAMPLE.get(sample_id, ""),
        source_coordinate_text=coordinate_text,
        coordinate_admission_status=(
            "withheld_utm_datum_unspecified" if coordinate_text else "unavailable"
        ),
    )


def _supplement_only_row(
    sample_id: str,
    site: CattleSiteEvidence,
) -> FertileCrescentCattleReconciliationRow:
    approximate_bp = APPROXIMATE_BP_BY_SAMPLE[sample_id]
    return FertileCrescentCattleReconciliationRow(
        sample_id=sample_id,
        archive_native_sample_id="",
        archive_native_experiment_ids=(),
        archive_submitted_basenames=(),
        source_native_tax_id="",
        source_native_scientific_name="",
        reconciliation_status="supplement_only",
        locality_text=site.locality_text,
        political_entity=site.political_entity,
        site_source_locator=site.locator,
        approximate_bp=approximate_bp,
        source_chronology_text=f"Approximate Date BP: {approximate_bp}",
        chronology_source_locator=(
            f"Table S2 (PDF pages 58-60), Test ID {sample_id}, Approximate Date BP"
        ),
        chronology_conflict_note="",
        source_coordinate_text="",
        coordinate_admission_status="unavailable",
    )


def _archive_only_row(
    archive: ArchiveSample,
) -> FertileCrescentCattleReconciliationRow:
    expected_tax_id, expected_name, expected_prefix = ARCHIVE_ONLY_IDENTITIES[
        archive.accession
    ]
    if (archive.tax_id, archive.scientific_name) != (expected_tax_id, expected_name):
        raise ValueError(f"archive-only taxonomy drift for {archive.accession}")
    if not any(
        basename.startswith(expected_prefix) for basename in archive.submitted_basenames
    ):
        raise ValueError(
            f"archive-only filename evidence drift for {archive.accession}"
        )
    return FertileCrescentCattleReconciliationRow(
        sample_id="",
        archive_native_sample_id=archive.accession,
        archive_native_experiment_ids=archive.experiment_ids,
        archive_submitted_basenames=archive.submitted_basenames,
        source_native_tax_id=archive.tax_id,
        source_native_scientific_name=archive.scientific_name,
        reconciliation_status="archive_only",
        locality_text="",
        political_entity="",
        site_source_locator="",
        approximate_bp=None,
        source_chronology_text="",
        chronology_source_locator="",
        chronology_conflict_note="",
        source_coordinate_text="",
        coordinate_admission_status="unavailable",
    )


def _validate_reconciliation(
    rows: list[FertileCrescentCattleReconciliationRow],
) -> None:
    statuses: dict[str, int] = {}
    for row in rows:
        statuses[row.reconciliation_status] = (
            statuses.get(row.reconciliation_status, 0) + 1
        )
    if statuses != {
        "archive_supplement_literal_join": 60,
        "archive_supplement_explicit_alias_join": 5,
        "archive_only": 12,
        "supplement_only": 1,
    }:
        raise ValueError("PRJEB31621 reconciliation denominator drift")
    ancient = tuple(row for row in rows if row.sample_id)
    if len(ancient) != 66 or len({row.locality_text for row in ancient}) != 40:
        raise ValueError("PRJEB31621 ancient site denominator drift")
    if sum(row.approximate_bp is not None for row in ancient) != 58:
        raise ValueError("PRJEB31621 approximate-BP denominator drift")
    if sum(row.source_coordinate_text != "" for row in rows) != 5:
        raise ValueError("PRJEB31621 source-coordinate denominator drift")
    if any(
        row.coordinate_admission_status
        not in {"unavailable", "withheld_utm_datum_unspecified"}
        for row in rows
    ):
        raise ValueError("PRJEB31621 coordinate admission posture drift")
    joined_taxa: dict[tuple[str, str], int] = {}
    for row in ancient:
        if not row.archive_native_sample_id:
            continue
        key = (row.source_native_tax_id, row.source_native_scientific_name)
        joined_taxa[key] = joined_taxa.get(key, 0) + 1
    if joined_taxa != {
        ("9913", "Bos taurus"): 60,
        ("9909", "Bos primigenius"): 5,
    }:
        raise ValueError("PRJEB31621 joined ancient taxonomy denominator drift")


__all__ = [
    "FERTILE_CRESCENT_CATTLE_PROJECT_ACCESSION",
    "FERTILE_CRESCENT_CATTLE_SUPPLEMENT_SHA256",
    "FertileCrescentCattleReconciliationRow",
    "_build_fertile_crescent_cattle_rows",
    "_reconcile_fertile_crescent_cattle_panel",
]
