"""Whole current native site spans and every known protected alias obligation."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
    load_neotoma_ancillary_context,
)

from ...client import positive_native_id
from ..facets.models import NeotomaFacetPlan
from ..facets.scope import _metadata, _owner, prepare_facet_parent_scope
from ..parent_scope import _pinned, _roster
from ..receipts import _safe_root
from ..resources.models import DEVELOPMENT_ROLES, NeotomaResourceSpec
from ..resources.replay import _same_json
from .models import NeotomaContextResourcePlan

_RANK = {
    "development_resource_discovery": 0,
    "exposed_development": 1,
    "reserved_candidate_confirmation": 2,
    "heldout_no_numerical_access": 3,
}


def _spec(row: dict[str, Any]) -> NeotomaResourceSpec:
    return NeotomaResourceSpec(
        row["dataset_id"],
        row["site_id"],
        row["collection_unit_id"],
        row["dataset_type"],
        row["database"],
        row["exposure_roles"]["current"],
        row["metadata_locator"]["response_sha256"],
        row["metadata_locator"]["json_pointer"],
        ("current",),
    )


def prepare_scope(
    plan: NeotomaContextResourcePlan,
    *,
    context_directory: Path,
    native_archive_directory: Path,
) -> dict[str, Any]:
    """Read outcome-free metadata only, before any context source GET or body.

    An unclassified native sibling prevents a complete alias proof. Such a
    resolver remains an explicit unavailable scope; it cannot authorize a
    caller's known subset of the current site.
    """
    context = load_neotoma_ancillary_context(
        context_directory,
        expected_manifest_sha256=plan.context_manifest_sha256,
        native_archive_directory=native_archive_directory,
    )
    if (
        context.manifest["native_archive"]["manifest_sha256"]
        != plan.native_archive_manifest_sha256
    ):
        raise ValueError("Context independently expected native archive anchor differs")
    if len(context.current_scope_inputs) != 1:
        raise ValueError("Context current roster epoch is ambiguous")
    pin, inputs = next(iter(context.current_scope_inputs.items()))
    roster = _roster(inputs.roster_path, pin)
    rows = roster["resources"]
    by_id = {row["dataset_id"]: row for row in rows}
    sites = {row["site_id"] for row in rows}
    units = {row["collection_unit_id"] for row in rows}
    required = set(roster.get("source_metadata_capture_manifest_sha256", []))
    required.update(
        row["current_metadata_lookup"]["manifest_sha256"]
        for row in rows
        if "current_metadata_lookup" in row
    )
    if not required:
        raise ValueError("Context parent scope has no native metadata sources")
    proofs, bodies, _ = _metadata(inputs, required)
    all_type = set()
    for digest in sorted(required):
        root = _safe_root(inputs.metadata_captures[digest])
        control = _pinned(
            root / "request-plan.json", proofs[digest]["plan_sha256"], 4 * 1024 * 1024
        )
        if control.get("plan", {}).get("inventory_all_dataset_types") is True:
            all_type.add(digest)
    current: dict[int, dict[int, dict[str, Any]]] = {}
    sources: dict[int, list[dict[str, Any]]] = {}
    unclassified: list[dict[str, Any]] = []
    for entities in bodies.values():
        for document, source in entities:
            if (
                source["capture_manifest_sha256"] not in all_type
                or source["role"] != "dataset_inventory"
                or source["parameters"].get("limit") != "10000"
            ):
                continue
            for index, wrapper in enumerate(document["data"]):
                site = wrapper["site"]
                site_id = positive_native_id(site["siteid"])
                unit_id = positive_native_id(site["collectionunitid"])
                if site_id not in sites and unit_id not in units:
                    continue
                native = site["datasets"]
                if not isinstance(native, list) or any(
                    not isinstance(row, dict) for row in native
                ):
                    raise ValueError(
                        "Context native parent dataset population is malformed"
                    )
                identities = [
                    positive_native_id(row.get("datasetid")) for row in native
                ]
                if len(set(identities)) != len(identities):
                    raise ValueError(
                        "Context native parent has duplicate dataset owners"
                    )
                owners = []
                for row in native:
                    identity = row["datasetid"]
                    if identity not in by_id:
                        unclassified.append(
                            {
                                "site_id": site_id,
                                "collection_unit_id": unit_id,
                                "dataset_id": identity,
                            }
                        )
                    else:
                        _owner(row, site_id, unit_id, by_id[identity])
                    if "database" not in row or not isinstance(
                        row.get("datasettype"), str
                    ):
                        raise ValueError(
                            "Context native type/database owner is missing"
                        )
                    owners.append(
                        {
                            key: row[key]
                            for key in ("datasetid", "datasettype", "database")
                        }
                    )
                span = {
                    "site_id": site_id,
                    "collection_unit_id": unit_id,
                    "datasets": sorted(owners, key=lambda row: row["datasetid"]),
                }
                previous = current.setdefault(site_id, {}).get(unit_id)
                if previous is not None and not _same_json(previous, span):
                    raise ValueError("Context current native parent epochs disagree")
                current[site_id][unit_id] = span
                locator = {**source, "json_pointer": f"/data/{index}/site"}
                sources.setdefault(site_id, []).append(locator)
    parent_proof = None
    if not unclassified:
        parent_proof = prepare_facet_parent_scope(
            NeotomaFacetPlan(tuple(_spec(row) for row in rows), pin, ("taxa",)), inputs
        )
    parent_roles = (
        {}
        if parent_proof is None
        else {
            row["dataset_id"]: row["effective_scope_role"]
            for row in parent_proof["parents"]
        }
    )
    ledger = []
    for site_id in sorted(sites):
        members = [row for row in rows if row["site_id"] == site_id]
        role = max(
            (
                role
                for row in members
                for role in (
                    *row["exposure_roles"].values(),
                    parent_roles.get(
                        row["dataset_id"], row["exposure_roles"]["current"]
                    ),
                )
            ),
            key=lambda value: _RANK[value],
        )
        expected: dict[int, dict[str, Any]] = {}
        for row in members:
            if (
                row["metadata_locator"].get("source_kind")
                == "retained_relational_dataset_metadata_not_current_HTTP"
            ):
                continue
            unit_id = row["collection_unit_id"]
            expected.setdefault(
                unit_id,
                {"site_id": site_id, "collection_unit_id": unit_id, "datasets": []},
            )["datasets"].append(
                {
                    "datasetid": row["dataset_id"],
                    "datasettype": row["dataset_type"],
                    "database": row["database"],
                }
            )
        for value in expected.values():
            value["datasets"].sort(key=lambda row: row["datasetid"])
        actual = current.get(site_id, {})
        complete = bool(expected) and _same_json(expected, actual) and not unclassified
        status = (
            "protected_current_scope"
            if role not in DEVELOPMENT_ROLES
            else "eligible_current_scope"
            if complete
            else "unestablished_current_parent_scope"
        )
        ledger.append(
            {
                "site_id": site_id,
                "scope_status": status,
                "effective_scope_role": role,
                "roster_dataset_ids": sorted(row["dataset_id"] for row in members),
                "current_native_units": [actual[key] for key in sorted(actual)],
                "native_source_locators": sources.get(site_id, []),
                "current_parent_span_matches_roster": complete,
                "scientific_admission": "not_asserted",
            }
        )
    by_site = {row["site_id"]: row for row in ledger}
    requested = [
        by_site.get(
            site_id,
            {
                "site_id": site_id,
                "scope_status": "unestablished_current_parent_scope",
                "effective_scope_role": None,
                "roster_dataset_ids": [],
                "current_native_units": [],
                "native_source_locators": [],
                "current_parent_span_matches_roster": False,
                "scientific_admission": "not_asserted",
            },
        )
        for site_id in plan.site_ids
    ]
    return {
        "schema_version": "neotoma-current-site-context-parent-scope.v1",
        "context_manifest_sha256": plan.context_manifest_sha256,
        "native_archive_manifest_sha256": plan.native_archive_manifest_sha256,
        "current_roster_sha256": pin,
        "all_type_metadata_capture_manifest_sha256s": sorted(all_type),
        "metadata_captures": proofs,
        "facet_parent_obligations": parent_proof,
        "unclassified_native_parents": sorted(
            {
                (row["site_id"], row["collection_unit_id"], row["dataset_id"]): row
                for row in unclassified
            }.values(),
            key=lambda row: (
                row["site_id"],
                row["collection_unit_id"],
                row["dataset_id"],
            ),
        ),
        "site_ledger": ledger,
        "site_partitions": dict(Counter(row["scope_status"] for row in ledger)),
        "site_count": len(ledger),
        "requested_sites": requested,
        "numerical_source_entities_inspected": False,
        "unknown_model_sharing": "not_established",
        "scientific_admission": "not_asserted",
    }
