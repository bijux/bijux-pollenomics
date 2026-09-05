from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.workflow.paths import adna_species_root

from bijux_pollenomics.adna.projects.registry.context import resolve_project_context
from bijux_pollenomics.adna.sources.ena import build_archive_project_catalog
from bijux_pollenomics.adna.species.tracked_species import TRACKED_ADNA_SPECIES
from .contracts import CoverageDashboard, CoverageRow, ShippedProductAudit
from .repository import (
    _atlas_locality_count,
    _count_sample_rows_by_mapping_posture,
    _country_output_count,
    _load_sample_rows,
)


def build_cross_species_coverage_dashboard(
    data_root: Path,
    report_root: Path,
) -> CoverageDashboard:
    """Report which animal evidence surfaces are actually shipped per species."""
    rows = [
        _build_species_coverage_row(
            data_root=Path(data_root),
            report_root=Path(report_root),
            species_name=species_name,
        )
        for species_name in TRACKED_ADNA_SPECIES
    ]
    return {
        "schema_version": "adna-cross-species-coverage-dashboard.v2",
        "rows": rows,
    }


def build_shipped_adna_product_audit(
    data_root: Path,
    report_root: Path,
) -> ShippedProductAudit:
    """Build a fuller product audit for what animal aDNA the repo really ships."""
    dashboard = build_cross_species_coverage_dashboard(data_root, report_root)
    rows = dashboard["rows"]
    return {
        "schema_version": "adna-shipped-product-audit.v2",
        "tracked_species_count": len(rows),
        "species_with_source_snapshots": sum(
            1 for row in rows if row["raw_source_snapshot_present"]
        ),
        "species_with_coordinate_provenance": sum(
            1 for row in rows if row["coordinate_provenance_present"]
        ),
        "species_with_locality_artifacts": sum(
            1 for row in rows if row["normalized_locality_artifact_present"]
        ),
        "species_with_country_outputs": sum(
            1 for row in rows if row["country_output_count"] > 0
        ),
        "species_with_atlas_localities": sum(
            1 for row in rows if row["atlas_locality_count"] > 0
        ),
        "rows": rows,
        "missing_public_outputs": [
            row["species_latin_name"]
            for row in rows
            if row["country_output_count"] == 0 and row["atlas_locality_count"] == 0
        ],
    }


def _build_species_coverage_row(
    *,
    data_root: Path,
    report_root: Path,
    species_name: str,
) -> CoverageRow:
    from bijux_pollenomics.adna.species.definitions import resolve_species_definition

    species = resolve_species_definition(species_name)
    species_root = adna_species_root(data_root, species_name)
    context_rows = [
        resolve_project_context(project)
        for project in build_archive_project_catalog()
        if project.species_latin_name == species.latin_name
    ]
    country_output_count = _country_output_count(
        report_root,
        species.latin_name,
        species.common_name,
    )
    atlas_locality_count = _atlas_locality_count(
        report_root / "world",
        species.latin_name,
        species.common_name,
    )
    return {
        "species_latin_name": species.latin_name,
        "species_common_name": species.common_name,
        "raw_inventory_present": (
            species_root / "raw" / "archive_inventory.csv"
        ).is_file(),
        "raw_source_snapshot_present": (
            species_root / "raw" / "source_snapshot.json"
        ).is_file(),
        "citation_manifest_present": (
            species_root / "manifests" / "citation_manifest.csv"
        ).is_file(),
        "normalized_project_summary_present": (
            species_root / "normalized" / "project_summaries.csv"
        ).is_file(),
        "coordinate_provenance_present": (
            species_root / "normalized" / "coordinate_provenance.csv"
        ).is_file(),
        "normalized_locality_artifact_present": (
            species_root / "normalized" / "locality_summaries.csv"
        ).is_file(),
        "review_markdown_present": (
            species_root / "review" / "species_review.md"
        ).is_file(),
        "review_json_present": (
            species_root / "review" / "species_review.json"
        ).is_file(),
        "country_output_count": country_output_count,
        "atlas_locality_count": atlas_locality_count,
        "mappable_coordinate_count": _count_sample_rows_by_mapping_posture(
            species_root,
            "mappable_point",
        ),
        "region_refused_coordinate_count": _count_sample_rows_by_mapping_posture(
            species_root,
            "refused_region_only",
        ),
        "unresolved_sample_count": sum(
            1
            for sample in _load_sample_rows(species_root)
            if str(sample.get("inclusion_status", "")) == "sample_context_blocked"
        ),
        "nordic_unmapped_lead_count": sum(
            1
            for row in context_rows
            if row.nordic_relevance == "nordic_relevant_unmapped"
        ),
    }
