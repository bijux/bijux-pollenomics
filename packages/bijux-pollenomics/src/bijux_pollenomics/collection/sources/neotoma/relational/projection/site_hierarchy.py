"""Site, collection-unit, and dataset relational projection."""

from __future__ import annotations

import copy
from collections.abc import Mapping

from ..country import (
    NeotomaCountryAttribution,
    missing_country_attribution,
    with_source_country,
)
from ..diagnostics import add_orphan, register_record, required_source_id
from ..source_payloads import copy_source_payload_excluding
from ..state import RelationalBuildState
from .chronologies import project_chronologies
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
        add_orphan(state.orphans, "download_row", None, "missing_site")
        return
    site_source_id = required_source_id(
        site.get("siteid"), "site", state.orphans, parent_id=None
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
    state.source_counts["site_rows"] += 1
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
    )

    unit = site.get("collectionunit")
    if not isinstance(unit, Mapping):
        add_orphan(state.orphans, "site", site_id, "missing_collection_unit")
        return
    unit_source_id = required_source_id(
        unit.get("collectionunitid"),
        "collection_unit",
        state.orphans,
        parent_id=site_id,
    )
    if unit_source_id is None:
        return
    unit_id = f"neotoma:collection-unit:{unit_source_id}"
    state.source_counts["collection_unit_rows"] += 1
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
    )

    dataset = unit.get("dataset")
    if not isinstance(dataset, Mapping):
        add_orphan(state.orphans, "collection_unit", unit_id, "missing_dataset")
        return
    dataset_source_id = required_source_id(
        dataset.get("datasetid"), "dataset", state.orphans, parent_id=unit_id
    )
    if dataset_source_id is None:
        return
    dataset_id = f"neotoma:dataset:{dataset_source_id}"
    state.source_counts["dataset_rows"] += 1
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
