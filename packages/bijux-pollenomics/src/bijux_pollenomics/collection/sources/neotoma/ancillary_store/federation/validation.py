"""Authenticate a declared capsule view and derive current-use coverage from metadata."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

from ...capture.facets.models import NeotomaFacetPlan
from ...capture.facets.scope import prepare_facet_parent_scope
from ...capture.parent_scope import _roster
from ...capture.receipts import _object, _read, _safe_root
from ...capture.resources.models import NeotomaResourceSpec
from ...resource_catalogue.archive.files import _digest, _member, encoded_json
from ...resource_catalogue.source_projection import _same
from ..capsule import (
    load_neotoma_ancillary_capsule,
    read_neotoma_ancillary_capsule_inventory,
)
from ..capsule.models import CAPSULE_SCHEMA
from ..context import load_neotoma_ancillary_context
from .models import (
    FACETS,
    SCHEMA,
    FederationMetadata,
    NeotomaAncillaryFederation,
    assemble_view,
    metadata_buffers,
)

MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000
MAX_METADATA_BYTES = 16 * 1024 * 1024
_FIELDS = {
    "schema_version",
    "context_manifest_sha256",
    "native_archive_manifest_sha256",
    "current_roster_sha256",
    "current_use_parent_obligations_sha256",
    "current_use_parent_obligations",
    "declared_facets",
    "capsule_manifest_sha256s",
    "capsule_captures",
    "files",
    "source_bytes",
    "summary",
    "integrity_scope",
    "entity_body_hashes_verified",
    "source_assessments_replayed",
    "scientific_admission",
    "payload_copies",
    "original_preget_scope_reconstructed",
    "related_resource_scope",
    "related_resource_graph_complete",
}


def _pinned(path: Path, digest: str, bound: int) -> tuple[bytes, dict[str, Any]]:
    raw = _read(path, bound)
    if not _digest(digest) or sha256(raw).hexdigest() != digest:
        raise ValueError("Federation metadata input identity differs")
    return raw, _object(raw)


def _capsules(
    sources: Mapping[str, Path], context: str
) -> tuple[dict[str, Path], dict[str, dict[str, Path]], dict[str, list[str]]]:
    """Resolve unique capture owners and exact predecessor closure without bodies."""
    if not isinstance(sources, Mapping) or len(sources) > MAX_FILES:
        raise ValueError("Federation capsule resolver population is malformed")
    roots, documents, owners = {}, {}, {}
    total = 0
    for digest, directory in sorted(sources.items()):
        if not _digest(digest):
            raise ValueError("Federation capsule identity is malformed")
        root = _safe_root(directory)
        raw, manifest = _pinned(
            root / "manifest.json", digest, min(MAX_METADATA_BYTES, MAX_BYTES - total)
        )
        if (
            manifest.get("schema_version") != CAPSULE_SCHEMA
            or manifest.get("context_manifest_sha256") != context
            or not isinstance(manifest.get("captures"), dict)
            or not isinstance(manifest.get("files"), dict)
        ):
            raise ValueError("Federation capsule schema or context differs")
        total += len(raw)
        for name, member in manifest["files"].items():
            _member(name)
            if (
                not isinstance(member, dict)
                or type(member.get("bytes")) is not int
                or member["bytes"] < 0
                or not _digest(member.get("sha256"))
            ):
                raise ValueError("Federation capsule member declaration is malformed")
            if not name.endswith(".body"):
                total += member["bytes"]
        if total > MAX_BYTES:
            raise ValueError("Federation capsule metadata exceeds finite input budget")
        for capture, descriptor in manifest["captures"].items():
            if (
                not _digest(capture)
                or not isinstance(descriptor, dict)
                or descriptor.get("kind") not in ("facet", "linked")
            ):
                raise ValueError("Federation capsule capture identity is malformed")
            if capture in owners:
                raise ValueError(
                    "Federation capture owner is duplicated across capsules"
                )
            owners[capture] = (root / "captures" / capture, descriptor["kind"])
        roots[digest], documents[digest] = root, manifest
    predecessors = {}
    for digest, manifest in documents.items():
        required = manifest.get("predecessor_facets")
        if (
            not isinstance(required, list)
            or any(not _digest(pin) for pin in required)
            or len(set(required)) != len(required)
            or any(
                not _digest(pin) or pin not in owners or owners[pin][1] != "facet"
                for pin in required
            )
        ):
            raise ValueError("Federation predecessor facet owner is unavailable")
        predecessors[digest] = {pin: owners[pin][0] for pin in required}
    return (
        roots,
        predecessors,
        {pin: sorted(document["captures"]) for pin, document in documents.items()},
    )


def prepare_federation(
    *,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
) -> FederationMetadata:
    """Read outcome-free parent metadata and capsule declarations, never entities."""
    context = load_neotoma_ancillary_context(
        context_directory,
        expected_manifest_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
    )
    roster_pin, scope = next(iter(context.current_scope_inputs.items()))
    roster = _roster(scope.roster_path, roster_pin)
    resources = tuple(
        NeotomaResourceSpec(
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
        for row in roster["resources"]
    )
    proof = prepare_facet_parent_scope(
        NeotomaFacetPlan(resources, roster_pin, ("taxa",)), scope
    )
    roles = {row["dataset_id"]: row["effective_scope_role"] for row in proof["parents"]}
    role_bytes = encoded_json(proof)
    role_pin = sha256(role_bytes).hexdigest()
    roots, predecessors, capture_ids = _capsules(
        capsule_sources, expected_context_sha256
    )
    indexes, attempts = {}, {}
    for digest, root in roots.items():
        inventory = read_neotoma_ancillary_capsule_inventory(
            root,
            expected_manifest_sha256=digest,
            context_directory=context_directory,
            native_archive_directory=native_archive_directory,
            predecessor_facets=predecessors[digest],
        )
        indexes[digest] = inventory.index
        for row in inventory.index["observations"]:
            capture = row["source_capture_manifest_sha256"]
            enriched = []
            for attempt in row["attempts"]:
                relative = f"captures/{capture}/{attempt['receipt_file']}"
                member = inventory.manifest["files"][relative]
                _, receipt = _pinned(root / relative, member["sha256"], member["bytes"])
                enriched.append(
                    {
                        **attempt,
                        **{
                            key: receipt[key]
                            for key in (
                                "http_status",
                                "body_complete",
                                "terminal_status",
                                "utc_start",
                                "utc_end",
                                "tls_mode",
                                "requested_url",
                            )
                            if key in receipt
                        },
                    }
                )
            attempts[capture, row["source_entry_pointer"]] = enriched
    slots, observations, occurrences, summary = assemble_view(
        roster, roles, indexes, attempts
    )
    buffers = metadata_buffers(slots, observations, occurrences, summary)
    buffers["scope/current-parent-proof.json"] = role_bytes
    manifest = {
        "schema_version": SCHEMA,
        "context_manifest_sha256": expected_context_sha256,
        "native_archive_manifest_sha256": context.manifest["native_archive"][
            "manifest_sha256"
        ],
        "current_roster_sha256": roster_pin,
        "current_use_parent_obligations_sha256": role_pin,
        "current_use_parent_obligations": {
            "path": "scope/current-parent-proof.json",
            "sha256": role_pin,
            "bytes": len(role_bytes),
            "scope": "current_use_metadata_only_not_historical_preget",
        },
        "declared_facets": list(FACETS),
        "capsule_manifest_sha256s": sorted(roots),
        "capsule_captures": capture_ids,
        "files": {
            name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
            for name, raw in buffers.items()
        },
        "source_bytes": sum(map(len, buffers.values())),
        "summary": summary,
        "integrity_scope": "current_context_and_capsule_metadata",
        "entity_body_hashes_verified": False,
        "source_assessments_replayed": False,
        "scientific_admission": "not_asserted",
        "payload_copies": 0,
        "original_preget_scope_reconstructed": False,
        "related_resource_scope": "captured_occurrences_and_current_native_parent_obligations",
        "related_resource_graph_complete": False,
    }
    if (
        len(buffers) + 1 > MAX_FILES
        or manifest["source_bytes"] + len(encoded_json(manifest)) > MAX_BYTES
        or len(encoded_json(manifest)) > MAX_METADATA_BYTES
    ):
        raise ValueError("Federation output exceeds finite publication budget")
    view = NeotomaAncillaryFederation(
        manifest, summary, slots, observations, occurrences
    )
    return FederationMetadata(manifest, buffers, view, roots, predecessors)


def _load(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
) -> FederationMetadata:
    root = _safe_root(directory)
    raw, manifest = _pinned(
        root / "manifest.json", expected_manifest_sha256, MAX_METADATA_BYTES
    )
    if (
        set(manifest) != _FIELDS
        or manifest.get("schema_version") != SCHEMA
        or not isinstance(manifest.get("files"), dict)
        or not isinstance(manifest.get("capsule_manifest_sha256s"), list)
        or not _digest(manifest.get("context_manifest_sha256"))
    ):
        raise ValueError("Federation schema or source identity fields differ")
    total = 0
    for name, member in manifest["files"].items():
        _member(name)
        if (
            not isinstance(member, dict)
            or set(member) != {"bytes", "sha256"}
            or type(member.get("bytes")) is not int
            or not 0 <= member["bytes"] <= MAX_METADATA_BYTES
            or not _digest(member.get("sha256"))
        ):
            raise ValueError("Federation metadata member identity is malformed")
        total += member["bytes"]
    if (
        type(manifest.get("source_bytes")) is not int
        or total != manifest["source_bytes"]
        or total + len(raw) > MAX_BYTES
    ):
        raise ValueError("Federation declared byte population differs")
    sizes = validate_regular_namespace(
        root,
        {"manifest.json", *manifest["files"]},
        max_files=MAX_FILES,
        max_bytes=MAX_BYTES,
    )
    if any(
        sizes[name] != member["bytes"] for name, member in manifest["files"].items()
    ):
        raise ValueError("Federation metadata physical size differs")
    required = manifest["capsule_manifest_sha256s"]
    if (
        any(not _digest(pin) for pin in required)
        or len(set(required)) != len(required)
        or not isinstance(capsule_sources, Mapping)
        or not set(required) <= set(capsule_sources)
    ):
        raise ValueError("Federation capsule resolver closure is incomplete")
    prepared = prepare_federation(
        context_directory=context_directory,
        expected_context_sha256=manifest["context_manifest_sha256"],
        native_archive_directory=native_archive_directory,
        capsule_sources={pin: capsule_sources[pin] for pin in required},
    )
    if not _same(prepared.manifest, manifest):
        raise ValueError("Federation source joins or coverage claims differ")
    for relative, expected in prepared.buffers.items():
        member = manifest["files"][relative]
        actual = _read(root / relative, member["bytes"])
        if actual != expected or sha256(actual).hexdigest() != member["sha256"]:
            raise ValueError(
                "Federation metadata buffer or index correspondence differs"
            )
    return prepared


def load_neotoma_ancillary_federation(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
) -> NeotomaAncillaryFederation:
    """Authenticate the declared metadata view; source entity buffers remain unopened."""
    return _load(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        context_directory=context_directory,
        native_archive_directory=native_archive_directory,
        capsule_sources=capsule_sources,
    ).view


def validate_neotoma_ancillary_federation_sources(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    capsule_sources: Mapping[str, Path],
) -> dict[str, Any]:
    """Explicitly replay every declared capsule; no native numerical archive sweep."""
    prepared = _load(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        context_directory=context_directory,
        native_archive_directory=native_archive_directory,
        capsule_sources=capsule_sources,
    )
    for digest, root in prepared.capsule_sources.items():
        load_neotoma_ancillary_capsule(
            root,
            expected_manifest_sha256=digest,
            context_directory=context_directory,
            native_archive_directory=native_archive_directory,
            predecessor_facets=prepared.predecessors[digest],
        )
    return {
        "schema_version": "neotoma-ancillary-federation-source-verification.v1",
        "federation_manifest_sha256": expected_manifest_sha256,
        "capsule_manifest_sha256s": sorted(prepared.capsule_sources),
        "capsule_count": len(prepared.capsule_sources),
        "source_assessments_replayed": True,
        "native_archive_numerical_entities_replayed": False,
        "scientific_admission": "not_asserted",
    }
