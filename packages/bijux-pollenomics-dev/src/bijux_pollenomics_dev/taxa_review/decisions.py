"""Validate returned review intent without authorizing canonical scientific changes."""

from __future__ import annotations

from datetime import date
import json
from typing import Any

from ..source_completion.evidence import digest

FIELDS = {
    "review_row_id",
    "source_identity_sha256",
    "review_state",
    "reviewer_id",
    "decision_date",
    "rationale",
    "evidence_reference_ids",
    "proposed_primary_group_id",
    "proposed_primary_subgroup_id",
    "proposed_role_ids",
}


def validate_decisions(
    bundle: dict[str, Any], returned: dict[str, Any]
) -> dict[str, Any]:
    """Reject stale/foreign identities and illegal groupings; acceptance remains review intent."""
    actual_hash = digest(
        {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    )
    if bundle.get("bundle_sha256") != actual_hash:
        raise ValueError("Review bundle digest does not match content")
    if (
        set(returned) != {"bundle_sha256", "decisions"}
        or returned["bundle_sha256"] != actual_hash
    ):
        raise ValueError("Returned decisions target a stale or unsupported bundle")
    rows = {row["review_row_id"]: row for row in bundle["rows"]}
    if len(rows) != len(bundle["rows"]):
        raise ValueError("Duplicate review identity in bundle")
    contract = bundle["classification_contract"]
    groups = {
        group["group_id"]: {subgroup["subgroup_id"] for subgroup in group["subgroups"]}
        for group in contract["hierarchy"]["groups"]
    }
    roles = set(contract["role_vocabulary"]["ecological_roles"]) | {
        role["role_id"] for role in contract["role_vocabulary"]["crop_evidence_roles"]
    }
    if not isinstance(returned["decisions"], list):
        raise ValueError("decisions must be a list")
    seen = set()
    diff = []
    for decision in returned["decisions"]:
        if not isinstance(decision, dict) or set(decision) != FIELDS:
            raise ValueError("Decision fields do not match the review-intent schema")
        identity = decision["review_row_id"]
        if not isinstance(identity, str) or identity not in rows or identity in seen:
            raise ValueError("Unknown or duplicate decision identity")
        seen.add(identity)
        row = rows[identity]
        if decision["source_identity_sha256"] != row["source_identity_sha256"]:
            raise ValueError("Decision source identity is stale")
        state = decision["review_state"]
        if not isinstance(state, str) or state not in {
            "proposed",
            "needs_discussion",
            "accepted",
            "rejected",
            "superseded",
        }:
            raise ValueError("Unknown review state")
        for field in ("reviewer_id", "decision_date", "rationale"):
            value = decision[field]
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"Invalid review field: {field}")
        references = decision["evidence_reference_ids"]
        if (
            not isinstance(references, list)
            or any(
                not isinstance(value, str) or not value.strip() for value in references
            )
            or len(set(references)) != len(references)
        ):
            raise ValueError("Evidence references must be unique nonempty strings")
        if state in {"accepted", "rejected", "superseded"} and (
            any(
                decision[field] is None
                for field in ("reviewer_id", "decision_date", "rationale")
            )
            or not references
        ):
            raise ValueError(
                "Conclusive review intent requires reviewer, date, rationale and evidence"
            )
        if decision["decision_date"] is not None:
            parsed = date.fromisoformat(decision["decision_date"])
            if parsed.isoformat() != decision["decision_date"]:
                raise ValueError("Decision date must be an ISO calendar date")
        group, subgroup = (
            decision["proposed_primary_group_id"],
            decision["proposed_primary_subgroup_id"],
        )
        if group is not None and (not isinstance(group, str) or group not in groups):
            raise ValueError("Unknown ecological group")
        if subgroup is not None and (
            not isinstance(subgroup, str)
            or group is None
            or subgroup not in groups[group]
        ):
            raise ValueError("Subgroup does not belong to proposed group")
        proposed_roles = decision["proposed_role_ids"]
        if (
            not isinstance(proposed_roles, list)
            or any(
                not isinstance(role, str) or role not in roles
                for role in proposed_roles
            )
            or len(set(proposed_roles)) != len(proposed_roles)
        ):
            raise ValueError("Unknown or duplicate ecological role")
        diff.append(
            {
                "review_row_id": identity,
                "previous_review_state": row["review_state"],
                "returned_review_intent": decision,
                "scientific_acceptance_verified": False,
                "canonical_import_allowed": False,
            }
        )
    return {
        "bundle_sha256": actual_hash,
        "decision_count": len(diff),
        "decisions": sorted(diff, key=lambda item: item["review_row_id"]),
        "canonical_import_allowed": False,
        "publication_allowed": False,
        "validation_scope": "Identity, vocabulary and documentation shape only; reviewer qualification, evidence sufficiency and scientific acceptance are not verified.",
    }


def load_review_json(content: bytes) -> dict[str, Any]:
    """Reject duplicate object keys at the human-review boundary."""

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON field: {key}")
            result[key] = value
        return result

    result = json.loads(content, object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError("Review JSON must be an object")
    return result
