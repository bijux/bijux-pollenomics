"""Taxonomic hierarchy and ecological-code join plans."""

from __future__ import annotations

from ...models import SeadJoinPlan

_JoinDefinition = tuple[str, str, str, str, str, str, bool]

_TAXONOMY_JOIN_DEFINITIONS: tuple[_JoinDefinition, ...] = (
    (
        "taxa.abundances",
        "tbl_taxa_tree_master",
        "tbl_abundances",
        "taxon_id",
        "abundance_id",
        "taxon_id",
        False,
    ),
    (
        "taxa.analysis_taxon_counts",
        "tbl_taxa_tree_master",
        "tbl_analysis_taxon_counts",
        "taxon_id",
        "analysis_taxon_count_id",
        "taxon_id",
        False,
    ),
    (
        "taxon_authors.taxa",
        "tbl_taxa_tree_authors",
        "tbl_taxa_tree_master",
        "author_id",
        "taxon_id",
        "author_id",
        False,
    ),
    (
        "taxon_genera.taxa",
        "tbl_taxa_tree_genera",
        "tbl_taxa_tree_master",
        "genus_id",
        "taxon_id",
        "genus_id",
        False,
    ),
    (
        "taxon_families.genera",
        "tbl_taxa_tree_families",
        "tbl_taxa_tree_genera",
        "family_id",
        "genus_id",
        "family_id",
        False,
    ),
    (
        "taxon_orders.families",
        "tbl_taxa_tree_orders",
        "tbl_taxa_tree_families",
        "order_id",
        "family_id",
        "order_id",
        False,
    ),
    (
        "record_types.taxon_orders",
        "tbl_record_types",
        "tbl_taxa_tree_orders",
        "record_type_id",
        "order_id",
        "record_type_id",
        False,
    ),
    (
        "record_types.abundance_elements",
        "tbl_record_types",
        "tbl_abundance_elements",
        "record_type_id",
        "abundance_element_id",
        "record_type_id",
        False,
    ),
    (
        "taxa.ecocodes",
        "tbl_taxa_tree_master",
        "tbl_ecocodes",
        "taxon_id",
        "ecocode_id",
        "taxon_id",
        True,
    ),
    (
        "ecocode_definitions.ecocodes",
        "tbl_ecocode_definitions",
        "tbl_ecocodes",
        "ecocode_definition_id",
        "ecocode_id",
        "ecocode_definition_id",
        False,
    ),
    (
        "ecocode_groups.definitions",
        "tbl_ecocode_groups",
        "tbl_ecocode_definitions",
        "ecocode_group_id",
        "ecocode_definition_id",
        "ecocode_group_id",
        False,
    ),
    (
        "ecocode_systems.groups",
        "tbl_ecocode_systems",
        "tbl_ecocode_groups",
        "ecocode_system_id",
        "ecocode_group_id",
        "ecocode_system_id",
        False,
    ),
)

_TAXONOMY_JOIN_PLANS = tuple(
    SeadJoinPlan(*definition) for definition in _TAXONOMY_JOIN_DEFINITIONS
)
