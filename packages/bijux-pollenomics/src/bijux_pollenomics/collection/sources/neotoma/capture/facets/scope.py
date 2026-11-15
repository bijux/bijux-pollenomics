"""Authenticate complete native parents and strongest known ancillary obligations."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any
import unicodedata

from ...client import decode_neotoma_json_object, positive_native_id
from .. import NeotomaMetadataLimits, replay_neotoma_metadata_capture
from ..parent_scope import _pinned, _roster
from ..receipts import _object, _read, _safe_root
from ..resources.replay import _same_json
from .models import NeotomaFacetPlan, NeotomaFacetScopeInputs

PARENT_SCOPE_SCHEMA = "neotoma-facet-parent-obligations.v1"
_MAX_SCOPE_BYTES = 16 * 1024 * 1024
_RANK = {
    "development_resource_discovery": 0,
    "exposed_development": 1,
    "reserved_candidate_confirmation": 2,
    "heldout_no_numerical_access": 3,
}
_LIMITS = NeotomaMetadataLimits(
    max_requests=256,
    max_pages_per_inventory=256,
    max_response_bytes=32 * 1024 * 1024,
    max_total_bytes=256 * 1024 * 1024,
)
_POINTER = re.compile(r"/data/(0|[1-9][0-9]*)/site/datasets/(0|[1-9][0-9]*)\Z")


def _source(
    digest: str, reference: dict[str, Any], receipt: dict[str, Any]
) -> dict[str, Any]:
    result = {
        "capture_manifest_sha256": digest,
        "request_name": reference["request_name"],
        "receipt_file": reference["receipt_file"],
        "receipt_sha256": reference["receipt_sha256"],
        "body_file": receipt["body_file"],
        "body_sha256": receipt["retained_body_sha256"],
        "response_sha256": receipt["retained_body_sha256"],
    }
    for key in (
        "request_name",
        "request_method",
        "requested_url",
        "parameters",
        "role",
        "expected_site_id",
        "expected_dataset_id",
        "utc_start",
        "utc_end",
        "tls_mode",
    ):
        if key in receipt:
            result[key] = receipt[key]
    return result


def _metadata(
    inputs: NeotomaFacetScopeInputs, required: set[str]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if (
        not isinstance(inputs.metadata_captures, Mapping)
        or set(inputs.metadata_captures) != required
    ):
        raise ValueError("Facet parent scope metadata resolver closure differs")
    proofs: dict[str, Any] = {}
    bodies: dict[str, Any] = {}
    results: dict[str, Any] = {}
    for digest in sorted(required):
        root = _safe_root(inputs.metadata_captures[digest])
        result = replay_neotoma_metadata_capture(
            root, expected_manifest_sha256=digest, limits=_LIMITS
        )
        results[digest] = result
        manifest = _pinned(root / "capture-manifest.json", digest, 16 * 1024 * 1024)
        records = []
        for reference in manifest["records"]:
            receipt = _pinned(
                root / reference["receipt_file"],
                reference["receipt_sha256"],
                1024 * 1024,
            )
            source = _source(digest, reference, receipt)
            raw = _read(root / receipt["body_file"], _LIMITS.max_response_bytes)
            if sha256(raw).hexdigest() != source["body_sha256"]:
                raise ValueError("Facet parent scope metadata buffer differs")
            records.append(source)
            bodies.setdefault(source["body_sha256"], []).append((_object(raw), source))
        proofs[digest] = {
            "capture_manifest_sha256": digest,
            "plan_sha256": manifest["plan_sha256"],
            "request_count": result.request_count,
            "response_bytes": result.response_bytes,
            "records": records,
        }
    return proofs, bodies, results


def _owner(
    dataset: dict[str, Any], site_id: int, unit_id: int, row: dict[str, Any]
) -> None:
    if (
        positive_native_id(dataset.get("datasetid")) != row["dataset_id"]
        or site_id != row["site_id"]
        or unit_id != row["collection_unit_id"]
        or not _same_json(dataset.get("datasettype"), row["dataset_type"])
        or "database" not in dataset
        or not _same_json(dataset["database"], row["database"])
        or not _same_json(dataset.get("doi", []), row.get("dataset_doi_values", []))
    ):
        raise ValueError(
            "Facet parent scope native dataset/site/core/type/database/DOI differs"
        )


def _current(
    row: dict[str, Any], bodies: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    locator = row["metadata_locator"]
    match = _POINTER.fullmatch(locator.get("json_pointer", ""))
    if match is None:
        raise ValueError("Facet parent scope metadata pointer is invalid")
    witnesses, sites = [], []
    for document, source in bodies.get(locator.get("response_sha256"), []):
        try:
            site = document["data"][int(match[1])]["site"]
            native = site["datasets"][int(match[2])]
        except (IndexError, KeyError, TypeError) as error:
            raise ValueError(
                "Facet parent scope metadata pointer does not resolve"
            ) from error
        if any(
            key not in source or not _same_json(value, source[key])
            for key, value in locator.items()
            if key != "json_pointer"
        ):
            continue
        _owner(
            native,
            positive_native_id(site.get("siteid")),
            positive_native_id(site.get("collectionunitid")),
            row,
        )
        witnesses.append({**source, "json_pointer": locator["json_pointer"]})
        sites.append({key: value for key, value in site.items() if key != "datasets"})
    if not witnesses:
        raise ValueError("Facet parent scope complete metadata witness is unavailable")
    return witnesses, sites


def _historical(
    row: dict[str, Any], inputs: NeotomaFacetScopeInputs, results: dict[str, Any]
) -> dict[str, Any]:
    locator = row["metadata_locator"]
    digest = locator["response_sha256"]
    if set(locator) != {
        "source_kind",
        "response_sha256",
        "json_pointer",
    } or digest not in (inputs.historical_metadata_parts or {}):
        raise ValueError(
            "Facet parent scope historical metadata resolver is unavailable"
        )
    part = _pinned(
        (inputs.historical_metadata_parts or {})[digest], digest, 16 * 1024 * 1024
    )
    match = re.fullmatch(
        r"/rows/(0|[1-9][0-9]*)/source_payload", locator["json_pointer"]
    )
    if match is None:
        raise ValueError("Facet parent scope historical pointer is invalid")
    try:
        outer = part["rows"][int(match[1])]
        native = outer["source_payload"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError(
            "Facet parent scope historical owner is unavailable"
        ) from error
    if (
        outer.get("site_id") != f"neotoma:site:{row['site_id']}"
        or outer.get("collection_unit_id")
        != f"neotoma:collection-unit:{row['collection_unit_id']}"
    ):
        raise ValueError("Facet parent scope historical parent differs")
    if (
        positive_native_id(outer.get("source_dataset_id")) != row["dataset_id"]
        or outer.get("dataset_id") != f"neotoma:dataset:{row['dataset_id']}"
    ):
        raise ValueError("Facet historical outer dataset identity differs")
    _owner(native, row["site_id"], row["collection_unit_id"], row)
    lookup = row.get("current_metadata_lookup", {})
    if (
        set(lookup)
        != {
            "dataset_id",
            "manifest_sha256",
            "body_sha256",
            "successful_empty",
            "absence_certified",
        }
        or type(lookup["dataset_id"]) is not int
        or lookup["dataset_id"] != row["dataset_id"]
        or lookup["successful_empty"] is not True
    ):
        raise ValueError(
            "Facet historical current lookup identity or empty assertion differs"
        )

    captured = results.get(lookup.get("manifest_sha256"))
    response = (
        captured.dataset_responses.get(row["dataset_id"])
        if captured is not None
        else None
    )
    if (
        response is None
        or sha256(response).hexdigest() != lookup.get("body_sha256")
        or _object(response).get("data") != []
        or lookup.get("absence_certified") is not False
    ):
        raise ValueError(
            "Facet parent scope historical success-empty lookup proof differs"
        )
    return {
        "source_kind": locator["source_kind"],
        "part_sha256": digest,
        "json_pointer": locator["json_pointer"],
        "current_metadata_lookup": lookup,
        "historical_owner_fields_verified": True,
        "current_native_metadata_returned": False,
    }


def _prepare_facet_parent_scope(
    plan: NeotomaFacetPlan, inputs: NeotomaFacetScopeInputs
) -> dict[str, Any]:
    """Resolve every declaration before output creation or any ancillary GET.

    Complete source metadata is outcome-free. Numerical facet buffers are never
    inspected to discover a protected parent's duties.
    """
    if not isinstance(inputs, NeotomaFacetScopeInputs):
        raise ValueError("Authenticated facet scope inputs are required")
    roster = _roster(inputs.roster_path, plan.roster_sha256)
    rows = roster["resources"]
    by_id = {row["dataset_id"]: row for row in rows}
    required = set(roster.get("source_metadata_capture_manifest_sha256", []))
    required.update(
        row["current_metadata_lookup"]["manifest_sha256"]
        for row in rows
        if "current_metadata_lookup" in row
    )
    if not required:
        raise ValueError("Facet parent scope declares no native metadata sources")
    proofs, bodies, results = _metadata(inputs, required)
    metadata: dict[int, list[dict[str, Any]]] = {}
    witnesses: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        if (
            row.get("metadata_locator", {}).get("source_kind")
            == "retained_relational_dataset_metadata_not_current_HTTP"
        ):
            witnesses[row["dataset_id"]] = [_historical(row, inputs, results)]
            metadata[row["dataset_id"]] = []
        else:
            witnesses[row["dataset_id"]], metadata[row["dataset_id"]] = _current(
                row, bodies
            )
    roster_sites = {r["site_id"] for r in rows}
    roster_units = {r["collection_unit_id"] for r in rows}
    native_ids = set()
    complete_parents = set()
    for entities in bodies.values():
        document, source = entities[0]
        for unit in document["data"]:
            site = unit["site"]
            site_id = positive_native_id(site["siteid"])
            unit_id = positive_native_id(site["collectionunitid"])
            if any(
                candidate["role"] in {"dataset_inventory", "site_datasets"}
                for _, candidate in entities
            ):
                complete_parents.add((site_id, unit_id))
            for native in site["datasets"]:
                identity = positive_native_id(native["datasetid"])
                native_ids.add(identity)
                if site_id in roster_sites or unit_id in roster_units:
                    if identity not in by_id:
                        raise ValueError(
                            "Facet parent scope has an unclassified native sibling"
                        )
                    _owner(native, site_id, unit_id, by_id[identity])
                    native_site = {
                        key: value for key, value in site.items() if key != "datasets"
                    }
                    if not any(
                        _same_json(native_site, previous)
                        for previous in metadata[identity]
                    ):
                        metadata[identity].append(native_site)
    if any(
        (row["site_id"], row["collection_unit_id"]) not in complete_parents
        for row in rows
        if row["metadata_locator"].get("source_kind")
        != "retained_relational_dataset_metadata_not_current_HTTP"
    ):
        raise ValueError("Facet complete native parent population is not authenticated")
    parents = {identity: identity for identity in by_id}

    def find(identity: int) -> int:
        while parents[identity] != identity:
            parents[identity] = parents[parents[identity]]
            identity = parents[identity]
        return identity

    def join(identities: list[int]) -> None:
        if identities:
            for identity in identities[1:]:
                parents[find(identity)] = find(identities[0])

    keys: dict[tuple[str, str], list[int]] = {}
    for row in rows:
        identity = row["dataset_id"]
        for field in ("site_id", "collection_unit_id"):
            keys.setdefault((field, str(row[field])), []).append(identity)
        for site in metadata[identity]:
            name = site.get("sitename")
            if isinstance(name, str) and name.strip():
                keys.setdefault(
                    (
                        "site_name",
                        " ".join(
                            unicodedata.normalize("NFKC", name).casefold().split()
                        ),
                    ),
                    [],
                ).append(identity)
            geography = site.get("geography")
            if isinstance(geography, str) and geography.strip():
                native_geometry = decode_neotoma_json_object(geography.encode())
            elif isinstance(geography, dict):
                native_geometry = geography
            else:
                continue
            if native_geometry:
                keys.setdefault(
                    (
                        "source_geography",
                        json.dumps(native_geometry, sort_keys=True, allow_nan=False),
                    ),
                    [],
                ).append(identity)
    for identities in keys.values():
        join(identities)
    groups = roster.get("source_dependency_groups", [])
    if not isinstance(groups, list):
        raise ValueError("Facet parent scope dependency declaration is malformed")
    for group in groups:
        if (
            not isinstance(group, dict)
            or set(group) != {"dataset_ids", "relation"}
            or group["relation"] not in {"known_shared_chronology", "known_same_source"}
            or not isinstance(group["dataset_ids"], list)
            or len(group["dataset_ids"]) < 2
        ):
            raise ValueError("Facet parent scope known dependency is malformed")
        identities = [positive_native_id(value) for value in group["dataset_ids"]]
        if len(set(identities)) != len(identities) or not set(identities) <= set(by_id):
            raise ValueError("Facet parent scope known dependency population differs")
        join(identities)
    authority = None
    if "reviewed_exposure_metadata_sha256" in roster:
        if inputs.alias_authority is None:
            raise ValueError("Facet parent scope known-alias authority is required")
        digest = roster["reviewed_exposure_metadata_sha256"]
        audit = _pinned(inputs.alias_authority, digest, 16 * 1024 * 1024)
        if (
            any(
                audit.get(key, 0) != 0
                for key in (
                    "current_and_prior_protected_geometry_leads",
                    "bbox_overlap_or_same_name_leads",
                )
            )
            and not groups
        ):
            raise ValueError(
                "Facet parent scope known-alias obligations remain unresolved"
            )
        authority = {"sha256": digest, "native_review_status": audit.get("status")}
    selected = []
    for resource in sorted(plan.resources, key=lambda item: item.dataset_id):
        row = by_id.get(resource.dataset_id)
        if (
            row is None
            or any(
                not _same_json(getattr(resource, key), row[key])
                for key in (
                    "dataset_id",
                    "site_id",
                    "collection_unit_id",
                    "dataset_type",
                    "database",
                )
            )
            or resource.exposure_role != row["exposure_roles"]["current"]
            or resource.metadata_sha256 != row["metadata_locator"]["response_sha256"]
            or resource.metadata_pointer != row["metadata_locator"]["json_pointer"]
        ):
            raise ValueError(
                "Facet parent scope requested root differs from frozen roster"
            )
        obligations = [
            r for r in rows if find(r["dataset_id"]) == find(resource.dataset_id)
        ]
        role = max(
            (
                role
                for member in obligations
                for role in member["exposure_roles"].values()
            ),
            key=lambda value: _RANK[value],
        )
        selected.append(
            {
                "dataset_id": resource.dataset_id,
                "declared_root_role": resource.exposure_role,
                "effective_scope_role": role,
                "metadata_sources": witnesses[resource.dataset_id],
                "obligations": [
                    {
                        "dataset_id": r["dataset_id"],
                        "site_id": r["site_id"],
                        "collection_unit_id": r["collection_unit_id"],
                        "exposure_roles": r["exposure_roles"],
                        "metadata_locator": r["metadata_locator"],
                    }
                    for r in sorted(obligations, key=lambda item: item["dataset_id"])
                ],
            }
        )
    return {
        "schema_version": PARENT_SCOPE_SCHEMA,
        "roster_sha256": plan.roster_sha256,
        "roster_resource_count": len(rows),
        "native_observed_dataset_count": len(native_ids),
        "metadata_captures": proofs,
        "alias_authority": authority,
        "declared_dependency_groups": groups,
        "parents": selected,
        "unknown_model_sharing": "not_established",
        "equal_age_or_null_ID_model_aliases": False,
        "scientific_admission": "not_asserted",
    }


def prepare_facet_parent_scope(
    plan: NeotomaFacetPlan, inputs: NeotomaFacetScopeInputs
) -> dict[str, Any]:
    """Refuse malformed declarations before output or ancillary source access."""
    try:
        proof = _prepare_facet_parent_scope(plan, inputs)
        encoded = (
            json.dumps(
                proof, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2
            )
            + "\n"
        ).encode()
        if len(encoded) > _MAX_SCOPE_BYTES:
            raise ValueError("Facet parent scope proof exceeds its byte bound")
        return proof
    except (KeyError, TypeError, AttributeError, IndexError) as error:
        raise ValueError("Malformed facet parent scope source or roster") from error


def authenticate_parent_scope(
    root: Path,
    control: dict[str, Any],
    plan: NeotomaFacetPlan,
    resolvers: Mapping[str, NeotomaFacetScopeInputs] | None,
) -> dict[str, Any]:
    reference = control.get("parent_scope")
    if (
        not isinstance(reference, dict)
        or set(reference) != {"file", "sha256"}
        or reference["file"] != "parent-scope.json"
    ):
        raise ValueError("Facet parent scope reference is malformed")
    if resolvers is None or plan.roster_sha256 not in resolvers:
        raise ValueError("Facet parent scope original input resolvers are required")
    proof = _pinned(root / reference["file"], reference["sha256"], _MAX_SCOPE_BYTES)
    expected = prepare_facet_parent_scope(plan, resolvers[plan.roster_sha256])
    if not _same_json(proof, expected):
        raise ValueError("Facet parent scope differs from authenticated native inputs")
    return proof
