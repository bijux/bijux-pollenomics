"""Bind three native detail routes to recomputed, occurrence-preserving proofs."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import asdict, fields
import json
from pathlib import Path
import re
from typing import Any

from ...client import positive_native_id
from ..facets.links import discover_neotoma_facet_links
from ..facets.models import NeotomaFacetScopeInputs
from ..facets.replay import _control as facet_control
from ..models import _Request
from ..receipts import _safe_root
from ..resources.models import (
    NeotomaResourceLimits,
    NeotomaResourcePlan,
    NeotomaResourceSpec,
)
from ..resources.protocol import validate_plan as validate_resource_plan
from .evidence import _index, load_neotoma_linked_evidence
from .models import (
    EVIDENCE_SCHEMA,
    LINKED_KINDS,
    SCOPED_LINKED_SCHEMA,
    NeotomaLinkedEvidence,
    NeotomaLinkedResourcePlan,
    NeotomaLinkedTarget,
)

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_RANK = {
    "development_resource_discovery": 0,
    "exposed_development": 1,
    "reserved_candidate_confirmation": 2,
    "heldout_no_numerical_access": 3,
}
_ROUTES = {"contact": "contacts", "publication": "publications", "taxon": "taxa"}


def _selected(
    plan: NeotomaLinkedResourcePlan, source_facets: Mapping[str, Path]
) -> set[tuple[str, int]]:
    if (
        not isinstance(plan, NeotomaLinkedResourcePlan)
        or not isinstance(plan.source_facet_manifest_sha256s, tuple)
        or not plan.source_facet_manifest_sha256s
        or any(
            not isinstance(digest, str) or not _HASH.fullmatch(digest)
            for digest in plan.source_facet_manifest_sha256s
        )
        or len(set(plan.source_facet_manifest_sha256s))
        != len(plan.source_facet_manifest_sha256s)
        or not isinstance(source_facets, Mapping)
        or set(source_facets) != set(plan.source_facet_manifest_sha256s)
        or type(plan.include_higher_taxa) is not bool
        or not isinstance(plan.targets, tuple)
        or not plan.targets
    ):
        raise ValueError("Neotoma linked source selection is malformed")
    selected = set()
    for target in plan.targets:
        if (
            not isinstance(target, NeotomaLinkedTarget)
            or target.kind not in LINKED_KINDS
        ):
            raise ValueError("Neotoma linked target kind is invalid")
        positive_native_id(target.native_id)
        key = (target.kind, target.native_id)
        if key in selected:
            raise ValueError("Neotoma linked target selection is duplicated")
        selected.add(key)
    return selected


def prepare_targets(
    plan: NeotomaLinkedResourcePlan,
    source_facets: Mapping[str, Path],
    limits: NeotomaResourceLimits,
    *,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Authenticate endpoint roots before discovering links; no source body shortcut.

    Original facet replay has its own bounded source limits. A linked transport
    budget of three requests must not be applied to its five predecessor requests.
    """
    selected = _selected(plan, source_facets)
    proofs: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    policies: list[str] = []
    for digest in sorted(plan.source_facet_manifest_sha256s):
        root = _safe_root(source_facets[digest])
        _, facet_plan, _, _ = facet_control(root, digest)
        source_plan = NeotomaResourcePlan(
            facet_plan.resources, facet_plan.roster_sha256
        )
        validate_resource_plan(source_plan, limits)
        policies = list(source_plan.policy_sources)
        links = discover_neotoma_facet_links(
            root,
            expected_manifest_sha256=digest,
            include_higher_taxa=plan.include_higher_taxa,
            scope_inputs=scope_inputs,
        )
        for proof in links["links"]:
            key = (proof["target_kind"], proof["native_id"])
            if key in selected:
                proofs[key].append(proof)
    targets = []
    for kind, native_id in sorted(selected):
        source_proofs = proofs[kind, native_id]
        if not source_proofs:
            raise ValueError(
                "Neotoma linked target lacks an authenticated source proof or admitted role"
            )
        role = max(
            (proof["inherited_exposure_role"] for proof in source_proofs),
            key=lambda value: _RANK[value],
        )
        targets.append(
            {
                "target_key": f"{kind}-{native_id}",
                "kind": kind,
                "native_id": native_id,
                "exposure_role": role,
                "source_proofs": source_proofs,
            }
        )
    return targets, policies


def request_for(target: dict[str, Any], attempt: int) -> _Request:
    """Bind a linked native identity to its exact current-response route."""
    return _Request(
        f"{target['target_key']}-current-attempt-{attempt}",
        f"linked_resource_{target['kind']}",
        f"/{_ROUTES[target['kind']]}/{target['native_id']}",
        {},
    )


def plan_from_json(
    control: dict[str, Any],
) -> tuple[NeotomaLinkedResourcePlan, NeotomaResourceLimits]:
    """Decode only the complete maintained linked plan and limit fields."""
    try:
        raw = control["plan"]
        if (
            not isinstance(raw, dict)
            or set(raw)
            != {"source_facet_manifest_sha256s", "targets", "include_higher_taxa"}
            or not isinstance(raw["source_facet_manifest_sha256s"], list)
            or not isinstance(raw["targets"], list)
            or any(
                not isinstance(row, dict) or set(row) != {"kind", "native_id"}
                for row in raw["targets"]
            )
            or not isinstance(control["limits"], dict)
            or set(control["limits"])
            != {field.name for field in fields(NeotomaResourceLimits)}
        ):
            raise ValueError("Neotoma linked plan fields differ")
        return NeotomaLinkedResourcePlan(
            tuple(raw["source_facet_manifest_sha256s"]),
            tuple(NeotomaLinkedTarget(**row) for row in raw["targets"]),
            raw["include_higher_taxa"],
        ), NeotomaResourceLimits(**control["limits"])
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Neotoma linked plan is malformed") from error


MAX_PLAN_BYTES = 16 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024 * 1024


def encoded_control(value: Any) -> bytes:
    """Encode deterministic finite control bytes for content-addressed receipts."""
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()


def scoped_control(
    plan: NeotomaLinkedResourcePlan,
    limits: NeotomaResourceLimits,
    targets: list[dict[str, Any]],
    policies: list[str],
    reference: dict[str, str],
) -> dict[str, Any]:
    """Retain exact target permissions and their independent evidence reference."""
    control = {
        "schema_version": SCOPED_LINKED_SCHEMA,
        "plan": asdict(plan),
        "limits": asdict(limits),
        "targets": targets,
        "policy_sources": policies,
        "source_evidence": reference,
    }
    attempts = min(limits.max_attempts, limits.max_requests)
    if (
        len(targets) * 65536 > MAX_MANIFEST_BYTES
        or len(targets) * attempts > MAX_MANIFEST_BYTES // 256
    ):
        raise ValueError(
            "Linked prospective metadata allocation exceeds its finite budget"
        )
    entries = [
        {
            "target_key": target["target_key"],
            "identity": target,
            "content_version": "current",
            "api_version": "v2.0",
            "scientific_admission": "not_asserted",
            "terminal_status": "transport_failure",
            "reason": "x" * 65536,
            "attempts": [
                {
                    "receipt_file": target["target_key"]
                    + "-current-attempt-1.receipt.json",
                    "receipt_sha256": "0" * 64,
                    "body_file": target["target_key"] + "-current-attempt-1.body",
                }
                for _ in range(attempts)
            ],
        }
        for target in targets
    ]
    prospective = {
        "schema_version": SCOPED_LINKED_SCHEMA,
        "source_evidence": reference,
        "capture_utc_start": "0" * 40,
        "capture_utc_end": "0" * 40,
        "plan_sha256": "0" * 64,
        "resources": entries,
        "request_count": limits.max_requests,
        "response_bytes": limits.max_total_bytes,
        "partitions": {"transport_failure": len(targets)},
        "scientific_admission": "not_asserted",
        "status": "closed",
        "snapshot_consistency": "Individually timed current linked responses",
    }
    if (
        len(encoded_control(control)) > MAX_PLAN_BYTES
        or len(encoded_control(prospective)) > MAX_MANIFEST_BYTES
    ):
        raise ValueError(
            "Linked plan and prospective manifest exceed separate finite metadata budgets"
        )
    return control


def validate_scoped_limits(
    evidence: NeotomaLinkedEvidence, limits: NeotomaResourceLimits
) -> None:
    """Apply existing source resource limits to the anchored evidence population."""
    header = _index(_safe_root(evidence.directory), evidence.manifest_sha256)
    roster_sha = header["authority"]["roster_sha256"]
    resources = tuple(
        NeotomaResourceSpec(**row, versions=("current",))
        for row in header["authority"]["root_identities"].values()
    )
    validate_resource_plan(NeotomaResourcePlan(resources, roster_sha), limits)


def prepare_scoped_targets(
    plan: NeotomaLinkedResourcePlan,
    source_facets: Mapping[str, Path],
    limits: NeotomaResourceLimits,
    *,
    evidence: NeotomaLinkedEvidence,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None,
    legacy_rosters: Mapping[str, Path] | None = None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, str]]:
    """Require a freshly authenticated complete evidence publication before GETs."""
    return _prepare_scoped_targets(
        plan,
        source_facets,
        limits,
        evidence=evidence,
        scope_inputs=scope_inputs,
        legacy_rosters=legacy_rosters,
    )


def _prepare_scoped_targets(
    plan: NeotomaLinkedResourcePlan,
    source_facets: Mapping[str, Path],
    limits: NeotomaResourceLimits,
    *,
    evidence: NeotomaLinkedEvidence,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None,
    legacy_rosters: Mapping[str, Path] | None = None,
    _session: Any = None,
    _operation: object | None = None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, str]]:
    """Require an externally anchored complete source publication before new GETs."""
    selected = _selected(plan, source_facets)
    if not isinstance(evidence, NeotomaLinkedEvidence):
        raise ValueError("Complete authenticated linked source evidence is required")
    header = _index(_safe_root(evidence.directory), evidence.manifest_sha256)
    roster_sha = header["authority"]["roster_sha256"]
    if not isinstance(scope_inputs, Mapping) or set(scope_inputs) != {roster_sha}:
        raise ValueError("Complete linked evidence scope resolvers are required")
    if set(source_facets) != set(header["authority"]["source_captures"]):
        raise ValueError("Linked evidence complete source namespace differs")
    validate_scoped_limits(evidence, limits)
    if _session is None:
        index = load_neotoma_linked_evidence(
            evidence.directory,
            expected_manifest_sha256=evidence.manifest_sha256,
            expected_roster_sha256=roster_sha,
            scope=scope_inputs[roster_sha],
            source_facets=source_facets,
            legacy_rosters=legacy_rosters,
        )
    else:
        from .evidence_parts.session import _LinkedEvidenceSession

        if type(_session) is not _LinkedEvidenceSession:
            raise ValueError("Only an active source-owned evidence session is accepted")
        index = _session.index(
            operation=_operation,
            evidence=evidence,
            source_facets=source_facets,
            scope_inputs=scope_inputs,
            legacy_rosters=legacy_rosters,
        )
    targets = []
    for kind, native_id in sorted(selected):
        key = f"{kind}-{native_id}"
        target = index["targets"].get(key)
        if (
            target is None
            or not plan.include_higher_taxa
            and not target["has_direct_proof"]
        ):
            raise ValueError(
                "Linked target lacks an approved direct or explicit higher-taxon source proof"
            )
        targets.append(
            {
                "target_key": key,
                "kind": kind,
                "native_id": native_id,
                "exposure_role": target["exposure_role"],
                "source_proof_reference": {
                    "target_key": key,
                    "occurrence_count": target["occurrence_count"],
                    "proof_ranges": target["proof_ranges"],
                },
                "metadata_dependency_count": len(target["metadata_dependencies"]),
            }
        )
    policies = index["authority"]["policy_sources"]
    reference = {
        "schema_version": EVIDENCE_SCHEMA,
        "manifest_sha256": evidence.manifest_sha256,
    }
    scoped_control(plan, limits, targets, policies, reference)
    return targets, policies, reference
