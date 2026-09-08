"""Representative chronology rows for audit tests."""

from __future__ import annotations

from types import SimpleNamespace

from bijux_pollenomics.adna.projects.evidence.chronology.models import (
    AdnaProjectSampleChronologyRow,
)


def project_catalog() -> tuple[SimpleNamespace, ...]:
    return (
        SimpleNamespace(project_accession="P2", species_latin_name="Species beta"),
        SimpleNamespace(project_accession="P1", species_latin_name="Species alpha"),
    )


def rows_for_project(accession: str) -> tuple[AdnaProjectSampleChronologyRow, ...]:
    if accession == "P1":
        return (_row(accession, precise=True),)
    if accession == "P2":
        return (_row(accession, precise=False),)
    return ()


def _row(accession: str, *, precise: bool) -> AdnaProjectSampleChronologyRow:
    return AdnaProjectSampleChronologyRow(
        species_latin_name="Species alpha" if precise else "Species beta",
        species_common_name="alpha" if precise else "beta",
        project_accession=accession,
        repo_stable_sample_id=f"sample:{accession}",
        preferred_sample_label=f"Sample {accession}",
        sample_basis="source_row",
        sample_evidence_status="recovered",
        sample_identity_resolution="exact",
        sample_ambiguity_note="",
        chronology_text="1200-1500 BP" if precise else "date unavailable",
        chronology_strength="sample_owned_interval" if precise else "unresolved",
        chronology_evidence_class=(
            "direct_radiocarbon_date" if precise else "unresolved"
        ),
        chronology_precision_posture="sample_precise_interval"
        if precise
        else "unresolved",
        chronology_provenance_path=f"source/{accession}.json",
        chronology_provenance_kind="source_row",
        chronology_provenance_locator="row:1",
        chronology_provenance_text="1200-1500 BP" if precise else "",
        chronology_normalization_status="normalized_interval"
        if precise
        else "unresolved",
        time_start_bp=1200 if precise else None,
        time_end_bp=1500 if precise else None,
        time_mean_bp=1350 if precise else None,
        dating_basis="radiocarbon" if precise else "unresolved",
        chronology_conflict_note="site context differs" if precise else "",
        review_note="review conflict" if precise else "date evidence missing",
    )
