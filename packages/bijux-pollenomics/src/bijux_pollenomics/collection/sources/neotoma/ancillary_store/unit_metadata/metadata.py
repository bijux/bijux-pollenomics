"""Finite, body-free unit source metadata and archive inventory authentication."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

from ...capture.receipts import (
    _object,
    _read,
    _request_record,
    _safe_root,
    _utc,
    _validate_transport_failure,
)
from ...capture.resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
)
from ...capture.unit_resources.protocol import request_for
from ...capture.unit_resources.replay import _control
from ...client import positive_native_id
from ...resource_catalogue.archive.files import _digest, _member, encoded_json
from ...resource_catalogue.source_projection import _same
from .scope import UnitScopes, prepare_scopes

SCHEMA = "neotoma-unit-metadata-source-archive.v1"
INDEX_SCHEMA = "neotoma-unit-metadata-source-index.v1"
MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000
MAX_METADATA = 16 * 1024 * 1024
_FIELDS = {
    "schema_version",
    "capture_manifest_sha256",
    "original_roster_sha256",
    "context_manifest_sha256",
    "native_archive_manifest_sha256",
    "current_roster_sha256",
    "current_scope_basis_sha256",
    "files",
    "source_bytes",
    "scientific_admission",
    "native_body_copies",
    "historical_snapshot_replaced",
    "metadata_scope",
    "related_resource_graph_complete",
}
_SCOPE = "source_unit_metadata_not_basin_or_vegetation_reference"


def pinned(path: Path, member: dict[str, Any], bound: int) -> bytes:
    path = _safe_root(path)
    if path.stat(follow_symlinks=False).st_size != member["bytes"]:
        raise ValueError("Unit archive physical member size differs")
    raw = _read(path, min(bound, member["bytes"]))
    if sha256(raw).hexdigest() != member["sha256"]:
        raise ValueError("Unit archive member identity differs")
    return raw


@dataclass
class UnitSourceMetadata:
    document: dict[str, Any]
    control: dict[str, Any]
    plan: Any
    limits: NeotomaResourceLimits
    files: dict[str, dict[str, Any]]
    buffers: dict[str, bytes]
    receipts: dict[str, dict[str, Any]]


def source_metadata(directory: Path, expected: str) -> UnitSourceMetadata:
    if not _digest(expected):
        raise ValueError("Unit source requires an independent capture anchor")
    root = _safe_root(directory)
    names = set()
    for path in root.iterdir():
        names.add(path.name)
        if len(names) > MAX_FILES:
            raise ValueError("Unit source exceeds finite file budget")
    sizes = validate_regular_namespace(
        root, names, max_files=MAX_FILES, max_bytes=MAX_BYTES
    )
    document, control, plan, limits, digest = _control(root, expected)
    files, buffers, receipts = {}, {}, {}
    for name, pin in (
        ("capture-manifest.json", digest),
        ("request-plan.json", document["plan_sha256"]),
    ):
        raw = _read(root / name, MAX_METADATA)
        if sha256(raw).hexdigest() != pin:
            raise ValueError("Unit source control buffer changed")
        files["capture/" + name] = {"sha256": pin, "bytes": len(raw)}
        buffers["capture/" + name] = raw
    entries, targets = document["units"], control["units"]
    if (
        not isinstance(entries, list)
        or not isinstance(targets, list)
        or len(entries) != len(targets)
        or len(entries) != len(plan.collection_unit_ids)
        or any(not isinstance(target, dict) for target in targets)
        or [target.get("collection_unit_id") for target in targets]
        != sorted(plan.collection_unit_ids)
    ):
        raise ValueError("Unit source target population differs")
    for unit_id in plan.collection_unit_ids:
        positive_native_id(unit_id)
    for target in targets:
        unit_id = positive_native_id(target.get("collection_unit_id"))
        positive_native_id(target.get("site_id"))
        if (
            target.get("unit_key") != f"speleothem-unit-{unit_id}"
            or target.get("resource_kind") != "speleothem"
        ):
            raise ValueError("Unit source native key or endpoint kind differs")
    previous = _utc(document["capture_utc_start"])
    end = _utc(document["capture_utc_end"])
    if previous > end:
        raise ValueError("Unit source capture timestamps are reversed")
    count = total = 0
    for entry, target in zip(entries, targets, strict=True):
        if (
            not isinstance(entry, dict)
            or entry.get("unit_key") != target["unit_key"]
            or not _same(entry.get("identity"), target)
            or entry.get("content_version") != "current"
            or entry.get("api_version") != "v2.0"
            or entry.get("scientific_admission") != "not_asserted"
            or not isinstance(entry.get("attempts"), list)
        ):
            raise ValueError("Unit source owner, epoch or attempt identity differs")
        assessed: dict[str, Any] | None = None
        if target.get("exposure_role") not in DEVELOPMENT_ROLES:
            if entry["attempts"]:
                raise ValueError("Original protected unit scope forbids body access")
            assessed = {
                "terminal_status": "not_attempted_exposure_role",
                "reason": target["exposure_role"],
            }
        elif not entry["attempts"]:
            assessed = {"terminal_status": "not_attempted_budget"}
        for ordinal, ref in enumerate(entry["attempts"], 1):
            count += 1
            request = request_for(target, ordinal)
            name = request.name + ".receipt.json"
            if (
                not isinstance(ref, dict)
                or ref.get("request_name") != request.name
                or ref.get("receipt_file") != name
                or not _digest(ref.get("receipt_sha256"))
            ):
                raise ValueError("Unit source receipt reference differs")
            raw = _read(root / name, 1024 * 1024)
            if sha256(raw).hexdigest() != ref["receipt_sha256"]:
                raise ValueError("Unit source receipt buffer differs")
            files["capture/" + name] = {
                "sha256": ref["receipt_sha256"],
                "bytes": len(raw),
            }
            buffers["capture/" + name] = raw
            record = _object(raw)
            receipts[request.name] = record
            baseline = _request_record(request, record.get("utc_start", ""))
            if not _same({key: record.get(key) for key in baseline}, baseline):
                raise ValueError("Unit source receipt endpoint or transport differs")
            start, finish = _utc(record.get("utc_start")), _utc(record.get("utc_end"))
            if not previous <= start <= finish <= end:
                raise ValueError("Unit source receipt epoch differs")
            previous = finish
            if record.get("terminal_status") == "transport_failure":
                if set(ref) != {
                    "request_name",
                    "receipt_file",
                    "receipt_sha256",
                } or set(record) != set(baseline) | {
                    "utc_end",
                    "terminal_status",
                    "error",
                    "body_complete",
                }:
                    raise ValueError("Unit source transport failure fields differ")
                _validate_transport_failure(record, request)
                assessed = {
                    "terminal_status": "transport_failure",
                    "reason": record["error"],
                }
            else:
                body_name = request.name + ".body"
                status, complete, size = (
                    record.get("http_status"),
                    record.get("body_complete"),
                    record.get("retained_body_bytes"),
                )
                if (
                    set(ref)
                    != {"request_name", "receipt_file", "receipt_sha256", "body_file"}
                    or set(record)
                    != set(baseline)
                    | {
                        "utc_end",
                        "final_url",
                        "http_status",
                        "response_headers",
                        "body_file",
                        "body_complete",
                        "retained_body_bytes",
                        "retained_body_sha256",
                        "terminal_status",
                    }
                    or ref.get("body_file") != body_name
                    or record.get("body_file") != body_name
                    or record.get("final_url") != request.url
                    or type(status) is not int
                    or not 100 <= status <= 599
                    or type(complete) is not bool
                    or type(size) is not int
                    or size < 0
                    or sizes.get(body_name) != size
                    or not _digest(record.get("retained_body_sha256"))
                    or record.get("terminal_status")
                    != (
                        "complete_http_200"
                        if status == 200 and complete
                        else "refused_http_response"
                    )
                ):
                    raise ValueError(
                        "Unit source HTTP receipt or body declaration differs"
                    )
                headers = record.get("response_headers")
                if not isinstance(headers, list) or any(
                    not isinstance(pair, list)
                    or len(pair) != 2
                    or any(not isinstance(value, str) for value in pair)
                    for pair in headers
                ):
                    raise ValueError("Unit source response headers are malformed")
                files["capture/" + body_name] = {
                    "sha256": record["retained_body_sha256"],
                    "bytes": size,
                }
                total += size
                assessed = (
                    {
                        "terminal_status": "unavailable_http",
                        "http_status": status,
                        "absence_certified": False,
                    }
                    if status != 200
                    else {
                        "terminal_status": "refused_incomplete_body",
                        "reason": "Incomplete or bounded HTTP entity",
                    }
                    if not complete
                    else None
                )
                if assessed is None:
                    declared = entry.get("terminal_status")
                    if declared == "received_complete_unqualified_unit_resource":
                        assessed = {
                            "terminal_status": declared,
                            "summary": {
                                "schema_qualified": False,
                                "payload_owner_status": "not_established",
                                "endpoint_owner_status": "authenticated_request_collection_unit",
                                "absence_certified": False,
                                "units_interpreted": False,
                            },
                        }
                    elif declared in {
                        "refused_http_receipt",
                        "refused_native_json",
                    } and isinstance(entry.get("reason"), str):
                        assessed = {
                            "terminal_status": declared,
                            "reason": entry["reason"],
                        }
                    else:
                        raise ValueError("Unit source complete HTTP assessment differs")
            if ordinal < len(entry["attempts"]) and not (
                record.get("terminal_status") == "transport_failure"
                or record.get("http_status") == 429
                or type(record.get("http_status")) is int
                and 500 <= record["http_status"] <= 599
            ):
                raise ValueError("Unit source retried a nontransient response")
        baseline_fields = {
            "unit_key",
            "identity",
            "content_version",
            "api_version",
            "attempts",
            "scientific_admission",
        }
        if (
            assessed is None
            or set(entry) != baseline_fields | set(assessed)
            or not _same({key: entry.get(key) for key in assessed}, assessed)
        ):
            raise ValueError("Unit source declared assessment fields differ")
    if (
        type(document["request_count"]) is not int
        or type(document["response_bytes"]) is not int
        or document["request_count"] != count
        or document["response_bytes"] != total
        or not _same(
            document["partitions"],
            dict(Counter(row["terminal_status"] for row in entries)),
        )
        or {"capture/" + name for name in names} != set(files)
    ):
        raise ValueError("Unit source file or request population differs")
    return UnitSourceMetadata(document, control, plan, limits, files, buffers, receipts)


def source_index(source: UnitSourceMetadata, scopes: UnitScopes) -> dict[str, Any]:
    rows = []
    for offset, entry in enumerate(source.document["units"]):
        attempts = []
        for ref in entry["attempts"]:
            record = source.receipts[ref["request_name"]]
            attempts.append(
                {
                    **ref,
                    **{
                        key: record[key]
                        for key in (
                            "http_status",
                            "body_complete",
                            "utc_start",
                            "utc_end",
                        )
                        if key in record
                    },
                    **(
                        {
                            "body_sha256": record["retained_body_sha256"],
                            "body_bytes": record["retained_body_bytes"],
                        }
                        if "body_file" in ref
                        else {}
                    ),
                }
            )
        rows.append(
            {
                "unit_key": entry["unit_key"],
                "source_entry_pointer": f"/units/{offset}",
                "content_version": entry["content_version"],
                "api_version": entry["api_version"],
                "terminal_status": entry["terminal_status"],
                "scope": scopes.account(entry["identity"]["collection_unit_id"]),
                "attempts": attempts,
                "scientific_admission": "not_asserted",
            }
        )
    return {
        "schema_version": INDEX_SCHEMA,
        "units": rows,
        "capture_utc_start": source.document["capture_utc_start"],
        "capture_utc_end": source.document["capture_utc_end"],
        "snapshot_consistency": source.document["snapshot_consistency"],
        "request_count": source.document["request_count"],
        "response_bytes": source.document["response_bytes"],
        "partitions": source.document["partitions"],
        "scientific_admission": "not_asserted",
    }


@dataclass(frozen=True)
class UnitMetadataInventory:
    root: Path
    manifest: dict[str, Any]
    index: dict[str, Any]
    source: UnitSourceMetadata
    scopes: UnitScopes
    source_entity_bodies_verified: bool = False
    source_assessments_replayed: bool = False


def read_neotoma_unit_metadata_inventory(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    expected_native_archive_sha256: str,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> UnitMetadataInventory:
    root = _safe_root(directory)
    raw = _read(root / "manifest.json", MAX_METADATA)
    if (
        not _digest(expected_manifest_sha256)
        or sha256(raw).hexdigest() != expected_manifest_sha256
    ):
        raise ValueError("Unit archive manifest identity differs")
    manifest = _object(raw)
    if (
        set(manifest) != _FIELDS
        or manifest["schema_version"] != SCHEMA
        or manifest["context_manifest_sha256"] != expected_context_sha256
        or manifest["native_archive_manifest_sha256"] != expected_native_archive_sha256
        or manifest["scientific_admission"] != "not_asserted"
        or type(manifest["native_body_copies"]) is not int
        or manifest["native_body_copies"] != 0
        or manifest["historical_snapshot_replaced"] is not False
        or manifest["related_resource_graph_complete"] is not False
        or manifest["metadata_scope"] != _SCOPE
        or not isinstance(manifest["files"], dict)
        or type(manifest["source_bytes"]) is not int
    ):
        raise ValueError("Unit archive anchors, schema or source-only claims differ")
    total = 0
    for name, member in manifest["files"].items():
        _member(name)
        if (
            name == "manifest.json"
            or not isinstance(member, dict)
            or set(member) != {"bytes", "sha256"}
            or type(member.get("bytes")) is not int
            or not 0 <= member["bytes"] <= MAX_BYTES
            or not _digest(member.get("sha256"))
        ):
            raise ValueError("Unit archive member declaration is malformed")
        total += member["bytes"]
    if total != manifest["source_bytes"] or total + len(raw) > MAX_BYTES:
        raise ValueError("Unit archive byte declarations exceed finite budget")
    sizes = validate_regular_namespace(
        root,
        {"manifest.json", *manifest["files"]},
        max_files=MAX_FILES,
        max_bytes=MAX_BYTES,
    )
    if any(
        sizes[name] != member["bytes"] for name, member in manifest["files"].items()
    ):
        raise ValueError("Unit archive member sizes differ")
    source = source_metadata(root / "capture", manifest["capture_manifest_sha256"])
    original = manifest["original_roster_sha256"]
    relative = f"rosters/{original}.json"
    if (
        original != source.plan.roster_sha256
        or relative not in manifest["files"]
        or manifest["files"][relative]["sha256"] != original
    ):
        raise ValueError("Unit archive original roster identity differs")
    pinned(root / relative, manifest["files"][relative], MAX_METADATA)
    if set(manifest["files"]) != {*source.files, relative, "index.json"} or any(
        not _same(manifest["files"][name], member)
        for name, member in source.files.items()
    ):
        raise ValueError("Unit archive source closure differs")
    scopes = prepare_scopes(
        source.plan,
        source.control,
        root / relative,
        source.limits,
        context_directory=context_directory,
        expected_context_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
        expected_native_archive_sha256=expected_native_archive_sha256,
        limits=limits,
    )
    if (
        manifest["current_roster_sha256"] != scopes.current_roster_sha256
        or manifest["current_scope_basis_sha256"] != scopes.current_basis_sha256
    ):
        raise ValueError("Unit archive current scope binding differs")
    index = source_index(source, scopes)
    actual = pinned(root / "index.json", manifest["files"]["index.json"], MAX_METADATA)
    if actual != encoded_json(index):
        raise ValueError("Unit archive derived index differs")
    return UnitMetadataInventory(root, manifest, index, source, scopes)
