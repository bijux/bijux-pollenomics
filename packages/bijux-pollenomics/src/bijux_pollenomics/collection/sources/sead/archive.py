from __future__ import annotations

from datetime import date
from pathlib import Path

from ....core.files import write_json

SEAD_LINKED_SOURCE_TABLES = (
    "tbl_sites",
    "tbl_sample_groups",
    "tbl_physical_samples",
    "tbl_analysis_entities",
    "tbl_analysis_entity_ages",
    "tbl_geochronology",
    "tbl_dendro_dates",
    "tbl_analysis_values",
    "tbl_analysis_dating_ranges",
    "tbl_age_types",
    "tbl_relative_dates",
    "tbl_relative_ages",
    "tbl_relative_age_refs",
    "tbl_dating_uncertainty",
    "tbl_methods",
    "tbl_datasets",
    "tbl_site_references",
    "tbl_sample_group_references",
    "tbl_biblio",
)

SEAD_FULL_EVIDENCE_SOURCE_TABLES = (
    "tbl_sites",
    "tbl_sample_groups",
    "tbl_physical_samples",
    "tbl_analysis_entities",
    "tbl_analysis_entity_ages",
    "tbl_geochronology",
    "tbl_dendro_dates",
    "tbl_analysis_values",
    "tbl_analysis_dating_ranges",
    "tbl_relative_dates",
    "tbl_age_types",
    "tbl_relative_ages",
    "tbl_relative_age_refs",
    "tbl_dating_uncertainty",
    "tbl_datasets",
    "tbl_site_references",
    "tbl_sample_group_references",
    "tbl_abundances",
    "tbl_analysis_taxon_counts",
    "tbl_analysis_numerical_values",
    "tbl_analysis_integer_values",
    "tbl_analysis_categorical_values",
    "tbl_analysis_boolean_values",
    "tbl_analysis_value_dimensions",
    "tbl_measured_values",
    "tbl_measured_value_dimensions",
    "tbl_analysis_entity_dimensions",
    "tbl_sample_dimensions",
    "tbl_sample_group_dimensions",
    "tbl_value_qualifiers",
    "tbl_abundance_ident_levels",
    "tbl_abundance_modifications",
    "tbl_abundance_properties",
    "tbl_abundance_elements",
    "tbl_identification_levels",
    "tbl_modification_types",
    "tbl_property_types",
    "tbl_taxa_tree_master",
    "tbl_taxa_tree_authors",
    "tbl_taxa_tree_genera",
    "tbl_taxa_tree_families",
    "tbl_taxa_tree_orders",
    "tbl_record_types",
    "tbl_ecocodes",
    "tbl_ecocode_definitions",
    "tbl_ecocode_groups",
    "tbl_ecocode_systems",
    "tbl_value_classes",
    "tbl_value_types",
    "tbl_value_type_items",
    "tbl_dimensions",
    "tbl_units",
    "tbl_data_types",
    "tbl_data_type_groups",
    "tbl_dataset_methods",
    "tbl_dataset_masters",
    "tbl_dataset_contacts",
    "tbl_contacts",
    "tbl_contact_types",
    "tbl_methods",
    "tbl_biblio",
)

__all__ = [
    "SEAD_FULL_EVIDENCE_SOURCE_TABLES",
    "SEAD_LINKED_SOURCE_TABLES",
    "write_sead_site_archive",
]


def write_sead_site_archive(
    raw_dir: Path,
    *,
    bbox: tuple[float, float, float, float],
    rows: list[dict[str, object]],
    inventory_summary: dict[str, int | str],
) -> Path:
    """Write the raw SEAD site inventory archive and return its path."""
    raw_path = Path(raw_dir) / "nordic_sites.json"
    write_json(
        raw_path,
        {
            "generated_on": str(date.today()),
            "source": "SEAD",
            "endpoint": "https://browser.sead.se/postgrest/tbl_sites",
            "row_count": len(rows),
            "bbox": list(bbox),
            "source_tables": list(SEAD_LINKED_SOURCE_TABLES),
            "inventory_summary": inventory_summary,
            "rows": rows,
        },
    )
    return raw_path
