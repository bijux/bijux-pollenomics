"""SEAD source collectors, normalization rules, and review helpers."""

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAcquisitionAdmission,
    SeadAdmissionExpectedIdentity,
    SeadMaterializedAdmissionSnapshot,
    materialize_sead_acquisition_admission,
    materialize_sead_full_evidence_admission,
    read_materialized_sead_full_evidence_admission,
    validate_materialized_sead_full_evidence_admission,
    validate_sead_acquisition_admission,
    validate_sead_full_evidence_admission,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    write_sead_site_archive,
)
from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    SEAD_FILTER_BATCH_SIZE,
    SEAD_LIMIT,
    SEAD_POSTGREST_ROOT,
    build_sead_in_filter,
    fetch_sead_rows,
    fetch_sead_rows_by_ids,
)
from bijux_pollenomics.collection.sources.sead.acquisition.fetch import (
    merge_sead_intervals,
    parse_optional_int,
    populate_sead_site_inventory_fields,
    sead_dating_interval,
)
from bijux_pollenomics.collection.sources.sead.catalog.inventory import (
    SeadSiteFetchResult,
    build_sead_site_inventory,
)
from bijux_pollenomics.collection.sources.sead.evidence.bundle import (
    build_sead_source_native_evidence_bundle,
    validate_sead_source_native_evidence_materialization,
    write_sead_source_native_evidence_bundle,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization import (
    normalize_sead_rows,
)

__all__ = [
    "SEAD_FILTER_BATCH_SIZE",
    "SEAD_LIMIT",
    "SEAD_POSTGREST_ROOT",
    "SeadAcquisitionAdmission",
    "SeadAdmissionExpectedIdentity",
    "SeadMaterializedAdmissionSnapshot",
    "SeadSiteFetchResult",
    "build_sead_in_filter",
    "build_sead_site_inventory",
    "build_sead_source_native_evidence_bundle",
    "fetch_sead_rows",
    "fetch_sead_rows_by_ids",
    "materialize_sead_acquisition_admission",
    "materialize_sead_full_evidence_admission",
    "merge_sead_intervals",
    "normalize_sead_rows",
    "parse_optional_int",
    "populate_sead_site_inventory_fields",
    "read_materialized_sead_full_evidence_admission",
    "sead_dating_interval",
    "validate_materialized_sead_full_evidence_admission",
    "validate_sead_acquisition_admission",
    "validate_sead_full_evidence_admission",
    "validate_sead_source_native_evidence_materialization",
    "write_sead_site_archive",
    "write_sead_source_native_evidence_bundle",
]
