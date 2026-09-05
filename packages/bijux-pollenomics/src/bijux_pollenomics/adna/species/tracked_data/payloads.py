from __future__ import annotations

from pathlib import Path
from typing import Any

from bijux_pollenomics.adna.sources.ena import (
    AdnaArchiveProject,
    classify_archive_project_evidence,
)
from bijux_pollenomics.adna.sources.recovery import build_species_project_deficit_ledger
from bijux_pollenomics.adna.sources.snapshots import (
    build_species_source_snapshots,
    resolve_archive_source_snapshot,
)
from bijux_pollenomics.adna.workflow.normalization import AdnaSpeciesNormalizationBundle

from ..definitions import resolve_species_definition


def _archive_inventory_payload(
    archive_projects: tuple[AdnaArchiveProject, ...],
) -> dict[str, object]:
    projects = []
    for project in archive_projects:
        payload = project.as_dict()
        payload["evidence_strength"] = classify_archive_project_evidence(project)
        payload["source_snapshot"] = resolve_archive_source_snapshot(project).as_dict()
        projects.append(payload)
    return {"projects": projects}


def _source_snapshot_payload(species_name: str) -> dict[str, object]:
    snapshots = build_species_source_snapshots(species_name)
    return {
        "schema_version": "adna-species-source-snapshot.v1",
        "species_latin_name": resolve_species_definition(species_name).latin_name,
        "projects": [snapshot.as_dict() for snapshot in snapshots],
    }


def _support_summary_payload(
    *,
    species_manifest: dict[str, object],
    dataset_review: dict[str, object],
    curation_manifest: dict[str, object],
    project_manifest: dict[str, object],
    normalization_bundle: dict[str, object],
) -> dict[str, object]:
    return {
        "species_manifest": species_manifest,
        "dataset_review": dataset_review,
        "curation_manifest": curation_manifest,
        "project_manifest": project_manifest,
        "normalization_bundle": normalization_bundle,
    }


def _sample_records_payload(
    bundle: AdnaSpeciesNormalizationBundle,
) -> dict[str, object]:
    sample_refusals = [
        refusal.as_dict()
        for refusal in bundle.refusals
        if refusal.record_kind == "sample_record"
    ]
    return {
        "schema_version": "adna-sample-record-export.v1",
        "evidence_domain": "animal_ancient_dna",
        "pollen_eligible": False,
        "pollen_propagation_eligible": False,
        "species_latin_name": bundle.species.latin_name,
        "admitted_sample_count": len(bundle.sample_records),
        "refused_sample_count": len(sample_refusals),
        "samples": [record.as_dict() for record in bundle.sample_records],
        "sample_refusals": sample_refusals,
    }


def _project_summaries_payload(
    bundle: AdnaSpeciesNormalizationBundle,
) -> dict[str, object]:
    return {
        "schema_version": "adna-project-summary-export.v1",
        "species_latin_name": bundle.species.latin_name,
        "projects": [summary.as_dict() for summary in bundle.project_summaries],
    }


def _site_evidence_payload(bundle: AdnaSpeciesNormalizationBundle) -> dict[str, object]:
    return {
        "schema_version": "adna-site-evidence-export.v1",
        "species_latin_name": bundle.species.latin_name,
        "site_evidence": [record.as_dict() for record in bundle.site_evidence_records],
    }


def _coordinate_provenance_payload(
    bundle: AdnaSpeciesNormalizationBundle,
) -> dict[str, object]:
    return {
        "schema_version": "adna-coordinate-provenance-export.v1",
        "species_latin_name": bundle.species.latin_name,
        "coordinate_provenance": [
            record.as_dict() for record in bundle.coordinate_provenance_records
        ],
    }


def _locality_summaries_payload(
    bundle: AdnaSpeciesNormalizationBundle,
) -> dict[str, object]:
    return {
        "schema_version": "adna-locality-summary-export.v1",
        "species_latin_name": bundle.species.latin_name,
        "localities": [summary.as_dict() for summary in bundle.locality_records],
    }


def _species_project_recovery_deficits_payload(
    output_root: Path,
    species_name: str,
) -> dict[str, Any]:
    ledger = build_species_project_deficit_ledger(output_root)
    rows = [row for row in ledger["rows"] if row["species_latin_name"] == species_name]
    counts = ledger["species_counts"].get(
        species_name,
        {
            "project_count": 0,
            "projects_with_sample_gap": 0,
            "projects_with_site_gap": 0,
            "projects_with_chronology_gap": 0,
            "projects_blocked_before_publication": 0,
        },
    )
    return {
        "schema_version": "animal-species-project-recovery-deficits.v1",
        "species_latin_name": species_name,
        "counts": counts,
        "rows": rows,
    }
