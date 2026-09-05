"""Animal evidence audit catalogs grouped by governed responsibility."""

from bijux_pollenomics.core.tabular import render_csv_rows

from .atlas_accountability import build_animal_atlas_candidate_accountability
from .coverage import (
    build_cross_species_coverage_dashboard,
    build_shipped_adna_product_audit,
)
from .map_readiness import build_cross_species_map_readiness
from .public_outputs import (
    build_public_animal_output_audit,
    build_public_animal_output_honesty,
)
from .rendering import (
    render_animal_atlas_candidate_accountability_markdown,
    render_coordinate_caveat_surface_markdown,
    render_coordinate_confidence_scale_markdown,
    render_public_animal_output_audit_markdown,
    render_public_animal_output_honesty_markdown,
)
from .site_posture import (
    build_coordinate_caveat_surface,
    build_overbroad_site_ledger,
    build_unresolved_site_ledger,
)
from .source_inventory import (
    build_cross_species_archive_inventory,
    build_cross_species_bibliography,
    build_species_freshness_table,
)

__all__ = [
    "build_animal_atlas_candidate_accountability",
    "build_coordinate_caveat_surface",
    "build_cross_species_archive_inventory",
    "build_cross_species_bibliography",
    "build_cross_species_coverage_dashboard",
    "build_cross_species_map_readiness",
    "build_overbroad_site_ledger",
    "build_public_animal_output_audit",
    "build_public_animal_output_honesty",
    "build_shipped_adna_product_audit",
    "build_species_freshness_table",
    "build_unresolved_site_ledger",
    "render_animal_atlas_candidate_accountability_markdown",
    "render_coordinate_caveat_surface_markdown",
    "render_coordinate_confidence_scale_markdown",
    "render_csv_rows",
    "render_public_animal_output_audit_markdown",
    "render_public_animal_output_honesty_markdown",
]
