"""Country-coverage vocabularies, paths, and validation errors."""

from __future__ import annotations

import re
from typing import Final
from bijux_pollenomics.collection.sources.sead.evidence.reader import (
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)
from bijux_pollenomics.collection.spatial import CountryAttributionDecision


COUNTRIES: Final = ("SE", "DK", "NO", "FI", "UNASSIGNED", "OUTSIDE")


COUNTRY_DIMENSIONS: Final = (
    "source_reported",
    "governed_assignment",
    "publication",
)


SOURCE_FAMILIES: Final = (
    "landclim",
    "neotoma",
    "sead",
    "raa",
    "boundaries",
    "svar",
    "aadr",
    "animal_adna",
)


PRODUCER_VERSION: Final = "1"


LEDGER_SCHEMA_VERSION: Final = "country-dimension-coverage-ledger.v1"


CELL_SCHEMA_ID: Final = "https://bijux.io/schemas/pollenomics/country-coverage.v2.json"


CELL_SCHEMA_SHA256: Final = (
    "9e1763379825d3868c743d19e54ec0cac8d8b15cc5e9d335872f4f346e7259bf"
)


BOUNDARY_METHOD: Final = "natural-earth-5.1.1-strict-containment-with-review.v1"


PUBLICATION_METHOD: Final = "product-country-publication-partition.v1"


BOUNDARY_ARTIFACT_PATH: Final = (
    "data/boundaries/normalized/nordic_country_boundaries.geojson"
)


SEAD_ACQUISITION_ROOT: Final = (
    f"data/sead/raw/acquisitions/{SEAD_GOVERNED_EVIDENCE_RUN_ID}"
)


SEAD_ADMISSION_PATH: Final = f"{SEAD_ACQUISITION_ROOT}/admission.json"


SEAD_DECISIONS_PATH: Final = f"{SEAD_ACQUISITION_ROOT}/country-decisions.json"


SEAD_SITES_PATH: Final = f"{SEAD_ACQUISITION_ROOT}/payloads/tbl_sites.json"


SEAD_EVIDENCE_MANIFEST_PATH: Final = (
    "data/sead/normalized/acquisitions/"
    f"{SEAD_GOVERNED_EVIDENCE_RUN_ID}/evidence_materialization_manifest.json"
)


SEAD_PUBLIC_SITES_PATH: Final = (
    "data/sead/normalized/nordic_environmental_sites.geojson"
)


COUNTRY_COVERAGE_OUTPUT_PATH: Final = "data/country_dimension_coverage.json"


COUNTRY_COVERAGE_ARTIFACT_ROOT: Final = "artifacts/execution-control/country-coverage"


COUNT_FIELDS: Final = (
    "requested_records",
    "received_records",
    "deduplicated_records",
    "failed_records",
    "accepted_records",
    "excluded_records",
    "unresolved_records",
    "published_records",
    "sites",
    "datasets",
    "collection_units",
    "samples",
    "dated_samples",
    "age_claims",
    "observations",
    "distinct_taxa",
    "mapped_taxa",
    "ambiguous_taxa",
    "unmapped_taxa",
    "events",
    "evaluated_pairs",
    "definite_candidates",
    "possible_candidates",
    "indeterminate_order_pairs",
    "unresolved_pairs",
    "excluded_pairs",
    "refused_pre_candidate_pairs",
)


INPUT_PATHS: Final = (
    "data/source_family_evidence_stage_matrix.json",
    "data/collection_summary.json",
    "data/boundaries/raw/source_manifest.json",
    "data/landclim/normalized/nordic_pollen_site_sequences.geojson",
    "data/neotoma/relational/reconciliation.json",
    SEAD_ADMISSION_PATH,
    SEAD_DECISIONS_PATH,
    SEAD_SITES_PATH,
    "docs/report/regions/nordic/nordic_pollen_site_sequences.geojson",
    "docs/report/regions/nordic/nordic_pollen_sites.geojson",
    "docs/report/countries/sweden/sweden_aadr_v66_summary.json",
    "docs/report/countries/denmark/denmark_aadr_v66_summary.json",
    "docs/report/countries/norway/norway_aadr_v66_summary.json",
    "docs/report/countries/finland/finland_aadr_v66_summary.json",
    "docs/report/animal_country_species_coverage.json",
    BOUNDARY_ARTIFACT_PATH,
    SEAD_EVIDENCE_MANIFEST_PATH,
    SEAD_PUBLIC_SITES_PATH,
)


_NAME_TO_CODE: Final = {
    "Sweden": "SE",
    "Denmark": "DK",
    "Norway": "NO",
    "Finland": "FI",
    "SE": "SE",
    "SWE": "SE",
    "SWE (Sweden)": "SE",
    "DK": "DK",
    "DK (Denmark)": "DK",
    "NO": "NO",
    "NOR": "NO",
    "NOR (Norway)": "NO",
    "FI": "FI",
    "FIN": "FI",
    "FIN (Finland)": "FI",
    "UNASSIGNED": "UNASSIGNED",
    "OUTSIDE": "OUTSIDE",
}


_RAW_SHA256_PATTERN: Final = re.compile(r"[0-9a-f]{64}\Z")


_SHA256_ID_PATTERN: Final = re.compile(r"sha256:[0-9a-f]{64}\Z")


_UUID_PATTERN: Final = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z"
)


_NORDIC_COUNTRY_CODES: Final = ("SE", "DK", "NO", "FI")


_CODE_TO_NAME: Final = {
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
}


_STAGE_STATUS_VALUES: Final = {"present", "missing", "refused"}


_AUTHORITY_STATUS_VALUES: Final = {
    "not_required",
    "refused",
    "review_required",
}


_COUNTRY_DECISION_CACHE: dict[
    tuple[str, str, float, float], CountryAttributionDecision
] = {}


class CountryCoverageError(ValueError):
    """Raised when governed coverage evidence cannot be reconciled."""
