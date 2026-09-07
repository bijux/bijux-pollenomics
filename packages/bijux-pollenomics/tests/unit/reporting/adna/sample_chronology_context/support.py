"""Minimal governed project-source fixtures for chronology-context tests."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

PROJECT = "PRJTEST1"
SPECIES = "Ovis aries"


def base_rows(
    sample_id: str = "prjtest1:sample1",
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    master: dict[str, object] = {
        "species_latin_name": SPECIES,
        "species_common_name": "sheep",
        "project_accession": PROJECT,
        "repo_stable_sample_id": sample_id,
        "preferred_sample_label": sample_id,
        "sample_basis": "source_sample",
        "sample_evidence_status": "direct_table_extracted",
        "sample_identity_resolution": "final",
        "sample_ambiguity_note": "",
        "sample_lineage_path": "papers/source.xlsx",
        "sample_lineage_locator": "Sheet1!A2",
        "sample_lineage_excerpt": "sample source row",
        "source_native_identity_kind": "biological_sample",
        "source_native_tax_id": "9940",
        "source_native_scientific_name": "Ovis aries",
        "latitude_text": "59.0",
        "longitude_text": "18.0",
    }
    chronology: dict[str, object] = {
        "species_latin_name": SPECIES,
        "species_common_name": "sheep",
        "project_accession": PROJECT,
        "repo_stable_sample_id": sample_id,
        "preferred_sample_label": sample_id,
        "sample_basis": "source_sample",
        "sample_evidence_status": "direct_table_extracted",
        "sample_identity_resolution": "final",
        "sample_ambiguity_note": "",
        "chronology_text": "1000-1200 BP",
        "chronology_strength": "sample_owned_interval",
        "chronology_evidence_class": "direct_radiocarbon_date",
        "chronology_precision_posture": "sample_precise_interval",
        "chronology_normalization_status": "normalized_interval",
        "time_start_bp": 1000,
        "time_end_bp": 1200,
        "time_mean_bp": 1100,
        "dating_basis": "radiocarbon",
        "chronology_provenance_path": "papers/source.xlsx",
        "chronology_provenance_kind": "supplementary_spreadsheet_row",
        "chronology_provenance_locator": "Sheet1!A2",
        "chronology_provenance_text": "1000-1200 BP",
    }
    site: dict[str, object] = {
        "species_latin_name": SPECIES,
        "species_common_name": "sheep",
        "project_accession": PROJECT,
        "repo_stable_sample_id": sample_id,
        "preferred_sample_label": sample_id,
        "sample_basis": "source_sample",
        "sample_evidence_status": "direct_table_extracted",
        "sample_identity_resolution": "final",
        "sample_ambiguity_note": "",
        "locality_text": "Test site",
        "locality_resolution_status": "direct_sample_site",
        "site_name": "Test site",
        "country_name": "Sweden",
        "broader_geography": "",
        "coordinate_basis": "supplementary_table_coordinates",
        "coordinate_mapping_posture": "mappable_point",
        "coordinate_confidence": "exact",
        "location_evidence_artifact_path": "papers/source.xlsx",
        "location_evidence_artifact_kind": "supplementary_spreadsheet_row",
        "location_evidence_locator": "Sheet1!A2",
        "location_evidence_text": "Test site, Sweden",
    }
    return master, chronology, site


def write_source_repository(
    data_root: Path,
    *,
    masters: list[dict[str, object]] | None = None,
    chronologies: list[dict[str, object]] | None = None,
    sites: list[dict[str, object]] | None = None,
    schema_overrides: dict[str, str] | None = None,
) -> None:
    master, chronology, site = base_rows()
    master_rows = deepcopy(masters if masters is not None else [master])
    chronology_rows = deepcopy(
        chronologies if chronologies is not None else [chronology]
    )
    site_rows = deepcopy(sites if sites is not None else [site])
    source_root = data_root / "adna" / "governance" / "source_library"
    project_root = source_root / "projects" / PROJECT
    project_root.mkdir(parents=True)
    _write(
        source_root / "project_registry.json",
        {
            "schema_version": "adna-source-library.v1",
            "rows": [
                {
                    "project_accession": PROJECT,
                    "species_latin_name": SPECIES,
                    "primary_paper_url": "https://doi.org/10.1000/test",
                    "project_url": "https://example.test/project",
                }
            ],
        },
    )
    schemas = {
        "sample_master.json": "animal-project-sample-master.v1",
        "sample_chronology.json": "animal-project-sample-chronology.v1",
        "sample_sites.json": "animal-project-sample-sites.v1",
        **(schema_overrides or {}),
    }
    biological_count = sum(
        row.get("source_native_identity_kind") != "sequencing_experiment_accession"
        for row in master_rows
    )
    _write(
        project_root / "sample_master.json",
        {
            "schema_version": schemas["sample_master.json"],
            "project_accession": PROJECT,
            "species_latin_name": SPECIES,
            "recovered_sample_count": biological_count,
            "final_sample_count": sum(
                row.get("sample_identity_resolution") == "final" for row in master_rows
            ),
            "ambiguity_row_count": sum(
                row.get("sample_identity_resolution") == "ambiguous"
                for row in master_rows
            ),
            "rows": master_rows,
        },
    )
    for filename, rows in (
        ("sample_chronology.json", chronology_rows),
        ("sample_sites.json", site_rows),
    ):
        _write(
            project_root / filename,
            {
                "schema_version": schemas[filename],
                "project_accession": PROJECT,
                "species_latin_name": SPECIES,
                "row_count": len(rows),
                "rows": rows,
            },
        )


def _write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
