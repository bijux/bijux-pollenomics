"""Source-owned metadata edges between Neotoma sites, units and dataset types."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import copy
from hashlib import sha256
import json
from typing import Any

from ..client import _validated_neotoma_rows


def positive_native_id(value: object) -> int:
    """Require the positive integer identity supplied by native metadata."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("Neotoma metadata identity must be a positive integer")
    return value


def _refuse_numerical_outcomes(value: object) -> None:
    if isinstance(value, dict):
        if {"samples", "datum", "chroncontrols", "ages"}.intersection(value):
            raise ValueError(
                "Neotoma metadata endpoint returned numerical outcome fields"
            )
        for child in value.values():
            _refuse_numerical_outcomes(child)
    elif isinstance(value, list):
        for child in value:
            _refuse_numerical_outcomes(child)


def _metadata_rows(content: bytes) -> list[dict[str, object]]:
    try:
        payload = json.loads(content)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("Neotoma metadata response is not bounded JSON") from error
    rows = _validated_neotoma_rows(payload)
    if payload.get("status") != "success":
        raise ValueError("Neotoma current metadata lacks successful source status")
    _refuse_numerical_outcomes(rows)
    return rows


def parse_neotoma_site_datasets(site_id: int, content: bytes) -> list[dict[str, Any]]:
    """Read one requested site's current units without parsing sample outcomes."""
    positive_native_id(site_id)
    rows = _metadata_rows(content)
    units: set[int] = set()
    datasets: set[int] = set()
    result = []
    for row_index, row in enumerate(rows):
        site = row.get("site")
        if (
            not isinstance(site, dict)
            or positive_native_id(site.get("siteid")) != site_id
        ):
            raise ValueError("Neotoma metadata response has the wrong site owner")
        unit_id = positive_native_id(site.get("collectionunitid"))
        if unit_id in units:
            raise ValueError("Neotoma metadata contains a duplicate collection unit")
        units.add(unit_id)
        native_datasets = site.get("datasets")
        if not isinstance(native_datasets, list):
            raise ValueError("Neotoma metadata datasets must be a list")
        for dataset in native_datasets:
            if not isinstance(dataset, dict):
                raise ValueError("Neotoma metadata dataset must be an object")
            dataset_id = positive_native_id(dataset.get("datasetid"))
            if dataset_id in datasets:
                raise ValueError("Neotoma metadata contains a duplicate dataset parent")
            datasets.add(dataset_id)
            kind = dataset.get("datasettype")
            if not isinstance(kind, str) or not kind.strip():
                raise ValueError("Neotoma metadata dataset type is missing")
        result.append(
            {
                "site_id": site_id,
                "collection_unit_id": unit_id,
                "source_row_index": row_index,
                "source_payload": copy.deepcopy(
                    {key: value for key, value in site.items() if key != "datasets"}
                ),
                "datasets": copy.deepcopy(native_datasets),
            }
        )
    return result


def parse_neotoma_dataset_metadata(
    dataset_id: int, content: bytes
) -> list[dict[str, Any]]:
    """Bind a dataset-ID metadata result, preserving a successful empty response.

    Empty data is an observation of this exact lookup, not certified absence.
    Returned parents and source types remain provider metadata for later review.
    """
    positive_native_id(dataset_id)
    rows = _metadata_rows(content)
    if not rows:
        return []
    if len(rows) != 1 or not isinstance(site := rows[0].get("site"), dict):
        raise ValueError("Neotoma dataset metadata lacks one native parent row")
    site_id = positive_native_id(site.get("siteid"))
    units = parse_neotoma_site_datasets(site_id, content)
    datasets = units[0]["datasets"]
    if len(datasets) != 1 or datasets[0]["datasetid"] != dataset_id:
        raise ValueError("Neotoma dataset metadata response owner differs")
    return units


def build_neotoma_connected_resources(
    *,
    site_ids: Sequence[int],
    retained_units: Mapping[int, int],
    retained_datasets: Mapping[int, int],
    responses: Mapping[int, bytes],
) -> dict[str, Any]:
    """Close a declared site census and keep current resources separate from admission."""
    declared = [positive_native_id(value) for value in site_ids]
    if not declared or len(set(declared)) != len(declared):
        raise ValueError("Neotoma metadata site roster is empty or duplicate")
    if set(responses) != set(declared):
        raise ValueError("Neotoma metadata response closure differs from site roster")
    for retained_unit, site in retained_units.items():
        positive_native_id(retained_unit)
        if positive_native_id(site) not in declared:
            raise ValueError("Retained Neotoma unit has an undeclared site parent")
    for dataset, retained_parent_unit in retained_datasets.items():
        positive_native_id(dataset)
        if positive_native_id(retained_parent_unit) not in retained_units:
            raise ValueError("Retained Neotoma dataset has an unknown unit parent")
    unit_rows = []
    dataset_rows = []
    source_rows = []
    empty_sites = []
    seen_units: set[int] = set()
    seen_datasets: set[int] = set()
    changes = []
    for site_id in sorted(declared):
        content = responses[site_id]
        digest = sha256(content).hexdigest()
        units = parse_neotoma_site_datasets(site_id, content)
        source_rows.append({"site_id": site_id, "response_sha256": digest})
        if not units:
            empty_sites.append(site_id)
        for unit in units:
            unit_id = unit["collection_unit_id"]
            if unit_id in seen_units:
                raise ValueError("Neotoma current unit has multiple site parents")
            seen_units.add(unit_id)
            retained_site = retained_units.get(unit_id)
            if retained_site is not None and retained_site != site_id:
                changes.append(
                    {
                        "kind": "retained_unit_parent_changed",
                        "collection_unit_id": unit_id,
                        "prior_site_id": retained_site,
                        "current_site_id": site_id,
                    }
                )
            locator = {
                "response_sha256": digest,
                "json_pointer": f"/data/{unit['source_row_index']}/site",
            }
            unit_rows.append(
                {
                    "site_id": site_id,
                    "collection_unit_id": unit_id,
                    "retained_unit": retained_site == site_id,
                    "retained_site_id": retained_site,
                    "source_payload": unit["source_payload"],
                    "source_locator": locator,
                }
            )
            for index, dataset in enumerate(unit["datasets"]):
                dataset_id = dataset["datasetid"]
                if dataset_id in seen_datasets:
                    raise ValueError(
                        "Neotoma current dataset has multiple unit parents"
                    )
                seen_datasets.add(dataset_id)
                prior_unit = retained_datasets.get(dataset_id)
                if prior_unit is not None and prior_unit != unit_id:
                    changes.append(
                        {
                            "kind": "retained_dataset_parent_changed",
                            "dataset_id": dataset_id,
                            "prior_collection_unit_id": prior_unit,
                            "current_collection_unit_id": unit_id,
                        }
                    )
                relationship = (
                    "retained_dataset"
                    if prior_unit == unit_id and retained_site == site_id
                    else "additional_dataset_same_unit"
                    if retained_site == site_id and prior_unit is None
                    else "dataset_other_unit"
                )
                dataset_rows.append(
                    {
                        "site_id": site_id,
                        "collection_unit_id": unit_id,
                        "dataset_id": dataset_id,
                        "dataset_type": dataset["datasettype"],
                        "relationship": relationship,
                        "retained_collection_unit_id": prior_unit,
                        "source_payload": dataset,
                        "source_locator": {
                            "response_sha256": digest,
                            "json_pointer": locator["json_pointer"]
                            + f"/datasets/{index}",
                        },
                    }
                )
    return {
        "schema_version": "neotoma-connected-resource-metadata.v1",
        "source_family": "neotoma",
        "status": "complete_declared_metadata_census",
        "site_ids": sorted(declared),
        "retained_identity_roster": {
            "site_ids": sorted(declared),
            "collection_unit_parents": [
                {"collection_unit_id": unit_id, "site_id": site_id}
                for unit_id, site_id in sorted(retained_units.items())
            ],
            "dataset_parents": [
                {"dataset_id": dataset_id, "collection_unit_id": unit_id}
                for dataset_id, unit_id in sorted(retained_datasets.items())
            ],
        },
        "response_count": len(responses),
        "source_responses": source_rows,
        "collection_units": sorted(
            unit_rows, key=lambda row: row["collection_unit_id"]
        ),
        "datasets": sorted(dataset_rows, key=lambda row: row["dataset_id"]),
        "dataset_type_counts": dict(
            sorted(Counter(row["dataset_type"] for row in dataset_rows).items())
        ),
        "successful_empty_site_ids": empty_sites,
        "unobserved_retained_unit_ids": sorted(set(retained_units) - seen_units),
        "unobserved_retained_dataset_ids": sorted(
            set(retained_datasets) - seen_datasets
        ),
        "historical_parent_changes": changes,
        "absence_certified": False,
        "scientific_admission": "not_asserted",
        "exposure_role": "metadata_only; no sample or observation outcomes",
    }
