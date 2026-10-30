"""Site, collection-unit, and dataset relational projection."""

from __future__ import annotations

from collections.abc import Mapping
import copy

from ..country import (
    NeotomaCountryAttribution,
    missing_country_attribution,
    with_source_country,
)
from ..diagnostics import add_orphan, register_record
from ..source_payloads import copy_source_payload_excluding
from ..state import RelationalBuildState
from .chronologies import project_chronologies
from .parent_refusals import (
    refuse_chronology_sibling,
    refuse_dataset_context,
    required_parent_id,
)
from .samples import project_samples


def project_download_row(
    state: RelationalBuildState,
    download_row: Mapping[str, object],
    *,
    country_attribution: Mapping[str, NeotomaCountryAttribution],
) -> None:
    state.source_counts["download_rows"] += 1
    site = download_row.get("site")
    if not isinstance(site, Mapping):
        add_orphan(
            state.orphans,
            "download_row",
            None,
            "missing_site",
            source_value=site,
            source_field_present="site" in download_row,
            excluded_source_row_counts={},
        )
        return
    state.source_counts["site_rows"] += 1
    site_source_id = required_parent_id(
        state,
        site,
        level="site",
        id_field="siteid",
        parent_id=None,
        own_counter="site_rows",
    )
    if site_source_id is None:
        return
    site_id = f"neotoma:site:{site_source_id}"
    attribution = country_attribution.get(site_source_id)
    if attribution is None:
        attribution = missing_country_attribution(site)
    else:
        attribution = with_source_country(attribution, site)
    country_code = attribution.final_country_code
    state.country_counts[country_code]["site_rows"] += 1
    register_record(
        state.tables["sites"],
        {
            "site_id": site_id,
            "source_site_id": site.get("siteid"),
            "raw_country": attribution.raw_country,
            "derived_country": attribution.derived_country,
            "country_code": country_code,
            "country_decision_status": attribution.decision_status,
            "country_decision_method": attribution.decision_method,
            "country_candidates": list(attribution.candidate_countries),
            "country_ambiguity_reason": attribution.ambiguity_reason,
            "country_refusal_reason": attribution.refusal_reason,
            "boundary_artifact_digest": attribution.boundary_artifact_digest,
            "boundary_version": attribution.boundary_version,
            "source_vs_derived_comparison": attribution.source_vs_derived_comparison,
            "country_propagation_eligible": attribution.propagation_eligible,
            "source_geopolitical": copy.deepcopy(site.get("geopolitical")),
            "source_payload": copy_source_payload_excluding(
                site, "collectionunit", "dataset"
            ),
            "source_snapshot_id": state.source_snapshot_id,
            "build_id": state.build_id,
        },
        id_field="site_id",
        conflicts=state.conflicts,
        conflict_kind="site_payload_conflict",
        occurrence_counts=state.registered_occurrences,
    )

    unit = site.get("collectionunit")
    if not isinstance(unit, Mapping):
        add_orphan(
            state.orphans,
            "site",
            site_id,
            "missing_collection_unit",
            source_value=unit,
            source_field_present="collectionunit" in site,
            excluded_source_row_counts={},
        )
        refuse_dataset_context(state, site, site_id)
        return
    state.source_counts["collection_unit_rows"] += 1
    unit_source_id = required_parent_id(
        state,
        unit,
        level="collection_unit",
        id_field="collectionunitid",
        parent_id=site_id,
        own_counter="collection_unit_rows",
    )
    if unit_source_id is None:
        refuse_dataset_context(state, site, site_id)
        return
    unit_id = f"neotoma:collection-unit:{unit_source_id}"
    state.country_counts[country_code]["collection_unit_rows"] += 1
    register_record(
        state.tables["collection_units"],
        {
            "collection_unit_id": unit_id,
            "source_collection_unit_id": unit.get("collectionunitid"),
            "site_id": site_id,
            "country_code": country_code,
            "source_payload": copy_source_payload_excluding(
                unit, "dataset", "chronologies", "defaultchronology"
            ),
            "source_snapshot_id": state.source_snapshot_id,
            "build_id": state.build_id,
        },
        id_field="collection_unit_id",
        conflicts=state.conflicts,
        conflict_kind="collection_unit_payload_conflict",
        occurrence_counts=state.registered_occurrences,
    )

    dataset = unit.get("dataset")
    if not isinstance(dataset, Mapping):
        add_orphan(
            state.orphans,
            "collection_unit",
            unit_id,
            "missing_dataset",
            source_value=dataset,
            source_field_present="dataset" in unit,
            excluded_source_row_counts={},
        )
        refuse_chronology_sibling(state, unit, unit_id)
        refuse_dataset_context(state, site, site_id)
        return
    state.source_counts["dataset_rows"] += 1
    dataset_source_id = required_parent_id(
        state,
        dataset,
        level="dataset",
        id_field="datasetid",
        parent_id=unit_id,
        own_counter="dataset_rows",
    )
    if dataset_source_id is None:
        refuse_chronology_sibling(state, unit, unit_id)
        refuse_dataset_context(state, site, site_id)
        return
    dataset_id = f"neotoma:dataset:{dataset_source_id}"
    state.country_counts[country_code]["dataset_rows"] += 1
    site_dataset = site.get("dataset")
    register_record(
        state.tables["datasets"],
        {
            "dataset_id": dataset_id,
            "source_dataset_id": dataset.get("datasetid"),
            "site_id": site_id,
            "collection_unit_id": unit_id,
            "country_code": country_code,
            "source_payload": copy_source_payload_excluding(dataset, "samples"),
            "source_site_dataset_payload": copy.deepcopy(site_dataset)
            if isinstance(site_dataset, Mapping)
            else None,
            "source_snapshot_id": state.source_snapshot_id,
            "build_id": state.build_id,
        },
        id_field="dataset_id",
        conflicts=state.conflicts,
        conflict_kind="dataset_payload_conflict",
        occurrence_counts=state.registered_occurrences,
    )

    default_source_id, chronology_ids_by_source = project_chronologies(
        state,
        unit=unit,
        unit_source_id=unit_source_id,
        unit_id=unit_id,
        dataset_id=dataset_id,
        site_id=site_id,
        country_code=country_code,
    )
    project_samples(
        state,
        dataset=dataset,
        dataset_id=dataset_id,
        unit_id=unit_id,
        site_id=site_id,
        country_code=country_code,
        default_source_id=default_source_id,
        chronology_ids_by_source=chronology_ids_by_source,
    )
