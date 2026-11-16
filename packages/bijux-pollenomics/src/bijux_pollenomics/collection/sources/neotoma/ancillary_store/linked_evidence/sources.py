"""Resolve shared anchored evidence separately from current metadata access duties."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ...capture.linked_resources.authority import authenticate_linked_root_metadata
from ...capture.linked_resources.evidence import (
    load_neotoma_linked_evidence,
    read_neotoma_linked_evidence_metadata,
    read_neotoma_linked_evidence_target,
)
from ...capture.linked_resources.models import EVIDENCE_SCHEMA, NeotomaLinkedEvidence
from ...capture.linked_resources.protocol import _RANK
from ...capture.resources.models import DEVELOPMENT_ROLES
from ...resource_catalogue.archive.files import _digest
from ...resource_catalogue.source_projection import _same
from ..context.validation import NeotomaAncillaryContext


def resolve_linked_evidence(
    control: dict[str, Any], evidence_sources: Mapping[str, Path] | None
) -> NeotomaLinkedEvidence:
    """Require an independent state anchor; source proof text is never a resolver."""
    reference = control.get("source_evidence")
    if (
        not isinstance(reference, dict)
        or set(reference) != {"schema_version", "manifest_sha256"}
        or reference["schema_version"] != EVIDENCE_SCHEMA
        or not _digest(reference["manifest_sha256"])
        or not isinstance(evidence_sources, Mapping)
        or reference["manifest_sha256"] not in evidence_sources
    ):
        raise ValueError("Scoped capsule requires an anchored evidence resolver")
    pin = reference["manifest_sha256"]
    return NeotomaLinkedEvidence(evidence_sources[pin], pin)


def scoped_metadata(
    control: dict[str, Any],
    context: NeotomaAncillaryContext,
    evidence_sources: Mapping[str, Path] | None,
) -> tuple[NeotomaLinkedEvidence, dict[str, Any], dict[str, Any]]:
    """Bind dated state metadata and fresh roots, without predecessor entity reads."""
    evidence = resolve_linked_evidence(control, evidence_sources)
    header = read_neotoma_linked_evidence_metadata(
        evidence.directory, expected_manifest_sha256=evidence.manifest_sha256
    )
    roster = header["authority"]["roster_sha256"]
    if roster not in context.current_scope_inputs:
        raise ValueError("Scoped evidence current metadata roster resolver is missing")
    current = authenticate_linked_root_metadata(
        expected_roster_sha256=roster, scope=context.current_scope_inputs[roster]
    )
    roots = header["authority"]["root_identities"]
    if set(roots) != {str(key) for key in current["roots"]}:
        raise ValueError("Scoped evidence current root population differs")
    for key, original in roots.items():
        fields = (
            "dataset_id",
            "site_id",
            "collection_unit_id",
            "dataset_type",
            "database",
        )
        if not _same(
            {field: original[field] for field in fields},
            {field: current["roots"][int(key)][field] for field in fields},
        ):
            raise ValueError("Scoped evidence current native owner differs")
    references = control["plan"]["source_facet_manifest_sha256s"]
    if (
        len(references) != len(header["authority"]["source_captures"])
        or set(references) != set(header["authority"]["source_captures"])
        or type(control["plan"]["include_higher_taxa"]) is not bool
    ):
        raise ValueError("Scoped evidence complete predecessor population differs")
    if not _same(control["policy_sources"], header["authority"]["policy_sources"]):
        raise ValueError("Scoped evidence policy source declarations differ")
    return evidence, header, current


def read_scoped_target(
    evidence: NeotomaLinkedEvidence,
    identity: dict[str, Any],
    current: dict[str, Any],
    *,
    attempted: bool,
) -> dict[str, Any]:
    """Authenticate selected dated proof parts, then apply every current restriction."""
    kind, native = identity.get("kind"), identity.get("native_id")
    if not isinstance(kind, str) or type(native) is not int:
        raise ValueError("Scoped linked native target identity is missing or malformed")
    selected = read_neotoma_linked_evidence_target(
        evidence.directory,
        expected_manifest_sha256=evidence.manifest_sha256,
        kind=kind,
        native_id=native,
    )
    target = selected["target"]
    expected = {
        "target_key": f"{target['kind']}-{target['native_id']}",
        "kind": target["kind"],
        "native_id": target["native_id"],
        "exposure_role": target["exposure_role"],
        "source_proof_reference": {
            "target_key": f"{target['kind']}-{target['native_id']}",
            "occurrence_count": target["occurrence_count"],
            "proof_ranges": target["proof_ranges"],
        },
        "metadata_dependency_count": len(target["metadata_dependencies"]),
    }
    if not _same(identity, expected):
        raise ValueError("Scoped linked target evidence correspondence differs")
    roles = []
    for proof in selected["source_proofs"]:
        dataset = proof["root_dataset_id"]
        if dataset not in current["roots"] or not _same(
            proof["root_identity"], current["roots"][dataset]
        ):
            raise ValueError("Scoped linked occurrence current root differs")
        roles.append(current["roles"][dataset])
    dependency = (
        current["protected"].get(str(identity["native_id"]))
        if identity["kind"] == "contact"
        else None
    )
    if dependency is not None:
        roles.append(dependency["exposure_role"])
    role = max(roles, key=_RANK.__getitem__)
    if attempted and role not in DEVELOPMENT_ROLES:
        raise ValueError(
            "Scoped linked current protected dependency forbids entity access"
        )
    return {
        **selected,
        "current_use_role": role,
        "integrity_scope": "anchored_selected_proof_parts_and_current_root_metadata",
    }


def full_evidence_inputs(
    control: dict[str, Any],
    context: NeotomaAncillaryContext,
    evidence_sources: Mapping[str, Path] | None,
    source_facets: Mapping[str, Path],
) -> dict[str, Any]:
    """Authenticate the complete external source closure without owning its copies."""
    evidence, header, _ = scoped_metadata(control, context, evidence_sources)
    authority = header["authority"]
    expected = set(authority["source_captures"])
    if not expected <= set(source_facets):
        raise ValueError("Scoped evidence complete predecessor resolver is missing")
    legacy = {
        pin: context.legacy_rosters[pin]
        for pin in authority["legacy_roster_sha256s"]
        if pin in context.legacy_rosters
    }
    kwargs = {
        "expected_roster_sha256": authority["roster_sha256"],
        "scope": context.current_scope_inputs[authority["roster_sha256"]],
        "source_facets": {pin: source_facets[pin] for pin in sorted(expected)},
        "legacy_rosters": legacy,
    }
    load_neotoma_linked_evidence(
        evidence.directory, expected_manifest_sha256=evidence.manifest_sha256, **kwargs
    )
    return {
        "evidence": evidence,
        "source_facets": kwargs["source_facets"],
        "scope_inputs": {authority["roster_sha256"]: kwargs["scope"]},
        "legacy_rosters": legacy,
    }
