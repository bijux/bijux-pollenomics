"""Close metadata populations without inventing selected-source authority."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from hashlib import sha256
import re
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation.models import (
    FACETS,
    MAX_PART_BYTES,
    SCHEMA,
    SCOPED_SCHEMA,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
    encoded_json,
)

from ...serialization import canonical_json
from .publication import SUPPORT_POPULATIONS, ancillary_counts

ANCILLARY_KINDS = (
    "ancillary_context",
    "facet_slots",
    "ancillary_observations",
    "linked_occurrences",
    "supporting_archives",
    "supporting_entries",
)
_FIELDS = {
    "ancillary_context": "record_id",
    "facet_slots": "slot_key",
    "ancillary_observations": "observation_id",
    "linked_occurrences": "occurrence_id",
}


def _digest(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("Ancillary source manifest digest differs")
    return value


def _native_id(value: object) -> int:
    if type(value) is not int or value < 1:
        raise ValueError("Ancillary source native ID is not a literal positive integer")
    return value


def metadata_only(value: Any) -> None:
    """Source JSON has no entity buffer, active href or elevated verification claim."""
    if isinstance(value, Mapping):
        for key, member in value.items():
            if key in {
                "native_body",
                "native_payload",
                "body_buffer",
                "href",
                "download_url",
            }:
                raise ValueError(
                    "Ancillary metadata cannot embed a native reader, body or active href"
                )
            if (
                key
                in {
                    "entity_body_hashes_verified",
                    "source_entity_bodies_verified",
                    "body_hashes_verified",
                    "native_profiles_verified",
                    "native_field_value_verified",
                    "source_assessments_replayed",
                    "related_resource_graph_complete",
                }
                and member is not False
            ):
                raise ValueError(
                    "Ancillary metadata cannot assert body/profile verification or complete related graph"
                )
            if key == "scientific_admission" and member != "not_asserted":
                raise ValueError(
                    "Ancillary metadata cannot assert scientific admission"
                )
            metadata_only(member)
    elif isinstance(value, (list, tuple)):
        for member in value:
            metadata_only(member)
    elif value is not None and type(value) not in (str, int, float, bool):
        raise ValueError(
            "Ancillary source metadata requires JSON, never entity bytes or local resolvers"
        )


def _same(left: object, right: object) -> bool:
    return canonical_json(left) == canonical_json(right)


def archive_id(row: Mapping[str, Any]) -> str:
    kind = row.get("archive_kind")
    if not isinstance(kind, str) or kind not in SUPPORT_POPULATIONS:
        raise ValueError("Supporting source archive kind differs")
    return f"{kind}:{_digest(row.get('archive_manifest_sha256'))}"


def ancillary_record_id(kind: str, row: Mapping[str, Any]) -> str:
    metadata_only(row)
    required = {
        "ancillary_context": ("source_manifest", "summary", "provenance"),
        "facet_slots": ("root_identity",),
        "ancillary_observations": ("capture_epoch",),
        "linked_occurrences": (),
        "supporting_archives": ("manifest", "index_metadata"),
        "supporting_entries": ("entry",),
    }
    if any(not isinstance(row.get(key), dict) for key in required[kind]):
        raise ValueError("Ancillary source structured metadata fields differ")
    if kind == "facet_slots":
        for key in ("dataset_id", "site_id", "collection_unit_id"):
            _native_id(row["root_identity"].get(key))
    if kind == "ancillary_observations":
        fields = (
            "kind",
            "source_capture_manifest_sha256",
            "capsule_manifest_sha256",
            "source_entry_pointer",
            "terminal_status",
            "current_owner_join",
            "current_use_role",
            "selected_by_default",
        )
        if any(key not in row for key in fields) or row["kind"] not in {
            "facet",
            "linked",
        }:
            raise ValueError("Ancillary observation fields differ")
        owner = (
            row.get("root_identity") if row["kind"] == "facet" else row.get("identity")
        )
        if not isinstance(owner, dict):
            raise ValueError("Ancillary observation native identity differs")
    if kind == "supporting_archives":
        return archive_id(row)
    if kind == "supporting_entries":
        index = row.get("row_index")
        archive_kind = row.get("archive_kind")
        if (
            type(index) is not int
            or index < 0
            or not isinstance(archive_kind, str)
            or row.get("population") != SUPPORT_POPULATIONS.get(archive_kind)
        ):
            raise ValueError("Supporting source row ordinal or population differs")
        return f"{archive_id(row)}:{row['population']}:{index}"
    identity = row.get(_FIELDS[kind])
    if not isinstance(identity, str) or not identity or len(identity) > 4096:
        raise ValueError("Ancillary source record identity differs")
    if kind == "ancillary_context" and identity != "ancillary":
        raise ValueError("Ancillary source context identity differs")
    return identity


def _supporting(groups: Mapping[str, Any]) -> None:
    headers, entries = groups["supporting_archives"], groups["supporting_entries"]
    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in headers}
    for row in entries.values():
        key = archive_id(row)
        if key not in grouped:
            raise ValueError("Supporting source row references a missing archive")
        grouped[key].append(row)
    for key, header in headers.items():
        population = SUPPORT_POPULATIONS[header["archive_kind"]]
        records = sorted(grouped[key], key=lambda row: row["row_index"])
        if (
            header.get("index_population") != population
            or type(header.get("index_record_count")) is not int
            or header["index_record_count"] != len(records)
            or [row["row_index"] for row in records] != list(range(len(records)))
            or population in header["index_metadata"]
        ):
            raise ValueError("Supporting source index population is incomplete")
        index = {
            **header["index_metadata"],
            population: [row["entry"] for row in records],
        }
        raw = encoded_json(index)
        expected = header["manifest"]["files"]["index.json"]
        if expected != {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}:
            raise ValueError(
                "Supporting source index identity differs from its archive manifest"
            )
        if (
            header.get("entity_body_hashes_verified") is not False
            or header.get("native_profiles_verified") is not False
            or header.get("source_assessments_replayed") is not False
            or header.get("selected_source_authority")
            != "not_provided_by_metadata_projection"
        ):
            raise ValueError("Supporting source verification posture differs")


def _context_source(manifest: Mapping[str, Any]) -> None:
    if (
        manifest.get("schema_version") not in {SCHEMA, SCOPED_SCHEMA}
        or manifest.get("scientific_admission") != "not_asserted"
        or any(
            manifest.get(key) is not False
            for key in (
                "entity_body_hashes_verified",
                "source_assessments_replayed",
                "original_preget_scope_reconstructed",
                "related_resource_graph_complete",
            )
        )
        or type(manifest.get("payload_copies")) is not int
        or manifest["payload_copies"] != 0
    ):
        raise ValueError(
            "Ancillary source federation schema or verification posture differs"
        )
    guard = manifest.get("current_use_parent_obligations")
    if not isinstance(guard, dict) or set(guard) != {
        "path",
        "sha256",
        "bytes",
        "scope",
    }:
        raise ValueError("Ancillary source parent scope descriptor differs")
    if (
        guard["path"] != "scope/current-parent-proof.json"
        or guard["scope"] != "current_use_metadata_only_not_historical_preget"
        or type(guard["bytes"]) is not int
        or not 0 < guard["bytes"] <= MAX_PART_BYTES
        or _digest(guard["sha256"])
        != manifest.get("current_use_parent_obligations_sha256")
        or not _same(
            manifest.get("files", {}).get(guard["path"]),
            {"bytes": guard["bytes"], "sha256": guard["sha256"]},
        )
    ):
        raise ValueError(
            "Ancillary source parent scope path, bound or identity differs"
        )


def validate_ancillary_groups(
    domain: Mapping[str, Any], groups: Mapping[str, Any], resources: Mapping[str, Any]
) -> None:
    groups = {kind: groups.get(kind, {}) for kind in ANCILLARY_KINDS}
    contexts = groups["ancillary_context"]
    if (
        set(contexts) != {"ancillary"}
        or domain.get("ancillary_context_part_id") != "ancillary_context:0"
    ):
        raise ValueError("Ancillary context population or part identity differs")
    context = contexts["ancillary"]
    manifest, provenance, summary = (
        context["source_manifest"],
        context["provenance"],
        context["summary"],
    )
    _context_source(manifest)
    if (
        manifest.get("declared_facets") != list(FACETS)
        or not _same(manifest.get("summary"), summary)
        or context.get("integrity_scope") != "current_context_and_capsule_metadata"
        or context.get("entity_body_hashes_verified") is not False
        or context.get("source_assessments_replayed") is not False
    ):
        raise ValueError(
            "Ancillary source context facets, summary or integrity differs"
        )
    for field in ("context_manifest_sha256", "native_archive_manifest_sha256"):
        if _digest(provenance.get(field)) != manifest.get(field):
            raise ValueError("Ancillary source independent parent anchors differ")
    _digest(provenance.get("federation_manifest_sha256"))
    if (
        provenance.get("catalogue_manifest_sha256")
        != domain["catalogue_manifest_sha256"]
        or provenance.get("selection_authority")
        != "not_provided_by_metadata_projection"
    ):
        raise ValueError("Ancillary source native anchor or authority differs")
    slots, observations, occurrences = (
        groups["facet_slots"],
        groups["ancillary_observations"],
        groups["linked_occurrences"],
    )
    expected_slots = {
        f"dataset-{key}-facet-{facet}-current" for key in resources for facet in FACETS
    }
    if set(slots) != expected_slots:
        raise ValueError(
            "Ancillary facet/native resource slot population is incomplete"
        )
    matched_by_slot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in observations.values():
        if (
            observation.get("kind") == "facet"
            and observation.get("current_owner_join") == "exact_current_owner"
        ):
            matched_by_slot[observation["facet_key"]].append(observation)
    roles: dict[str, str] = {}
    for key, slot in slots.items():
        owner = slot["root_identity"]
        resource = resources.get(str(_native_id(owner.get("dataset_id"))))
        if resource is None:
            raise ValueError("Ancillary native slot owner is unavailable")
        expected = (
            {
                field: int(resource[field])
                if field.endswith("_id")
                else resource[field]
                for field in (
                    "dataset_id",
                    "site_id",
                    "collection_unit_id",
                    "dataset_type",
                    "database",
                )
            }
            if resource
            else None
        )
        if (
            not _same(owner, expected)
            or slot.get("facet") not in FACETS
            or key != f"dataset-{owner['dataset_id']}-facet-{slot['facet']}-current"
            or slot.get("selected_observation_id") is not None
            or slot.get("current_declared_role") != resource["exposure_role"]
        ):
            raise ValueError("Ancillary exact native slot owner or selection differs")
        role = slot.get("current_use_role")
        dataset = str(owner["dataset_id"])
        if not isinstance(role, str) or dataset in roles and roles[dataset] != role:
            raise ValueError(
                "Ancillary current slot roles differ within a native owner"
            )
        roles[dataset] = role
        members = slot.get("observation_ids")
        if (
            not isinstance(members, list)
            or any(not isinstance(value, str) for value in members)
            or len(set(members)) != len(members)
        ):
            raise ValueError("Ancillary slot observation membership repeats")
        matched = matched_by_slot[key]
        if (
            set(members) != {row["observation_id"] for row in matched}
            or not _same(
                slot.get("source_terminal_counts"),
                dict(Counter(row["terminal_status"] for row in matched)),
            )
            or any(
                not _same(
                    {field: row["root_identity"].get(field) for field in owner}, owner
                )
                for row in matched
            )
        ):
            raise ValueError("Ancillary slot observation population differs")
    for key, row in observations.items():
        if (
            row.get("kind") not in {"facet", "linked"}
            or row.get("selected_by_default") is not False
            or key
            != f"{_digest(row.get('source_capture_manifest_sha256'))}:{row.get('source_entry_pointer')}"
            or _digest(row.get("capsule_manifest_sha256"))
            not in manifest["capsule_manifest_sha256s"]
            or row["source_capture_manifest_sha256"]
            not in manifest["capsule_captures"].get(row["capsule_manifest_sha256"], [])
        ):
            raise ValueError(
                "Ancillary observation source identity or default selection differs"
            )
    for row in occurrences.values():
        observation = observations.get(row.get("observation_id"))
        if (
            observation is None
            or observation["kind"] != "linked"
            or row.get("linked_capture_manifest_sha256")
            != observation["source_capture_manifest_sha256"]
            or row.get("native_field_value_verified") is not False
        ):
            raise ValueError("Ancillary linked occurrence source membership differs")
        locator = row.get("evidence_locator")
        if locator is not None:
            state, part = (
                _digest(locator.get("evidence_manifest_sha256")),
                _digest(locator.get("part_sha256")),
            )
            offset = locator.get("row_offset")
            expected_occurrence = (
                f"{row['observation_id']}:evidence:{state}:{part}:{offset}"
            )
            reference = observation["identity"].get("source_proof_reference", {})
            ranges = reference.get("proof_ranges", [])
            membership = (
                any(
                    isinstance(item, dict)
                    and item.get("part_sha256") == part
                    and type(item.get("start")) is int
                    and type(item.get("count")) is int
                    and item["start"] <= offset < item["start"] + item["count"]
                    for item in ranges
                )
                if type(offset) is int
                else False
            )
            if (
                type(offset) is not int
                or offset < 0
                or state not in manifest.get("linked_evidence", {})
                or state
                != observation.get("source_evidence", {}).get("manifest_sha256")
                or not membership
                or row["occurrence_id"] != expected_occurrence
                or "source_proof_pointer" in row
                or "source_proof" in row
            ):
                raise ValueError("Ancillary scoped occurrence locator differs")
        elif not isinstance(row.get("source_proof"), dict) or not isinstance(
            row.get("source_proof_pointer"), str
        ):
            raise ValueError("Ancillary legacy occurrence source pointer is missing")
        else:
            prefix = row["observation_id"] + ":proof:"
            position = row["occurrence_id"].removeprefix(prefix)
            if (
                not row["occurrence_id"].startswith(prefix)
                or re.fullmatch(r"0|[1-9][0-9]*", position) is None
                or row["source_proof_pointer"]
                != observation["source_entry_pointer"]
                + "/identity/source_proofs/"
                + position
            ):
                raise ValueError("Ancillary legacy occurrence source pointer differs")
    counts = ancillary_counts(dict(groups))
    if any(
        type(domain.get(key)) is not int or domain[key] != count
        for key, count in counts.items()
    ):
        raise ValueError("Ancillary declared population count differs")
    comparisons = {
        "resource_count": len(resources),
        "declared_facet_count": len(FACETS),
        "required_slot_count": len(slots),
        "observation_count": len(observations),
        "facet_observation_count": counts["ancillary_facet_observation_count"],
        "linked_observation_count": counts["ancillary_linked_observation_count"],
        "linked_occurrence_count": len(occurrences),
        "unmatched_facet_observation_count": sum(
            row["kind"] == "facet"
            and row["current_owner_join"] != "exact_current_owner"
            for row in observations.values()
        ),
    }
    if (
        any(
            type(summary.get(key)) is not int or summary[key] != count
            for key, count in comparisons.items()
        )
        or not _same(
            summary.get("slot_coverage_counts"),
            dict(Counter(row["coverage_status"] for row in slots.values())),
        )
        or not _same(
            summary.get("source_terminal_counts"),
            dict(Counter(row["terminal_status"] for row in observations.values())),
        )
        or not _same(
            summary.get("current_scope_resource_role_counts"),
            dict(Counter(roles.values())),
        )
    ):
        raise ValueError("Ancillary source summary population differs")
    _supporting(groups)
