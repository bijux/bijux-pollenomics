"""Neotoma metadata request plans, endpoint scope and pagination closure."""

from __future__ import annotations

from collections.abc import Callable
import math
from typing import Any

from ..client import build_neotoma_bbox_geojson
from ..site_inventory.connected_resources import (
    _metadata_rows,
    parse_neotoma_dataset_metadata,
    parse_neotoma_site_datasets,
    positive_native_id,
)
from .models import NeotomaMetadataLimits, NeotomaMetadataPlan, _Request


def _plan_from_spec(
    spec: dict[str, Any],
) -> tuple[NeotomaMetadataPlan, NeotomaMetadataLimits]:
    raw_plan, raw_limits = spec.get("plan"), spec.get("limits")
    legacy_fields = {"inventory_bbox", "inventory_limits", "site_ids"}
    if (
        not isinstance(raw_plan, dict)
        or not legacy_fields <= raw_plan.keys()
        or not raw_plan.keys()
        <= legacy_fields | {"dataset_ids", "inventory_all_dataset_types"}
    ):
        raise ValueError("Neotoma metadata plan must contain its exact declared fields")
    if not isinstance(raw_limits, dict) or set(raw_limits) != {
        "max_requests",
        "max_pages_per_inventory",
        "max_response_bytes",
        "max_total_bytes",
        "timeout_seconds",
    }:
        raise ValueError(
            "Neotoma metadata limits must contain their exact declared fields"
        )
    bbox = raw_plan["inventory_bbox"]
    if bbox is not None and not isinstance(bbox, list):
        raise ValueError("Neotoma metadata bbox must be an array or null")
    if any(
        not isinstance(raw_plan[name], list)
        for name in ("inventory_limits", "site_ids")
    ) or not isinstance(raw_plan.get("dataset_ids", []), list):
        raise ValueError("Neotoma metadata declared populations must be arrays")
    plan = NeotomaMetadataPlan(
        inventory_bbox=tuple(bbox) if bbox is not None else None,
        inventory_limits=tuple(raw_plan["inventory_limits"]),
        site_ids=tuple(raw_plan["site_ids"]),
        dataset_ids=tuple(raw_plan.get("dataset_ids", [])),
        inventory_all_dataset_types=raw_plan.get("inventory_all_dataset_types", False),
    )
    limits = NeotomaMetadataLimits(**raw_limits)
    _validate_plan(plan, limits)
    return plan, limits


def _validate_plan(plan: NeotomaMetadataPlan, limits: NeotomaMetadataLimits) -> None:
    if type(plan.inventory_all_dataset_types) is not bool:
        raise ValueError("Neotoma inventory mode must be a literal boolean")
    if plan.inventory_all_dataset_types and not plan.inventory_limits:
        raise ValueError("Neotoma all-type inventory mode requires inventory queries")
    for name in (
        "max_requests",
        "max_pages_per_inventory",
        "max_response_bytes",
        "max_total_bytes",
    ):
        positive_native_id(getattr(limits, name))
    if (
        isinstance(limits.timeout_seconds, bool)
        or not isinstance(limits.timeout_seconds, (int, float))
        or not math.isfinite(limits.timeout_seconds)
        or limits.timeout_seconds <= 0
    ):
        raise ValueError("Neotoma metadata timeout must be positive and finite")
    if not plan.inventory_limits and not plan.site_ids and not plan.dataset_ids:
        raise ValueError("Neotoma metadata plan is empty")
    if bool(plan.inventory_limits) != (plan.inventory_bbox is not None):
        raise ValueError("Neotoma inventory limits require exactly one declared bbox")
    for limit in plan.inventory_limits:
        if positive_native_id(limit) > 10000:
            raise ValueError("Neotoma inventory limit exceeds the official maximum")
    if len(set(plan.inventory_limits)) != len(plan.inventory_limits):
        raise ValueError("Neotoma inventory query limits are duplicate")
    if plan.inventory_bbox is not None:
        bbox = plan.inventory_bbox
        if len(bbox) != 4 or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in bbox
        ):
            raise ValueError("Neotoma inventory bbox is malformed")
        if not (-180 <= bbox[0] < bbox[2] <= 180 and -90 <= bbox[1] < bbox[3] <= 90):
            raise ValueError("Neotoma inventory bbox is outside geographic bounds")
    for site_id in plan.site_ids:
        positive_native_id(site_id)
    if len(set(plan.site_ids)) != len(plan.site_ids):
        raise ValueError("Neotoma metadata site roster is duplicate")
    for dataset_id in plan.dataset_ids:
        positive_native_id(dataset_id)
    if len(set(plan.dataset_ids)) != len(plan.dataset_ids):
        raise ValueError("Neotoma metadata dataset roster is duplicate")


def _inventory_identities(
    rows: list[dict[str, object]], *, all_dataset_types: bool = False
) -> tuple[set[int], set[int]]:
    units: set[int] = set()
    datasets: set[int] = set()
    for row in rows:
        site = row.get("site")
        if not isinstance(site, dict):
            raise ValueError("Neotoma inventory site is malformed")
        positive_native_id(site.get("siteid"))
        unit_id = positive_native_id(site.get("collectionunitid"))
        if unit_id in units:
            raise ValueError("Neotoma inventory contains a duplicate collection unit")
        units.add(unit_id)
        native_datasets = site.get("datasets")
        if not isinstance(native_datasets, list) or not native_datasets:
            raise ValueError("Neotoma inventory dataset population is malformed")
        for dataset in native_datasets:
            if not isinstance(dataset, dict):
                raise ValueError("Neotoma inventory dataset is malformed")
            dataset_type = dataset.get("datasettype")
            if (
                not isinstance(dataset_type, str)
                or not dataset_type
                or dataset_type.strip() != dataset_type
            ):
                raise ValueError("Neotoma inventory dataset type is malformed")
            if not all_dataset_types and dataset_type != "pollen":
                raise ValueError("Neotoma inventory contains a non-pollen dataset")
            identity = positive_native_id(dataset.get("datasetid"))
            if identity in datasets:
                raise ValueError("Neotoma inventory contains a duplicate dataset")
            datasets.add(identity)
    return units, datasets


def _walk_plan(
    plan: NeotomaMetadataPlan,
    limits: NeotomaMetadataLimits,
    consume: Callable[[_Request], bytes],
) -> tuple[dict[int, list[dict[str, object]]], dict[int, bytes], dict[int, bytes]]:
    inventories = {}
    sites = {}
    datasets_by_id = {}
    for limit in plan.inventory_limits:
        rows: list[dict[str, object]] = []
        seen_units: set[int] = set()
        seen_datasets: set[int] = set()
        if plan.inventory_bbox is None:
            raise ValueError("Neotoma inventory bbox is absent")
        for page in range(limits.max_pages_per_inventory):
            offset = page * limit
            request = _Request(
                f"inventory-limit-{limit}-offset-{offset}",
                "dataset_inventory"
                if plan.inventory_all_dataset_types
                else "pollen_inventory",
                "/datasets",
                {
                    **(
                        {}
                        if plan.inventory_all_dataset_types
                        else {"datasettype": "pollen"}
                    ),
                    "loc": build_neotoma_bbox_geojson(plan.inventory_bbox),
                    "limit": str(limit),
                    "offset": str(offset),
                },
            )
            chunk = _metadata_rows(consume(request))
            if len(chunk) > limit:
                raise ValueError(
                    "Neotoma inventory page is unsuccessful or exceeds its limit"
                )
            units, datasets = _inventory_identities(
                chunk, all_dataset_types=plan.inventory_all_dataset_types
            )
            if seen_units.intersection(units) or seen_datasets.intersection(datasets):
                raise ValueError(
                    "Neotoma inventory pagination contains duplicate identities"
                )
            seen_units.update(units)
            seen_datasets.update(datasets)
            rows.extend(chunk)
            if len(chunk) < limit:
                break
        else:
            raise ValueError(
                "Neotoma inventory page budget lacks successful short-page termination"
            )
        inventories[limit] = rows
    for site_id in sorted(plan.site_ids):
        content = consume(
            _Request(
                f"site-{site_id}-datasets",
                "site_datasets",
                f"/sites/{site_id}/datasets",
                {},
                site_id,
            )
        )
        parse_neotoma_site_datasets(site_id, content)
        sites[site_id] = content
    for dataset_id in sorted(plan.dataset_ids):
        content = consume(
            _Request(
                f"dataset-{dataset_id}-metadata",
                "dataset_metadata",
                f"/datasets/{dataset_id}",
                {},
                dataset_id=dataset_id,
            )
        )
        parse_neotoma_dataset_metadata(dataset_id, content)
        datasets_by_id[dataset_id] = content
    return inventories, sites, datasets_by_id
