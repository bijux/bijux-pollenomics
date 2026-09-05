"""Stable table and reconciliation vocabulary for Neotoma projection."""

from bijux_pollenomics.evidence.sources.neotoma.contract import (
    COUNTRY_CODES as COUNTRY_CODES,
    RELATIONAL_TABLE_SURFACES,
    SURFACE_ID_FIELDS,
)

TABLE_NAMES = RELATIONAL_TABLE_SURFACES
TABLE_ID_FIELDS = {
    table_name: SURFACE_ID_FIELDS[table_name] for table_name in TABLE_NAMES
}

COUNTRY_COUNT_FIELDS = (
    "site_rows",
    "sites",
    "collection_unit_rows",
    "collection_units",
    "dataset_rows",
    "datasets",
    "chronologies",
    "chronology_controls",
    "sample_rows",
    "samples",
    "age_claim_rows",
    "age_comparable",
    "age_context_only",
    "age_refused",
    "age_unresolved",
    "observation_rows",
    "variables",
    "assigned_sites",
    "review_sites",
    "unassigned_sites",
    "refused_sites",
    "propagation_eligible_sites",
)

COUNTRY_NAMES_TO_CODES = {
    "Denmark": "DK",
    "Finland": "FI",
    "Norway": "NO",
    "Sweden": "SE",
}
