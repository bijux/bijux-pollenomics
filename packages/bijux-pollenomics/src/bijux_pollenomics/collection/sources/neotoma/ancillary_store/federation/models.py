"""Current-use coverage and immutable occurrence indexes, without scientific admission."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...capture.linked_resources.protocol import _RANK
from ...capture.resources.models import DEVELOPMENT_ROLES
from ...resource_catalogue.archive.files import encoded_json
from ...resource_catalogue.source_projection import _same

SCHEMA = "neotoma-ancillary-source-federation.v1"
INDEX_SCHEMA = "neotoma-ancillary-federation-index.v1"
FACETS = (
    "chronologies",
    "lithology",
    "projects",
    "publications",
    "taxa",
    "contacts",
    "doi",
    "sites",
)
MAX_PART_BYTES = 16 * 1024 * 1024
_OWNER = ("dataset_id", "site_id", "collection_unit_id", "dataset_type", "database")


@dataclass(frozen=True)
class NeotomaAncillaryFederation:
    """A complete declared metadata view; source entity integrity remains unverified."""

    manifest: dict[str, Any]
    summary: dict[str, Any]
    slots: list[dict[str, Any]]
    observations: list[dict[str, Any]]
    linked_occurrences: list[dict[str, Any]]
    integrity_scope: str = field(
        default="current_context_and_capsule_metadata", init=False
    )
    entity_body_hashes_verified: bool = field(default=False, init=False)
    source_assessments_replayed: bool = field(default=False, init=False)


@dataclass(frozen=True)
class FederationMetadata:
    """Deterministic buffers and resolvers for publication or explicit full replay."""

    manifest: dict[str, Any]
    buffers: dict[str, bytes]
    view: NeotomaAncillaryFederation
    capsule_sources: dict[str, Path]
    predecessors: dict[str, dict[str, Path]]


def _owner(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row[key] for key in _OWNER}


def _match(owner: dict[str, Any], roots: dict[int, dict[str, Any]]) -> str:
    root = roots.get(owner["dataset_id"])
    if root is None:
        return "source_root_not_in_current_context"
    return (
        "exact_current_owner"
        if _same(_owner(owner), _owner(root))
        else "source_owner_differs_from_current_context"
    )


def _observation_id(row: dict[str, Any]) -> str:
    return f"{row['source_capture_manifest_sha256']}:{row['source_entry_pointer']}"


def assemble_view(
    roster: dict[str, Any],
    roles: dict[int, str],
    indexes: dict[str, dict[str, Any]],
    attempts: dict[tuple[str, str], list[dict[str, Any]]],
) -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]
]:
    """Preserve all epochs while joining only exact current native owner tuples."""
    roots = {row["dataset_id"]: row for row in roster["resources"]}
    observations: list[dict[str, Any]] = []
    occurrences: list[dict[str, Any]] = []
    by_slot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    facets = {
        (row["source_capture_manifest_sha256"], row["facet_key"]): row
        for index in indexes.values()
        for row in index["observations"]
        if row["kind"] == "facet"
    }
    for capsule, index in sorted(indexes.items()):
        captures = {
            row["source_capture_manifest_sha256"]: row for row in index["captures"]
        }
        for source in index["observations"]:
            identity = _observation_id(source)
            capture = source["source_capture_manifest_sha256"]
            row = {key: value for key, value in source.items() if key != "attempts"}
            row.update(
                observation_id=identity,
                capsule_manifest_sha256=capsule,
                attempts=attempts[capture, source["source_entry_pointer"]],
                selected_by_default=False,
            )
            row["capture_epoch"] = {
                key: captures[capture][key]
                for key in (
                    "capture_utc_start",
                    "capture_utc_end",
                    "snapshot_consistency",
                )
            }
            if row["kind"] == "facet":
                match = _match(row["root_identity"], roots)
                role = roles.get(row["root_identity"]["dataset_id"])
                row.update(
                    current_owner_join=match,
                    current_use_role=role,
                    capture_parent_scope_verification=source[
                        "parent_scope_verification"
                    ],
                )
                if match == "exact_current_owner":
                    by_slot[row["facet_key"]].append(row)
            else:
                proofs = source["identity"]["source_proofs"]
                row["identity"] = {
                    key: value
                    for key, value in source["identity"].items()
                    if key != "source_proofs"
                }
                joins, inherited = [], []
                for position, proof in enumerate(proofs):
                    original = facets[
                        proof["source_capture_manifest_sha256"],
                        proof["source_facet_key"],
                    ]
                    match = _match(proof["root_identity"], roots)
                    role = roles.get(proof["root_dataset_id"])
                    joins.append(match)
                    if role is not None:
                        inherited.append(role)
                    occurrences.append(
                        {
                            "occurrence_id": f"{identity}:proof:{position}",
                            "observation_id": identity,
                            "linked_capture_manifest_sha256": capture,
                            "source_proof_pointer": source["source_entry_pointer"]
                            + f"/identity/source_proofs/{position}",
                            "source_proof": proof,
                            "current_owner_join": match,
                            "current_use_role": role,
                            "capture_parent_scope_verification": original[
                                "parent_scope_verification"
                            ],
                            "native_field_value_verified": False,
                        }
                    )
                match = (
                    "exact_current_owner"
                    if all(value == "exact_current_owner" for value in joins)
                    else "linked_source_owner_differs_from_current_context"
                )
                role = (
                    max(inherited, key=lambda value: _RANK[value])
                    if inherited
                    else None
                )
                row.update(
                    current_owner_join=match,
                    current_use_role=role,
                    capture_parent_scope_verification="inherited_from_original_source_occurrences",
                )
            row["current_use_scope_verification"] = (
                "authenticated_current_context_only"
                if match == "exact_current_owner"
                else "not_established_for_unmatched_original_owner"
            )
            row["access_restrictions"] = (
                (["owner_context_mismatch"] if match != "exact_current_owner" else [])
                + (
                    ["protected_current_scope"]
                    if role is not None and role not in DEVELOPMENT_ROLES
                    else []
                )
                + (["current_role_unknown"] if role is None else [])
            )
            row["current_use_role_basis"] = (
                "most_restrictive_known_native_dataset_restriction"
            )
            row["entity_access_status"] = (
                "blocked_current_scope"
                if role is not None and role not in DEVELOPMENT_ROLES
                else "blocked_owner_context"
                if match != "exact_current_owner" or role is None
                else "requires_selected_source_guard"
            )
            if (
                match == "exact_current_owner"
                and role in DEVELOPMENT_ROLES
                and row["attempts"]
                and "body_file" in row["attempts"][-1]
            ):
                attempt = row["attempts"][-1]
                locator = {
                    "capsule_manifest_sha256": capsule,
                    "capture_manifest_sha256": capture,
                    "source_entry_pointer": source["source_entry_pointer"],
                    "receipt_sha256": attempt["receipt_sha256"],
                    "body_sha256": attempt["body_sha256"],
                    "body_relative_path": f"captures/{capture}/{attempt['body_file']}",
                    "body_complete": attempt["body_complete"],
                    "http_status": attempt["http_status"],
                    "selected_guard_required": True,
                    "entity_body_hash_verified": False,
                }
                row["forensic_locator"] = locator
                if row["terminal_status"].startswith("received_complete_unqualified_"):
                    row["download_locator"] = locator
            observations.append(row)
    if len({_observation_id(row) for row in observations}) != len(observations):
        raise ValueError("Federation observation identity is ambiguous")
    slots = []
    for root in sorted(roots.values(), key=lambda row: row["dataset_id"]):
        for facet in FACETS:
            key = f"dataset-{root['dataset_id']}-facet-{facet}-current"
            sources = by_slot[key]
            received = any(
                row["terminal_status"] == "received_complete_unqualified_facet"
                for row in sources
            )
            status = (
                "protected_current_scope"
                if roles[root["dataset_id"]] not in DEVELOPMENT_ROLES
                else "pending_capture"
                if not sources
                else "complete_source_entity"
                if received
                else "recorded_without_complete_source_entity"
            )
            slots.append(
                {
                    "slot_key": key,
                    "root_identity": _owner(root),
                    "facet": facet,
                    "content_version": "current",
                    "api_version": "v2.0",
                    "current_declared_role": root["exposure_roles"]["current"],
                    "current_use_role": roles[root["dataset_id"]],
                    "current_use_scope_verification": "authenticated_current_context_only",
                    "coverage_status": status,
                    "observation_ids": [row["observation_id"] for row in sources],
                    "selected_observation_id": None,
                    "source_terminal_counts": dict(
                        sorted(
                            Counter(row["terminal_status"] for row in sources).items()
                        )
                    ),
                    "scientific_admission": "not_asserted",
                }
            )
    summary = {
        "resource_count": len(roots),
        "declared_facet_count": len(FACETS),
        "required_slot_count": len(slots),
        "observation_count": len(observations),
        "facet_observation_count": sum(row["kind"] == "facet" for row in observations),
        "linked_observation_count": sum(
            row["kind"] == "linked" for row in observations
        ),
        "linked_occurrence_count": len(occurrences),
        "unmatched_facet_observation_count": sum(
            row["kind"] == "facet"
            and row["current_owner_join"] != "exact_current_owner"
            for row in observations
        ),
        "slot_coverage_counts": dict(
            sorted(Counter(row["coverage_status"] for row in slots).items())
        ),
        "source_terminal_counts": dict(
            sorted(Counter(row["terminal_status"] for row in observations).items())
        ),
        "current_scope_resource_role_counts": dict(
            sorted(Counter(roles.values()).items())
        ),
        "coverage_scope": "declared_capsules_and_current_context",
    }
    return slots, observations, occurrences, summary


def metadata_buffers(
    slots: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    occurrences: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, bytes]:
    """Partition by native dataset ranges or immutable source-capture identities."""
    buffers: dict[str, bytes] = {}
    parts = []
    for population, rows, key_field in (
        ("slots", slots, "slot_key"),
        ("observations", observations, "observation_id"),
        ("linked_occurrences", occurrences, "occurrence_id"),
    ):
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            group = (
                f"native-datasets-{row['root_identity']['dataset_id'] // 1000}"
                if population == "slots"
                else row["source_capture_manifest_sha256"]
                if population == "observations"
                else row["linked_capture_manifest_sha256"]
            )
            groups[group].append(row)

        def partition(
            group: str,
            records: list[dict[str, Any]],
            population: str = population,
            key_field: str = key_field,
        ) -> None:
            raw = encoded_json(
                {
                    "schema_version": INDEX_SCHEMA,
                    "population": population,
                    "rows": records,
                }
            )
            if len(raw) > MAX_PART_BYTES:
                if len(records) < 2:
                    raise ValueError("One federation metadata row exceeds its bound")
                middle = len(records) // 2
                partition(group, records[:middle])
                partition(group, records[middle:])
                return
            first, last = records[0][key_field], records[-1][key_field]
            digest = sha256(
                (group + "\x00" + first + "\x00" + last).encode()
            ).hexdigest()
            path = f"{population}/{digest}.json"
            if path in buffers:
                raise ValueError("Federation metadata range identity is ambiguous")
            buffers[path] = raw
            parts.append(
                {
                    "population": population,
                    "group": group,
                    "first_key": first,
                    "last_key": last,
                    "path": path,
                    "sha256": sha256(raw).hexdigest(),
                    "bytes": len(raw),
                    "row_count": len(records),
                }
            )

        for group, records in sorted(groups.items()):
            partition(group, sorted(records, key=lambda row: row[key_field]))
    root = encoded_json(
        {"schema_version": INDEX_SCHEMA, "summary": summary, "parts": parts}
    )
    if len(root) > MAX_PART_BYTES:
        raise ValueError("Federation metadata part index exceeds its bound")
    return {"index.json": root, **buffers}
