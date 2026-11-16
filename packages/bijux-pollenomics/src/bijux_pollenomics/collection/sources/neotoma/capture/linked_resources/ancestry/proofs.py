"""Authenticate complete frozen source populations before retaining native taxon fields."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import nullcontext
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

from ....ancillary_store.context import load_neotoma_ancillary_context
from ....resource_catalogue.archive.files import _digest
from ....resource_catalogue.source_projection import _same
from ...receipts import _object, _read, _safe_root, _validate_receipt
from ...resources.models import DEVELOPMENT_ROLES
from ..authority import authenticate_linked_root_metadata
from ..evidence import (
    iter_neotoma_linked_evidence_occurrences,
    read_neotoma_linked_evidence_metadata,
)
from ..evidence_parts.ownership import _LinkedEvidenceSources
from ..evidence_parts.session import _LinkedEvidenceSession
from ..models import EVIDENCE_SCHEMA, LINKED_SCHEMA, SCOPED_LINKED_SCHEMA
from ..profiles import _UnavailableLinkedSource, parse_neotoma_linked_source
from ..protocol import _RANK, request_for
from ..replay import _control, _replay_linked_resources
from .models import (
    MAX_FILES,
    MAX_SOURCE_BYTES,
    NeotomaTaxonAncestryLimits,
    NeotomaTaxonAncestrySources,
)


def capture_snapshot(
    roots: Mapping[str, Path], *, _before_body_read: Callable[[], None] | None = None
) -> dict[str, Any]:
    """Hash finite literal capture namespaces; never accept caller-added members."""
    result = {}
    total = 0
    for digest, directory in sorted(roots.items()):
        root = _safe_root(directory)
        manifest, _, _, _, actual = _control(root, digest)
        expected = {"capture-manifest.json", "request-plan.json"}
        for entry in manifest["resources"]:
            for reference in entry["attempts"]:
                expected.add(reference["receipt_file"])
                if "body_file" in reference:
                    expected.add(reference["body_file"])
        sizes = validate_regular_namespace(
            root, expected, max_files=MAX_FILES, max_bytes=MAX_SOURCE_BYTES - total
        )
        members = {}
        for name, size in sorted(sizes.items()):
            if name.endswith(".body") and _before_body_read is not None:
                _before_body_read()
            raw = _read(root / name, min(32 * 1024 * 1024, MAX_SOURCE_BYTES - total))
            if len(raw) != size:
                raise ValueError("Taxon ancestry source namespace size changed")
            total += len(raw)
            members[name] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
        result[actual] = members
    return result


def source_facts(
    sources: NeotomaTaxonAncestrySources,
    limits: NeotomaTaxonAncestryLimits,
    *,
    _before_body_read: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Replay each source capture once, then parse each authenticated buffer once."""
    limits.validate()
    if _before_body_read is not None:
        _before_body_read()
    if (
        not isinstance(sources.capture_sources, Mapping)
        or not sources.capture_sources
        or len(sources.capture_sources) > limits.max_source_entities
    ):
        raise ValueError("Complete taxon ancestry source capture bindings required")
    header = read_neotoma_linked_evidence_metadata(
        sources.evidence.directory,
        expected_manifest_sha256=sources.evidence.manifest_sha256,
    )
    if len(header["targets"]) > limits.max_source_entities:
        raise ValueError("Taxon ancestry source entity population exceeds bound")
    context = load_neotoma_ancillary_context(
        sources.context_directory,
        expected_manifest_sha256=sources.expected_context_sha256,
        native_archive_directory=sources.native_archive_directory,
    )
    if (
        context.manifest["native_archive"]["manifest_sha256"]
        != sources.expected_native_archive_sha256
    ):
        raise ValueError("Taxon ancestry native archive anchor differs")
    roster = header["authority"]["roster_sha256"]
    if roster not in context.current_scope_inputs or set(sources.source_facets) != set(
        header["authority"]["source_captures"]
    ):
        raise ValueError("Taxon ancestry complete parent source bindings differ")
    current = authenticate_linked_root_metadata(
        expected_roster_sha256=roster, scope=context.current_scope_inputs[roster]
    )
    declared = header["authority"]["root_identities"]
    if set(declared) != {str(key) for key in current["roots"]} or any(
        not _same(owner, current["roots"][int(key)]) for key, owner in declared.items()
    ):
        raise ValueError("Taxon ancestry current root population or identity differs")
    roots: dict[str, set[int]] = {key: set() for key in header["targets"]}
    for proof, _ in iter_neotoma_linked_evidence_occurrences(
        sources.evidence.directory,
        expected_manifest_sha256=sources.evidence.manifest_sha256,
    ):
        dataset = proof["root_dataset_id"]
        if dataset not in current["roles"] or not _same(
            proof["root_identity"], current["roots"].get(dataset)
        ):
            raise ValueError("Taxon ancestry source occurrence current owner differs")
        roots[f"{proof['target_kind']}-{proof['native_id']}"].add(dataset)
    roles = {}
    for key, target in header["targets"].items():
        inherited = [current["roles"][dataset] for dataset in roots[key]]
        dependency = (
            current["protected"].get(str(target["native_id"]))
            if target["kind"] == "contact"
            else None
        )
        if dependency is not None:
            inherited.append(dependency["exposure_role"])
        roles[key] = max(inherited, key=_RANK.__getitem__)
    controls = {}
    seen = set()
    for digest, directory in sorted(sources.capture_sources.items()):
        if not _digest(digest):
            raise ValueError("Taxon ancestry capture identity is invalid")
        manifest, control, plan, recorded, _ = _control(_safe_root(directory), digest)
        if manifest["schema_version"] == SCOPED_LINKED_SCHEMA:
            expected_reference = {
                "schema_version": EVIDENCE_SCHEMA,
                "manifest_sha256": sources.evidence.manifest_sha256,
            }
            if not _same(
                manifest.get("source_evidence"), expected_reference
            ) or not _same(control.get("source_evidence"), expected_reference):
                raise ValueError("Taxon ancestry scoped evidence reference differs")
        entries = manifest["resources"]
        targets = control["targets"]
        if (
            not isinstance(entries, list)
            or not isinstance(targets, list)
            or len(entries) != len(targets)
        ):
            raise ValueError("Taxon ancestry source target metadata population differs")
        for entry, target in zip(entries, targets, strict=True):
            if (
                not isinstance(entry, dict)
                or not isinstance(target, dict)
                or not _same(entry.get("identity"), target)
                or entry.get("target_key") != target.get("target_key")
                or target.get("target_key")
                != f"{target.get('kind')}-{target.get('native_id')}"
            ):
                raise ValueError(
                    "Taxon ancestry source target metadata identity differs"
                )
            key = entry["target_key"]
            if key not in roles or key in seen:
                raise ValueError("Taxon ancestry source target is foreign or ambiguous")
            expected = header["targets"][key]
            if (
                type(target.get("native_id")) is not int
                or target["native_id"] != expected["native_id"]
                or target.get("kind") != expected["kind"]
                or not isinstance(entry.get("attempts"), list)
            ):
                raise ValueError(
                    "Taxon ancestry source native identity or attempt population differs"
                )
            if manifest["schema_version"] == SCOPED_LINKED_SCHEMA:
                correspondence = {
                    "target_key": key,
                    "kind": expected["kind"],
                    "native_id": expected["native_id"],
                    "exposure_role": expected["exposure_role"],
                    "source_proof_reference": {
                        "target_key": key,
                        "occurrence_count": expected["occurrence_count"],
                        "proof_ranges": expected["proof_ranges"],
                    },
                    "metadata_dependency_count": len(expected["metadata_dependencies"]),
                }
                if not _same(target, correspondence):
                    raise ValueError(
                        "Taxon ancestry scoped target evidence correspondence differs"
                    )
            seen.add(key)
            if entry["attempts"] and roles[key] not in DEVELOPMENT_ROLES:
                raise ValueError(
                    "Taxon ancestry protected current target forbids body access"
                )
        controls[digest] = (manifest, control, plan, recorded)
    required = {key for key, role in roles.items() if role in DEVELOPMENT_ROLES}
    if not required <= seen:
        raise ValueError(
            "Taxon ancestry complete eligible source target coverage is missing"
        )
    legacy = {
        pin: context.legacy_rosters[pin]
        for pin in header["authority"]["legacy_roster_sha256s"]
        if pin in context.legacy_rosters
    }
    from .chain.models import MAX_FILES as MAX_ANCESTRY_SOURCE_FILES

    operation = object()
    session = (
        _LinkedEvidenceSession(
            source_owner=_LinkedEvidenceSources(
                evidence=sources.evidence,
                source_facets=sources.source_facets,
                capture_sources=sources.capture_sources,
                context_directory=sources.context_directory,
                expected_context_sha256=sources.expected_context_sha256,
                native_archive_directory=sources.native_archive_directory,
                expected_native_archive_sha256=sources.expected_native_archive_sha256,
            ),
            _max_source_files=MAX_ANCESTRY_SOURCE_FILES,
            scope_inputs=context.current_scope_inputs,
            legacy_rosters=legacy,
            operation=operation,
            _before_body_read=_before_body_read,
        )
        if any(
            control[0]["schema_version"] == SCOPED_LINKED_SCHEMA
            for control in controls.values()
        )
        else None
    )

    def check_body_permission() -> None:
        if _before_body_read is not None:
            _before_body_read()
        if session is not None:
            session.check(
                operation=operation,
                evidence=sources.evidence,
                source_facets=sources.source_facets,
                scope_inputs=context.current_scope_inputs,
                legacy_rosters=legacy,
            )

    with session if session is not None else nullcontext():
        before = capture_snapshot(
            sources.capture_sources, _before_body_read=check_body_permission
        )
        seeds = []
        edges = []
        source_counts = {}
        attempted_targets = received_entities = 0
        for digest, directory in sorted(sources.capture_sources.items()):
            manifest, control, plan, recorded = controls[digest]
            scoped = manifest["schema_version"] == SCOPED_LINKED_SCHEMA
            predecessors = {
                key: sources.source_facets[key]
                for key in plan.source_facet_manifest_sha256s
            }
            captured = _replay_linked_resources(
                directory,
                expected_manifest_sha256=digest,
                source_facets=predecessors,
                scope_inputs=context.current_scope_inputs,
                evidence=sources.evidence if scoped else None,
                legacy_rosters=legacy,
                _session=session,
                _operation=operation,
                _before_body_read=_before_body_read,
            )
            for entry in captured.resources:
                identity = entry["identity"]
                source_counts[entry["target_key"]] = entry["terminal_status"]
                attempted_targets += bool(entry["attempts"])
                received_entities += sum(
                    "body_file" in attempt for attempt in entry["attempts"]
                )
                if identity["kind"] != "taxon":
                    continue
                row = {
                    "native_id": identity["native_id"],
                    "source_capture_manifest_sha256": digest,
                    "target_key": entry["target_key"],
                    "source_terminal_status": entry["terminal_status"],
                    "source_proof_reference": {
                        "target_key": entry["target_key"],
                        "occurrence_count": header["targets"][entry["target_key"]][
                            "occurrence_count"
                        ],
                        "proof_ranges": header["targets"][entry["target_key"]][
                            "proof_ranges"
                        ],
                    },
                    "literal_record_count": None,
                    "capture_preget_scope": "not_recorded_legacy_capture"
                    if manifest["schema_version"] == LINKED_SCHEMA
                    else "authenticated_complete_source_evidence",
                }
                seeds.append(row)
                if (
                    entry["terminal_status"]
                    != "received_complete_unqualified_linked_resource"
                ):
                    row["qualification_status"] = "unavailable_source_result"
                    continue
                reference = entry["attempts"][-1]
                receipt_raw = _read(directory / reference["receipt_file"], 1024 * 1024)
                if sha256(receipt_raw).hexdigest() != reference["receipt_sha256"]:
                    raise ValueError("Taxon ancestry source receipt identity differs")
                receipt = _object(receipt_raw)
                check_body_permission()
                body = _read(
                    directory / reference["body_file"], recorded.max_response_bytes
                )
                _validate_receipt(
                    receipt,
                    request_for(identity, len(entry["attempts"])),
                    body,
                    recorded.max_response_bytes,
                )
                row["source"] = {
                    "body_file": reference["body_file"],
                    "body_sha256": sha256(body).hexdigest(),
                    "receipt_file": reference["receipt_file"],
                    "receipt_sha256": reference["receipt_sha256"],
                    "utc_start": receipt["utc_start"],
                    "utc_end": receipt["utc_end"],
                }
                try:
                    parsed = parse_neotoma_linked_source(
                        identity, body, expected_body_sha256=sha256(body).hexdigest()
                    )
                except _UnavailableLinkedSource as error:
                    row.update(
                        qualification_status="successful_empty_not_absence",
                        reason=str(error),
                    )
                    continue
                except ValueError as error:
                    row.update(
                        qualification_status="refused_source_profile", reason=str(error)
                    )
                    continue
                row["qualification_status"] = "qualified_native_taxon_detail"
                row["literal_record_count"] = len(parsed.records)
                for index, record in enumerate(parsed.payload["data"]):
                    for field, kind, relation in [
                        ("highertaxonid", "taxon", "taxon_parent"),
                        ("publicationid", "publication", "taxon_reference_publication"),
                    ]:
                        value = record[field]
                        status = (
                            "explicit_null"
                            if value is None
                            else "self_edge"
                            if kind == "taxon" and value == identity["native_id"]
                            else "literal_parent"
                            if kind == "taxon"
                            else "literal_citation"
                        )
                        edge = {
                            "child_taxon_id": identity["native_id"],
                            "native_id": value,
                            "target_kind": kind,
                            "relation": relation,
                            "status": status,
                            "json_pointer": f"/data/{index}/{field}",
                            "source_capture_manifest_sha256": digest,
                            "source_target_key": entry["target_key"],
                            "source": row["source"],
                            "native_field_value_verified": True,
                        }
                        edge["edge_id"] = sha256(
                            json.dumps(
                                edge, sort_keys=True, separators=(",", ":")
                            ).encode()
                        ).hexdigest()
                        edges.append(edge)
                        if len(edges) > limits.max_literal_edges:
                            raise ValueError(
                                "Taxon ancestry literal edge population exceeds bound"
                            )
        expected_seeds = {
            target["native_id"]
            for target in header["targets"].values()
            if target["kind"] == "taxon"
        }
        if {row["native_id"] for row in seeds} != expected_seeds:
            raise ValueError("Taxon ancestry complete declared seed population differs")
        if (
            capture_snapshot(
                sources.capture_sources, _before_body_read=check_body_permission
            )
            != before
        ):
            raise ValueError("Taxon ancestry source captures changed during derivation")
    return {
        "header": header,
        "roots": roots,
        "roles": current["roles"],
        "target_roles": roles,
        "seeds": seeds,
        "edges": edges,
        "source_results": source_counts,
        "source_snapshot": before,
        "context": context,
        "attempted_targets": attempted_targets,
        "received_entities": received_entities,
    }
