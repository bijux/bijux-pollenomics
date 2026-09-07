from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.governance.audit_catalogs import (
    build_coordinate_caveat_surface,
    build_cross_species_archive_inventory,
    build_cross_species_bibliography,
    build_cross_species_coverage_dashboard,
    build_cross_species_map_readiness,
    build_overbroad_site_ledger,
    build_shipped_adna_product_audit,
    build_species_freshness_table,
    build_unresolved_site_ledger,
    render_coordinate_caveat_surface_markdown,
    render_coordinate_confidence_scale_markdown,
)
from bijux_pollenomics.adna.projects.registry.sample_truth import (
    build_animal_sample_aggregation_warnings,
    build_animal_sample_foundation_truth,
    build_animal_sample_product_contract,
    render_animal_sample_aggregation_warnings_markdown,
    render_animal_sample_foundation_truth_markdown,
    render_animal_sample_product_contract_markdown,
)
from bijux_pollenomics.adna.workflow.paths import adna_governance_root
from bijux_pollenomics.core.files import write_json, write_text
from bijux_pollenomics.core.records import require_record_rows
from bijux_pollenomics.core.tabular import render_csv_rows


def _materialize_cross_species_adna_artifacts(
    output_root: Path, *, report_root: Path | None = None
) -> None:
    governance_root = adna_governance_root(output_root)
    governance_root.mkdir(parents=True, exist_ok=True)
    report_root = (
        output_root.parent / "docs" / "report"
        if report_root is None
        else Path(report_root)
    )
    bibliography_rows = build_cross_species_bibliography()
    archive_rows = build_cross_species_archive_inventory()
    freshness_rows = build_species_freshness_table()
    coverage_dashboard = build_cross_species_coverage_dashboard(
        output_root, report_root
    )
    product_audit = build_shipped_adna_product_audit(output_root, report_root)
    map_readiness = build_cross_species_map_readiness(output_root)
    sample_product_contract = build_animal_sample_product_contract()
    sample_foundation_truth = build_animal_sample_foundation_truth(output_root)
    sample_aggregation_warnings = build_animal_sample_aggregation_warnings(
        output_root,
        report_root,
    )
    unresolved_site_ledger = build_unresolved_site_ledger(output_root)
    overbroad_site_ledger = build_overbroad_site_ledger(output_root)
    coordinate_caveat_surface = build_coordinate_caveat_surface(output_root)
    write_json(
        governance_root / "cross_species_bibliography.json",
        {
            "schema_version": "adna-cross-species-bibliography.v1",
            "rows": bibliography_rows,
        },
    )
    write_text(
        governance_root / "cross_species_bibliography.csv",
        render_csv_rows(bibliography_rows),
    )
    write_json(
        governance_root / "cross_species_archive_inventory.json",
        {
            "schema_version": "adna-cross-species-archive-inventory.v1",
            "rows": archive_rows,
        },
    )
    write_text(
        governance_root / "cross_species_archive_inventory.csv",
        render_csv_rows(archive_rows),
    )
    write_json(
        governance_root / "cross_species_freshness.json", {"rows": freshness_rows}
    )
    write_text(
        governance_root / "cross_species_freshness.csv",
        render_csv_rows(freshness_rows),
    )
    write_json(
        governance_root / "cross_species_coverage_dashboard.json", coverage_dashboard
    )
    write_text(
        governance_root / "cross_species_coverage_dashboard.csv",
        render_csv_rows(require_record_rows(coverage_dashboard, "rows")),
    )
    write_json(
        governance_root / "animal_sample_product_contract.json", sample_product_contract
    )
    write_text(
        governance_root / "animal_sample_product_contract.md",
        render_animal_sample_product_contract_markdown(sample_product_contract),
    )
    write_json(
        governance_root / "animal_sample_foundation_truth.json", sample_foundation_truth
    )
    write_text(
        governance_root / "animal_sample_foundation_truth.md",
        render_animal_sample_foundation_truth_markdown(sample_foundation_truth),
    )
    write_text(
        governance_root / "animal_sample_foundation_truth_species.csv",
        render_csv_rows(require_record_rows(sample_foundation_truth, "species_rows")),
    )
    write_text(
        governance_root / "animal_sample_foundation_truth_projects.csv",
        render_csv_rows(require_record_rows(sample_foundation_truth, "project_rows")),
    )
    write_json(
        governance_root / "animal_sample_aggregation_warnings.json",
        sample_aggregation_warnings,
    )
    write_text(
        governance_root / "animal_sample_aggregation_warnings.md",
        render_animal_sample_aggregation_warnings_markdown(sample_aggregation_warnings),
    )
    write_json(governance_root / "shipped_product_audit.json", product_audit)
    write_json(governance_root / "cross_species_map_readiness.json", map_readiness)
    write_text(
        governance_root / "cross_species_map_readiness.csv",
        render_csv_rows(require_record_rows(map_readiness, "rows")),
    )
    write_json(
        governance_root / "unresolved_site_ledger.json",
        {
            "schema_version": "adna-unresolved-site-ledger.v1",
            "rows": unresolved_site_ledger,
        },
    )
    write_text(
        governance_root / "unresolved_site_ledger.csv",
        render_csv_rows(unresolved_site_ledger),
    )
    write_json(
        governance_root / "overbroad_site_ledger.json",
        {
            "schema_version": "adna-overbroad-site-ledger.v1",
            "rows": overbroad_site_ledger,
        },
    )
    write_text(
        governance_root / "overbroad_site_ledger.csv",
        render_csv_rows(overbroad_site_ledger),
    )
    write_json(
        governance_root / "coordinate_caveat_surface.json", coordinate_caveat_surface
    )
    write_text(
        governance_root / "coordinate_caveat_surface.md",
        render_coordinate_caveat_surface_markdown(coordinate_caveat_surface),
    )
    write_text(
        governance_root / "coordinate_confidence_scale.md",
        render_coordinate_confidence_scale_markdown(),
    )
