"""Bind three native detail routes to recomputed, occurrence-preserving proofs."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import fields
from pathlib import Path
import re
from typing import Any

from ...client import positive_native_id
from ..facets.links import discover_neotoma_facet_links
from ..facets.replay import _control as facet_control
from ..models import _Request
from ..receipts import _safe_root
from ..resources.models import NeotomaResourceLimits, NeotomaResourcePlan
from ..resources.protocol import validate_plan as validate_resource_plan
from .models import LINKED_KINDS, NeotomaLinkedResourcePlan, NeotomaLinkedTarget

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_RANK = {
    "development_resource_discovery": 0,
    "exposed_development": 1,
    "reserved_candidate_confirmation": 2,
    "heldout_no_numerical_access": 3,
}
_ROUTES = {"contact": "contacts", "publication": "publications", "taxon": "taxa"}


def prepare_targets(
    plan: NeotomaLinkedResourcePlan,
    source_facets: Mapping[str, Path],
    limits: NeotomaResourceLimits,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Authenticate endpoint roots before discovering links; no source body shortcut.

    Original facet replay has its own bounded source limits. A linked transport
    budget of three requests must not be applied to its five predecessor requests.
    """
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
    return _Request(
        f"{target['target_key']}-current-attempt-{attempt}",
        f"linked_resource_{target['kind']}",
        f"/{_ROUTES[target['kind']]}/{target['native_id']}",
        {},
    )


def plan_from_json(
    control: dict[str, Any],
) -> tuple[NeotomaLinkedResourcePlan, NeotomaResourceLimits]:
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
