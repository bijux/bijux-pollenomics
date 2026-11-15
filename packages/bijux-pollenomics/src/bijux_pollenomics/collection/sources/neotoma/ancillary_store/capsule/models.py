"""Finite capsule metadata and source occurrence serialization."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...capture.facets.models import SCOPED_FACET_SCHEMA
from ...capture.linked_resources.protocol import _RANK
from ...capture.models import _Request
from ...capture.receipts import _request_record, _utc, _validate_transport_failure
from ...capture.resources.models import EXPOSURE_ROLES
from ...client import positive_native_id
from ...resource_catalogue.archive.files import encoded_json
from ...resource_catalogue.source_projection import _same
from ..context.validation import NeotomaAncillaryContext

CAPSULE_SCHEMA = "neotoma-ancillary-source-capsule.v1"
INDEX_SCHEMA = "neotoma-ancillary-source-occurrences.v1"
MAX_INDEX_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class NeotomaAncillaryCapsule:
    """Full replay result, not a selected-only or scientifically admitted view."""

    manifest: dict[str, Any]
    index: dict[str, Any]
    facet_sources: dict[str, Path]
    linked_sources: dict[str, Path]


def index_buffers(index: dict[str, Any]) -> dict[str, bytes]:
    """Keep large occurrence populations in bounded native-identity range parts."""
    content = encoded_json(index)
    if len(content) <= MAX_INDEX_BYTES:
        return {"index.json": content}
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in index["observations"]:
        kind = row["kind"]
        semantic = row["facet"] if kind == "facet" else row["identity"]["kind"]
        grouped[kind, row["source_capture_manifest_sha256"], semantic].append(row)
    buffers: dict[str, bytes] = {}
    parts = []

    def partition(prefix: str, rows: list[dict[str, Any]]) -> None:
        raw = encoded_json({"schema_version": INDEX_SCHEMA, "observations": rows})
        if len(raw) > MAX_INDEX_BYTES:
            if len(rows) < 2:
                raise ValueError(
                    "One ancillary source occurrence exceeds metadata bound"
                )
            middle = len(rows) // 2
            partition(prefix, rows[:middle])
            partition(prefix, rows[middle:])
            return

        def identity(row: dict[str, Any]) -> int:
            return int(
                row["root_identity"]["dataset_id"]
                if row["kind"] == "facet"
                else row["identity"]["native_id"]
            )

        relative = f"index/observations/{prefix}/native-{identity(rows[0])}-{identity(rows[-1])}.json"
        if relative in buffers:
            raise ValueError("Ancillary source occurrence identity range is ambiguous")
        buffers[relative] = raw
        parts.append(
            {
                "path": relative,
                "sha256": sha256(raw).hexdigest(),
                "bytes": len(raw),
                "row_count": len(rows),
            }
        )

    for key, rows in sorted(grouped.items()):
        partition("/".join(key), rows)
    root = {key: value for key, value in index.items() if key != "observations"}
    root["observation_parts"] = parts
    root["observation_count"] = len(index["observations"])
    raw = encoded_json(root)
    if len(raw) > MAX_INDEX_BYTES:
        raise ValueError("Ancillary capsule index directory exceeds metadata bound")
    return {"index.json": raw, **buffers}


def compact_index(
    captures: dict[str, Any], documents: dict[str, Any], controls: dict[str, Any]
) -> dict[str, Any]:
    observations, summaries = [], []
    for digest, descriptor in sorted(captures.items()):
        kind = descriptor["kind"]
        manifest, control = documents[digest], controls[digest]
        scoped = descriptor["native_schema_version"] == SCOPED_FACET_SCHEMA
        summary = {
            key: manifest[key]
            for key in (
                "request_count",
                "response_bytes",
                "partitions",
                "capture_utc_start",
                "capture_utc_end",
                "snapshot_consistency",
            )
        }
        summary.update(
            source_capture_manifest_sha256=digest,
            kind=kind,
            native_schema_version=descriptor["native_schema_version"],
            policy_sources=control["policy_sources"],
        )
        if kind == "facet":
            summary.update(
                original_roster_sha256=control["plan"]["roster_sha256"],
                parent_scope_verification="authenticated_original_parent_scope"
                if scoped
                else "not_recorded_legacy_capture",
            )
        else:
            summary["source_facet_manifest_sha256s"] = control["plan"][
                "source_facet_manifest_sha256s"
            ]
        summaries.append(summary)
        source_rows = manifest["facets" if kind == "facet" else "resources"]
        for offset, entry in enumerate(source_rows):
            fields = (
                ("facet_key", "root_identity", "facet")
                if kind == "facet"
                else ("target_key", "identity")
            )
            row = {
                key: entry[key]
                for key in (
                    *fields,
                    "content_version",
                    "api_version",
                    "terminal_status",
                    "attempts",
                )
            }
            row["attempts"] = [
                {
                    **attempt,
                    **(
                        {
                            "body_sha256": descriptor["files"][attempt["body_file"]][
                                "sha256"
                            ],
                            "body_bytes": descriptor["files"][attempt["body_file"]][
                                "bytes"
                            ],
                        }
                        if "body_file" in attempt
                        else {}
                    ),
                }
                for attempt in entry["attempts"]
            ]
            row.update(
                kind=kind,
                source_capture_manifest_sha256=digest,
                source_entry_pointer=f"/{'facets' if kind == 'facet' else 'resources'}/{offset}",
                scientific_admission="not_asserted",
            )
            if kind == "facet":
                row["parent_scope_role"] = entry.get("parent_scope_role")
                row["parent_scope_verification"] = summary["parent_scope_verification"]
            observations.append(row)
    return {
        "schema_version": INDEX_SCHEMA,
        "captures": summaries,
        "observations": observations,
        "scientific_admission": "not_asserted",
        "capture_assessments_relabelled": False,
        "numerical_payloads_in_index": False,
    }


@dataclass(frozen=True)
class CapsuleMetadata:
    """Prepared metadata before any source entity replay."""

    manifest: dict[str, Any]
    paths: dict[str, tuple[Path, int]]
    buffers: dict[str, bytes]
    index: dict[str, Any]
    context: NeotomaAncillaryContext
    facet_sources: dict[str, Path]
    linked_sources: dict[str, Path]
    documents: dict[str, Any]
    controls: dict[str, Any]


@dataclass(frozen=True)
class NeotomaAncillaryCapsuleInventory:
    """Authenticated source declarations; no numerical entity integrity claim."""

    root: Path
    manifest: dict[str, Any]
    index: dict[str, Any]
    facet_sources: dict[str, Path]
    linked_sources: dict[str, Path]
    integrity_scope: str = "capsule_metadata_and_source_declarations"
    entity_body_hashes_verified: bool = False
    source_assessments_replayed: bool = False


def verify_metadata_population(
    descriptor: dict[str, Any], manifest: dict[str, Any], control: dict[str, Any]
) -> None:
    """Verify source denominators and closed metadata identities without body claims."""
    kind = descriptor["kind"]
    entries = manifest["facets" if kind == "facet" else "resources"]
    received = (
        "received_complete_unqualified_facet"
        if kind == "facet"
        else "received_complete_unqualified_linked_resource"
    )
    statuses = {
        received,
        "not_attempted_budget",
        "not_attempted_exposure_role",
        "transport_failure",
        "unavailable_http",
        "refused_incomplete_body",
        "refused_http_receipt",
        "refused_native_json",
    }
    if kind == "facet":
        statuses.add("not_attempted_parent_scope")
    count = total = 0
    for entry in entries:
        if (
            not isinstance(entry.get("terminal_status"), str)
            or entry["terminal_status"] not in statuses
            or entry.get("scientific_admission") != "not_asserted"
            or entry.get("content_version") != "current"
            or entry.get("api_version") != "v2.0"
        ):
            raise ValueError("Ancillary source metadata status or admission differs")
        count += len(entry["attempts"])
        total += sum(
            descriptor["files"][attempt["body_file"]]["bytes"]
            for attempt in entry["attempts"]
            if "body_file" in attempt
        )
    if (
        type(manifest["request_count"]) is not int
        or type(manifest["response_bytes"]) is not int
        or manifest["request_count"] != count
        or manifest["response_bytes"] != total
        or not _same(
            manifest["partitions"],
            dict(Counter(row["terminal_status"] for row in entries)),
        )
    ):
        raise ValueError("Ancillary source metadata denominator differs")
    if kind == "linked":
        targets = control["targets"]
        planned = control["plan"]["targets"]
        if (
            not isinstance(targets, list)
            or len(targets) != len(entries)
            or len(planned) != len(entries)
        ):
            raise ValueError("Ancillary linked source target population differs")
        expected = sorted(
            (row["kind"], positive_native_id(row["native_id"])) for row in planned
        )
        actual = []
        for entry, target in zip(entries, targets, strict=True):
            if (
                not isinstance(target, dict)
                or target.get("kind") not in ("contact", "publication", "taxon")
                or not isinstance(target.get("exposure_role"), str)
                or target["exposure_role"] not in EXPOSURE_ROLES
                or not isinstance(target.get("source_proofs"), list)
                or not target["source_proofs"]
            ):
                raise ValueError("Ancillary linked source target identity is malformed")
            identity = positive_native_id(target["native_id"])
            key = f"{target['kind']}-{identity}"
            if (
                entry.get("target_key") != key
                or target.get("target_key") != key
                or not _same(entry.get("identity"), target)
            ):
                raise ValueError(
                    "Ancillary linked source target correspondence differs"
                )
            actual.append((target["kind"], identity))
        if actual != expected or len(set(actual)) != len(actual):
            raise ValueError("Ancillary linked source target selection differs")


def verify_linked_metadata_sources(
    documents: dict[str, Any],
    controls: dict[str, Any],
    descriptors: dict[str, Any],
    linked: Mapping[str, Path],
) -> None:
    """Bind each declared occurrence to predecessor metadata; defer native field values."""
    relations = {
        "chronology_preparer": ("chronologies", "contact"),
        "dataset_contributor": ("contacts", "contact"),
        "dataset_publication": ("publications", "publication"),
        "dataset_reported_taxon": ("taxa", "taxon"),
        "taxonomic_reference_publication": ("taxa", "publication"),
        "source_reported_higher_taxon": ("taxa", "taxon"),
    }
    for digest in linked:
        for target in controls[digest]["targets"]:
            roles = []
            for proof in target["source_proofs"]:
                if not isinstance(proof, dict):
                    raise ValueError("Ancillary linked occurrence proof is malformed")
                source = proof.get("source_capture_manifest_sha256")
                if (
                    not isinstance(source, str)
                    or source
                    not in controls[digest]["plan"]["source_facet_manifest_sha256s"]
                    or source not in descriptors
                    or descriptors[source]["kind"] != "facet"
                ):
                    raise ValueError("Ancillary linked occurrence predecessor differs")
                entry = next(
                    (
                        row
                        for row in documents[source]["facets"]
                        if row["facet_key"] == proof.get("source_facet_key")
                    ),
                    None,
                )
                if (
                    entry is None
                    or not entry["attempts"]
                    or "body_file" not in entry["attempts"][-1]
                ):
                    raise ValueError(
                        "Ancillary linked occurrence has no source entity declaration"
                    )
                attempt = entry["attempts"][-1]
                role = (
                    entry.get("parent_scope_role")
                    or entry["root_identity"]["exposure_role"]
                )
                relation, pointer = proof.get("relation"), proof.get("json_pointer")
                if (
                    not isinstance(relation, str)
                    or relation not in relations
                    or relations[relation] != (entry["facet"], target["kind"])
                    or not isinstance(pointer, str)
                    or not pointer.startswith("/data/")
                    or "\x00" in pointer
                ):
                    raise ValueError(
                        "Ancillary linked occurrence relation or pointer differs"
                    )
                higher = relation == "source_reported_higher_taxon"
                if higher and not controls[digest]["plan"]["include_higher_taxa"]:
                    raise ValueError(
                        "Ancillary linked occurrence is outside source selection"
                    )
                expected = {
                    "source_capture_manifest_sha256": source,
                    "source_facet_key": entry["facet_key"],
                    "source_receipt_sha256": attempt["receipt_sha256"],
                    "source_body_sha256": descriptors[source]["files"][
                        attempt["body_file"]
                    ]["sha256"],
                    "root_dataset_id": entry["root_identity"]["dataset_id"],
                    "root_identity": entry["root_identity"],
                    "inherited_exposure_role": role,
                    "content_version": entry["content_version"],
                    "api_version": entry["api_version"],
                    "target_kind": target["kind"],
                    "native_id": target["native_id"],
                    "json_pointer": pointer,
                    "relation": relation,
                    "optional_higher_taxon": higher,
                }
                if not _same(proof, expected):
                    raise ValueError(
                        "Ancillary linked occurrence metadata correspondence differs"
                    )
                roles.append(role)
            if target["exposure_role"] != max(roles, key=lambda role: _RANK[role]):
                raise ValueError("Ancillary linked occurrence inherited role differs")


def verify_receipt_metadata(
    record: dict[str, Any],
    request: _Request,
    manifest: dict[str, Any],
    previous: datetime,
) -> datetime:
    """Verify endpoint, transport and clock declarations without an entity buffer."""
    started, finished = _utc(record.get("utc_start")), _utc(record.get("utc_end"))
    if not previous <= started <= finished <= _utc(manifest["capture_utc_end"]):
        raise ValueError("Ancillary source receipt timing correspondence differs")
    expected = _request_record(request, record["utc_start"])
    if not _same({key: record.get(key) for key in expected}, expected):
        raise ValueError("Ancillary source receipt request identity differs")
    rows = manifest["facets"] if "facets" in manifest else manifest["resources"]
    matches = [
        row
        for row in rows
        if any(
            attempt.get("request_name") == request.name for attempt in row["attempts"]
        )
    ]
    if len(matches) != 1:
        raise ValueError("Ancillary source receipt attempt correspondence differs")
    source = matches[0]
    final = source["attempts"][-1].get("request_name") == request.name
    if record.get("terminal_status") == "transport_failure":
        _validate_transport_failure(record, request)
        if final and source.get("terminal_status") != "transport_failure":
            raise ValueError("Ancillary source transport failure assessment differs")
        return finished
    if (
        record.get("final_url") != request.url
        or type(record.get("http_status")) is not int
        or not 100 <= record["http_status"] <= 599
        or type(record.get("body_complete")) is not bool
    ):
        raise ValueError("Ancillary source receipt response identity differs")
    complete = record["http_status"] == 200 and record["body_complete"]
    terminal = "complete_http_200" if complete else "refused_http_response"
    if record.get("terminal_status") != terminal:
        raise ValueError(
            "Ancillary source HTTP status/completeness declaration differs"
        )
    received = (
        "received_complete_unqualified_facet"
        if "facets" in manifest
        else "received_complete_unqualified_linked_resource"
    )
    allowed = (
        {"unavailable_http"}
        if record["http_status"] != 200
        else {"refused_incomplete_body"}
        if not record["body_complete"]
        else {received, "refused_http_receipt", "refused_native_json"}
    )
    if final and (
        not isinstance(source.get("terminal_status"), str)
        or source["terminal_status"] not in allowed
    ):
        raise ValueError("Ancillary source HTTP outcome assessment differs")
    headers = record.get("response_headers")
    if not isinstance(headers, list) or any(
        not isinstance(pair, list)
        or len(pair) != 2
        or any(not isinstance(value, str) for value in pair)
        for pair in headers
    ):
        raise ValueError("Ancillary source response header metadata is malformed")
    return finished
