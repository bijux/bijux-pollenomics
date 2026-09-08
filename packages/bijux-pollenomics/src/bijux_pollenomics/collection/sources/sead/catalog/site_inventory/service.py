"""Coordinate source loading, indexing, and SEAD site enrichment."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from .bibliography_projection import project_site_bibliography
from .chronology_projection import project_site_chronology
from .site_projection import apply_site_inventory_projection
from .source_data.lookups import build_lookup_index
from .source_data.relations import build_relation_index
from .source_data.source_tables import load_inventory_source_rows
from .source_data.table_readers import (
    ApiSeadTableReader,
    MappingSeadTableReader,
    SeadTableReader,
)
from .values import parse_optional_int

_REQUIRED_ACQUISITION_TABLES = frozenset(
    {
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
    }
)


def build_sead_site_rows_from_acquisition_tables(
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
) -> tuple[list[dict[str, object]], dict[str, int | str]]:
    """Rebuild linked site rows solely from one admitted acquisition snapshot."""
    if set(rows_by_table) != _REQUIRED_ACQUISITION_TABLES:
        raise ValueError("SEAD chronology materialization requires the exact table set")
    sites = [dict(row) for row in rows_by_table["tbl_sites"]]
    summary = populate_sead_site_inventory_from_reader(
        sites,
        reader=MappingSeadTableReader(rows_by_table),
    )
    return sites, summary


def populate_sead_site_inventory_fields(
    rows: list[dict[str, object]],
    *,
    fetch_json_fn: Callable[..., object],
) -> dict[str, int | str]:
    return populate_sead_site_inventory_from_reader(
        rows, reader=ApiSeadTableReader(fetch_json_fn)
    )


def populate_sead_site_inventory_from_reader(
    rows: list[dict[str, object]], *, reader: SeadTableReader
) -> dict[str, int | str]:
    site_ids = [
        site_id
        for row in rows
        if (site_id := parse_optional_int(row.get("site_id"))) is not None
    ]
    source = load_inventory_source_rows(site_ids, reader=reader)
    relations = build_relation_index(source)
    lookups = build_lookup_index(source)
    chronology = project_site_chronology(source, relations, lookups)
    bibliography = project_site_bibliography(
        source,
        relations,
        lookups,
        chronology,
    )
    coverage = apply_site_inventory_projection(
        rows,
        relations=relations,
        lookups=lookups,
        chronology=chronology,
        bibliography=bibliography,
    )
    return {
        "site_row_count": len(rows),
        "sample_group_row_count": len(source.sample_groups),
        "physical_sample_row_count": len(source.physical_samples),
        "analysis_entity_row_count": len(source.analysis_entities),
        "analysis_entity_age_row_count": len(source.analysis_entity_ages),
        "geochronology_row_count": len(source.geochronology_rows),
        "dendro_date_row_count": len(source.dendro_dates),
        "analysis_value_row_count": len(source.analysis_values),
        "dating_range_row_count": len(source.dating_ranges),
        "age_type_row_count": len(source.age_types),
        "relative_date_row_count": len(source.relative_dates),
        "relative_age_row_count": len(source.relative_ages),
        "dating_uncertainty_row_count": len(source.dating_uncertainties),
        "method_row_count": len(source.methods),
        "dataset_row_count": len(source.datasets),
        "site_reference_row_count": len(source.site_references),
        "sample_group_reference_row_count": len(source.sample_group_references),
        "relative_age_reference_row_count": len(source.relative_age_references),
        "bibliography_source_row_count": len(source.bibliography_rows),
        "bibliography_row_count": sum(
            len(site_rows)
            for site_rows in bibliography.bibliography_rows_by_site.values()
        ),
        "bibliography_site_count": len(bibliography.bibliography_rows_by_site),
        "dating_range_site_count": len(chronology.dating_range_rows_by_site),
        "relative_period_site_count": len(chronology.relative_period_rows_by_site),
        "analysis_entity_age_site_count": len(
            chronology.analysis_entity_age_rows_by_site
        ),
        "geochronology_site_count": len(chronology.geochronology_rows_by_site),
        "dendro_date_site_count": len(chronology.dendro_date_rows_by_site),
        "numeric_interval_row_count": len(coverage.numeric_interval_site_ids),
        "contextual_only_site_count": len(
            coverage.contextual_interval_site_ids - coverage.numeric_interval_site_ids
        ),
        "unresolved_site_count": len(rows)
        - len(
            coverage.numeric_interval_site_ids | coverage.contextual_interval_site_ids
        ),
        "site_inventory_only_row_count": len(rows)
        - len(
            coverage.numeric_interval_site_ids | coverage.contextual_interval_site_ids
        ),
        "temporal_capture_posture": "linked_chronology_captured",
    }


__all__ = [
    "build_sead_site_rows_from_acquisition_tables",
    "populate_sead_site_inventory_fields",
]
