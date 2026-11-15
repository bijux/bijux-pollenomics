"""Bound literal capture closures before full source replay and compact indexing."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

from ...capture.facets.models import FACET_SCHEMA, SCOPED_FACET_SCHEMA
from ...capture.facets.protocol import facet_identity
from ...capture.facets.protocol import plan_from_json as facet_plan
from ...capture.facets.protocol import request_for as facet_request
from ...capture.facets.replay import _control as facet_control
from ...capture.facets.scope import authenticate_parent_scope
from ...capture.linked_resources.models import LINKED_SCHEMA
from ...capture.linked_resources.protocol import request_for as linked_request
from ...capture.linked_resources.replay import _control as linked_control
from ...capture.parent_scope import _roster
from ...capture.receipts import _object, _read, _safe_root, _utc
from ...capture.resources.models import DEVELOPMENT_ROLES
from ...client import positive_native_id
from ...resource_catalogue.archive.files import _digest, encoded_json
from ...resource_catalogue.source_projection import _same
from ..context.validation import NeotomaAncillaryContext, load_neotoma_ancillary_context
from .models import (
    CAPSULE_SCHEMA,
    CapsuleMetadata,
    NeotomaAncillaryCapsuleInventory,
    compact_index,
    index_buffers,
    verify_linked_metadata_sources,
    verify_metadata_population,
    verify_receipt_metadata,
)

MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000
MAX_MEMBER_BYTES = 32 * 1024 * 1024 + 1
MAX_METADATA_BYTES = 16 * 1024 * 1024
_FIELDS = {
    "schema_version",
    "context_manifest_sha256",
    "native_archive_manifest_sha256",
    "captures",
    "predecessor_facets",
    "files",
    "source_bytes",
    "scientific_admission",
    "native_body_copies",
    "historical_snapshot_replaced",
}


def _pinned(path: Path, digest: object, bound: int) -> tuple[bytes, dict[str, Any]]:
    raw = _read(path, bound)
    if not _digest(digest) or sha256(raw).hexdigest() != digest:
        raise ValueError("Ancillary capsule source identity differs")
    return raw, _object(raw)


def _name(value: Any) -> str:
    if (
        not isinstance(value, str)
        or Path(value).name != value
        or value in {"", ".", ".."}
        or "\\" in value
    ):
        raise ValueError("Ancillary capture member is not a portable flat name")
    return value


def _physical(
    root: Path, remaining_bytes: int, remaining_files: int
) -> tuple[int, int]:
    if remaining_bytes <= 0 or remaining_files <= 0:
        raise ValueError("Ancillary capsule exceeds finite input/publication budget")
    root = _safe_root(root)
    names: set[str] = set()
    for path in root.iterdir():
        names.add(path.name)
        if len(names) > remaining_files:
            raise ValueError("Ancillary capsule exceeds finite file budget")
    sizes = validate_regular_namespace(
        root, names, max_bytes=remaining_bytes, max_files=remaining_files
    )
    return sum(sizes.values()), len(sizes)


def _capture(
    root: Path, digest: str, kind: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = _safe_root(root)
    raw, manifest = _pinned(root / "capture-manifest.json", digest, MAX_METADATA_BYTES)
    schema = manifest.get("schema_version")
    if (
        not isinstance(schema, str)
        or (kind == "facet" and schema not in {FACET_SCHEMA, SCOPED_FACET_SCHEMA})
        or (kind == "linked" and schema != LINKED_SCHEMA)
        or kind not in {"facet", "linked"}
    ):
        raise ValueError("Ancillary capsule capture kind or native schema differs")
    control_raw, control = _pinned(
        root / "request-plan.json", manifest.get("plan_sha256"), MAX_METADATA_BYTES
    )
    resources = facet_plan(control)[0].resources if kind == "facet" else ()
    (facet_control if kind == "facet" else linked_control)(root, digest)
    if (
        not {
            "request_count",
            "response_bytes",
            "partitions",
            "capture_utc_start",
            "capture_utc_end",
            "snapshot_consistency",
        }
        <= manifest.keys()
        or "policy_sources" not in control
    ):
        raise ValueError("Ancillary capsule source metadata is incomplete")
    files = {
        "capture-manifest.json": {"sha256": digest, "bytes": len(raw)},
        "request-plan.json": {
            "sha256": sha256(control_raw).hexdigest(),
            "bytes": len(control_raw),
        },
    }
    if schema == SCOPED_FACET_SCHEMA:
        proof = control.get("parent_scope")
        if not isinstance(proof, dict) or proof.get("file") != "parent-scope.json":
            raise ValueError("Ancillary capsule parent scope reference is malformed")
        proof_raw, _ = _pinned(
            root / "parent-scope.json", proof.get("sha256"), MAX_METADATA_BYTES
        )
        files["parent-scope.json"] = {
            "sha256": sha256(proof_raw).hexdigest(),
            "bytes": len(proof_raw),
        }
    entries = manifest.get("facets" if kind == "facet" else "resources")
    if not isinstance(entries, list):
        raise ValueError("Ancillary capsule source observation population is malformed")
    previous = _utc(manifest.get("capture_utc_start"))
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("attempts"), list):
            raise ValueError("Ancillary capsule source attempts are malformed")
        owner = entry.get("root_identity" if kind == "facet" else "identity")
        if not isinstance(owner, dict):
            raise ValueError("Ancillary capsule source owner is malformed")
        if entry["attempts"] and (
            not isinstance(owner.get("exposure_role"), str)
            or owner["exposure_role"] not in DEVELOPMENT_ROLES
            or kind == "facet"
            and schema == SCOPED_FACET_SCHEMA
            and (
                not isinstance(entry.get("parent_scope_role"), str)
                or entry["parent_scope_role"] not in DEVELOPMENT_ROLES
            )
        ):
            raise ValueError("Ancillary capsule exposure role forbids attempt access")
        for number, attempt in enumerate(entry["attempts"], 1):
            if not isinstance(attempt, dict):
                raise ValueError("Ancillary capsule attempt reference is malformed")
            name = _name(attempt.get("receipt_file"))
            request_name = _name(attempt.get("request_name"))
            if name != f"{request_name}.receipt.json":
                raise ValueError(
                    "Ancillary capsule receipt name differs from its attempt"
                )
            content, receipt = _pinned(
                root / name, attempt.get("receipt_sha256"), 1024 * 1024
            )
            if kind == "facet":
                resource = next(
                    (
                        row
                        for row in resources
                        if row.dataset_id == owner.get("dataset_id")
                    ),
                    None,
                )
                if resource is None:
                    raise ValueError(
                        "Ancillary source receipt has no declared native root"
                    )
                request = facet_request(resource, entry["facet"], number)
            else:
                if owner.get("kind") not in ("contact", "publication", "taxon"):
                    raise ValueError("Ancillary linked receipt native kind differs")
                positive_native_id(owner.get("native_id"))
                request = linked_request(owner, number)
            previous = verify_receipt_metadata(receipt, request, manifest, previous)
            if name in files:
                raise ValueError("Ancillary capsule source member is duplicated")
            files[name] = {"sha256": sha256(content).hexdigest(), "bytes": len(content)}
            if "body_file" in attempt:
                name = _name(attempt["body_file"])
                if (
                    name != f"{request_name}.body"
                    or name != receipt.get("body_file")
                    or name in files
                    or not _digest(receipt.get("retained_body_sha256"))
                    or type(receipt.get("retained_body_bytes")) is not int
                    or not 0 <= receipt["retained_body_bytes"] <= MAX_MEMBER_BYTES
                ):
                    raise ValueError(
                        "Ancillary capsule source entity identity is malformed"
                    )
                files[name] = {
                    "sha256": receipt["retained_body_sha256"],
                    "bytes": receipt["retained_body_bytes"],
                }
    sizes = validate_regular_namespace(
        root, set(files), max_bytes=MAX_BYTES, max_files=MAX_FILES
    )
    if any(sizes[name] != member["bytes"] for name, member in files.items()):
        raise ValueError("Ancillary capsule source physical size differs")
    return (
        {"kind": kind, "native_schema_version": schema, "files": files},
        manifest,
        control,
    )


def _legacy_roots(control: dict[str, Any], context: NeotomaAncillaryContext) -> None:
    plan = control["plan"]
    digest = plan["roster_sha256"]
    if digest not in context.legacy_rosters:
        raise ValueError("Ancillary legacy capture lacks its original roster identity")
    roster = _roster(context.legacy_rosters[digest], digest)
    rows = {row["dataset_id"]: row for row in roster["resources"]}
    for resource in plan["resources"]:
        row = rows.get(resource["dataset_id"])
        if row is None:
            raise ValueError("Ancillary legacy dataset is absent from original roster")
        locator = row.get("metadata_locator")
        if (
            not isinstance(locator, dict)
            or not _digest(locator.get("response_sha256"))
            or not isinstance(locator.get("json_pointer"), str)
        ):
            raise ValueError("Ancillary legacy original source locator is malformed")
        expected = {
            key: row[key]
            for key in (
                "dataset_id",
                "site_id",
                "collection_unit_id",
                "dataset_type",
                "database",
            )
        }
        expected.update(
            exposure_role=row["exposure_roles"]["current"],
            metadata_sha256=locator["response_sha256"],
            metadata_pointer=locator["json_pointer"],
        )
        if not _same({key: resource.get(key) for key in expected}, expected):
            raise ValueError(
                "Ancillary legacy native owner/role/source locator differs"
            )


def prepare_capsule_metadata(
    *,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    facet_captures: Mapping[str, Path],
    linked_captures: Mapping[str, Path] | None = None,
    predecessor_facets: Mapping[str, Path] | None = None,
    max_bytes: int = MAX_BYTES,
    max_files: int = MAX_FILES,
) -> CapsuleMetadata:
    """Preflight exact consumed closures before any full source/body replay."""
    context = load_neotoma_ancillary_context(
        context_directory,
        expected_manifest_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
    )
    if (
        not isinstance(facet_captures, Mapping)
        or linked_captures is not None
        and not isinstance(linked_captures, Mapping)
    ):
        raise ValueError("Ancillary capsule source resolver mapping is malformed")
    linked_captures = linked_captures or {}
    if (
        not facet_captures
        and not linked_captures
        or set(facet_captures) & set(linked_captures)
        or len(facet_captures) + len(linked_captures) > max_files
    ):
        raise ValueError("Ancillary capsule capture population is empty or ambiguous")
    physical_bytes = physical_files = 0
    for root in (*facet_captures.values(), *linked_captures.values()):
        size, count = _physical(
            root, max_bytes - physical_bytes, max_files - physical_files
        )
        physical_bytes += size
        physical_files += count
    captures, documents, controls, paths = {}, {}, {}, {}
    for kind, sources in (("facet", facet_captures), ("linked", linked_captures)):
        for digest, root in sorted(sources.items()):
            if not _digest(digest):
                raise ValueError("Ancillary capsule capture identity is malformed")
            descriptor, document, control = _capture(root, digest, kind)
            captures[digest], documents[digest], controls[digest] = (
                descriptor,
                document,
                control,
            )
            for name, member in descriptor["files"].items():
                paths[f"captures/{digest}/{name}"] = (
                    _safe_root(root) / name,
                    member["bytes"],
                )
    all_descriptors = dict(captures)
    required = set()
    for digest in linked_captures:
        references = controls[digest]["plan"].get("source_facet_manifest_sha256s")
        if not isinstance(references, list) or not all(
            _digest(value) for value in references
        ):
            raise ValueError("Ancillary linked predecessor declarations are malformed")
        required.update(references)
    external = required - set(facet_captures)
    if not external <= set(predecessor_facets or {}):
        raise ValueError("Ancillary linked predecessor resolver is incomplete")
    facets = dict(facet_captures)
    total = sum(size for _, size in paths.values())
    count = len(paths)
    for digest in sorted(external):
        root = (predecessor_facets or {})[digest]
        size, files_count = _physical(
            root, max_bytes - physical_bytes, max_files - physical_files
        )
        physical_bytes += size
        physical_files += files_count
        descriptor, document, control = _capture(root, digest, "facet")
        total += sum(member["bytes"] for member in descriptor["files"].values())
        count += len(descriptor["files"])
        facets[digest], documents[digest], controls[digest] = root, document, control
        all_descriptors[digest] = descriptor
    try:
        index = compact_index(captures, documents, controls)
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError(
            "Ancillary capsule source occurrence metadata is malformed"
        ) from error
    buffers = index_buffers(index)
    files = {
        relative: member
        for digest, descriptor in captures.items()
        for name, member in descriptor["files"].items()
        for relative in [f"captures/{digest}/{name}"]
    }
    files.update(
        {
            name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
            for name, raw in buffers.items()
        }
    )
    manifest = {
        "schema_version": CAPSULE_SCHEMA,
        "context_manifest_sha256": expected_context_sha256,
        "native_archive_manifest_sha256": context.manifest["native_archive"][
            "manifest_sha256"
        ],
        "captures": captures,
        "predecessor_facets": sorted(external),
        "files": files,
        "source_bytes": sum(member["bytes"] for member in files.values()),
        "scientific_admission": "not_asserted",
        "native_body_copies": 0,
        "historical_snapshot_replaced": False,
    }
    if (
        count + len(buffers) + 1 > max_files
        or total + sum(map(len, buffers.values())) + len(encoded_json(manifest))
        > max_bytes
        or len(encoded_json(manifest)) > MAX_METADATA_BYTES
    ):
        raise ValueError("Ancillary capsule exceeds finite input/publication budget")
    for digest, root in sorted(facets.items()):
        plan, _ = facet_plan(controls[digest])
        parents = {}
        if documents[digest]["schema_version"] == FACET_SCHEMA:
            _legacy_roots(controls[digest], context)
        else:
            proof = authenticate_parent_scope(
                root, controls[digest], plan, context.current_scope_inputs
            )
            parents = {
                row["dataset_id"]: row["effective_scope_role"]
                for row in proof["parents"]
            }
        expected = [
            facet_identity(resource, facet)
            for resource in sorted(plan.resources, key=lambda row: row.dataset_id)
            for facet in plan.facets
        ]
        entries = documents[digest]["facets"]
        if len(entries) != len(expected) or any(
            not _same({key: entry.get(key) for key in identity}, identity)
            for entry, identity in zip(entries, expected, strict=True)
        ):
            raise ValueError(
                "Ancillary source facet native owner correspondence differs"
            )
        if parents and any(
            entry.get("parent_scope_role")
            != parents[entry["root_identity"]["dataset_id"]]
            for entry in entries
        ):
            raise ValueError("Ancillary source facet parent role differs")
    for digest, descriptor in all_descriptors.items():
        verify_metadata_population(descriptor, documents[digest], controls[digest])
    verify_linked_metadata_sources(
        documents, controls, all_descriptors, linked_captures
    )
    return CapsuleMetadata(
        manifest,
        paths,
        buffers,
        index,
        context,
        facets,
        dict(linked_captures),
        documents,
        controls,
    )


def read_neotoma_ancillary_capsule_inventory(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    predecessor_facets: Mapping[str, Path] | None = None,
) -> NeotomaAncillaryCapsuleInventory:
    """Authenticate metadata and declarations; numerical entity hashes stay unverified."""
    root = _safe_root(directory)
    raw, manifest = _pinned(
        root / "manifest.json", expected_manifest_sha256, MAX_METADATA_BYTES
    )
    if (
        set(manifest) != _FIELDS
        or manifest.get("schema_version") != CAPSULE_SCHEMA
        or not isinstance(manifest.get("files"), dict)
        or not isinstance(manifest.get("captures"), dict)
        or not _digest(manifest.get("context_manifest_sha256"))
    ):
        raise ValueError("Ancillary capsule manifest fields or schema differ")
    declared = 0
    for member in manifest["files"].values():
        if (
            not isinstance(member, dict)
            or set(member) != {"sha256", "bytes"}
            or not _digest(member.get("sha256"))
            or type(member.get("bytes")) is not int
            or not 0 <= member["bytes"] <= MAX_MEMBER_BYTES
        ):
            raise ValueError("Ancillary capsule member identity is malformed")
        declared += member["bytes"]
    if (
        type(manifest.get("source_bytes")) is not int
        or declared != manifest["source_bytes"]
        or declared + len(raw) > MAX_BYTES
    ):
        raise ValueError("Ancillary capsule declared byte population differs")
    sizes = validate_regular_namespace(
        root,
        {"manifest.json", *manifest["files"]},
        max_files=MAX_FILES,
        max_bytes=MAX_BYTES,
    )
    if any(
        sizes[name] != member["bytes"] for name, member in manifest["files"].items()
    ):
        raise ValueError("Ancillary capsule physical size differs")
    facets: dict[str, Path] = {}
    linked: dict[str, Path] = {}
    for digest, descriptor in manifest["captures"].items():
        if (
            not _digest(digest)
            or not isinstance(descriptor, dict)
            or not isinstance(descriptor.get("kind"), str)
            or descriptor["kind"] not in {"facet", "linked"}
        ):
            raise ValueError("Ancillary capsule capture kind or identity differs")
        (facets if descriptor["kind"] == "facet" else linked)[digest] = (
            root / "captures" / digest
        )
    prepared = prepare_capsule_metadata(
        context_directory=context_directory,
        expected_context_sha256=manifest["context_manifest_sha256"],
        native_archive_directory=native_archive_directory,
        facet_captures=facets,
        linked_captures=linked,
        predecessor_facets=predecessor_facets,
    )
    if not _same(prepared.manifest, manifest):
        raise ValueError("Ancillary capsule source identity or compact claims differ")
    for relative, member in manifest["files"].items():
        if relative.endswith(".body"):
            continue
        content = _read(root / relative, member["bytes"])
        if (
            sha256(content).hexdigest() != member["sha256"]
            or len(content) != member["bytes"]
            or relative in prepared.buffers
            and content != prepared.buffers[relative]
        ):
            raise ValueError("Ancillary capsule member buffer or source index differs")
    return NeotomaAncillaryCapsuleInventory(
        root, manifest, prepared.index, facets, linked
    )
