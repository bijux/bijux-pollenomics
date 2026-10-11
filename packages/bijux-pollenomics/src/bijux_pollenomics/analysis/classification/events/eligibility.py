"""Reviewed membership eligibility independent of pollen detection and chronology."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from typing import cast

from . import authority
from .admission import _classification_refusal_reason, _source_identity_refusal_reason
from .identity import _canonical, _digest, _optional_text
from .indexing import (
    _deduplicate_memberships,
    _source_observation_index,
    _unique_index,
)
from .models import ClassificationReviewContext
from .vocabulary import _COUNTRY_CODES


@dataclass(frozen=True)
class ClassificationEligibilityResult:
    """Immutable review projection; a positive decision never admits an LRA run."""

    canonical_json: str
    result_digest: str

    def as_dict(self) -> dict[str, object]:
        """Return an independent projection, retaining source zero/null/absence."""
        return cast(dict[str, object], json.loads(self.canonical_json))


def assess_classification_eligibility(
    *,
    observation_memberships: Sequence[Mapping[str, object]],
    classification_mappings: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
    context: ClassificationReviewContext,
) -> ClassificationEligibilityResult:
    """Assess the complete observation union using the governed review authority.

    Counts, units, detection, chronology, geometry and PPE remain unassessed.
    Thus zero, null and absent values can retain a reviewed taxon identity; this
    does not make them valid counts, positive detections or executable samples.
    All supplied rows bind the input digest, including duplicate/refused rows.
    Callers cannot supply an authority receipt or bypass the authority universe.
    """
    # Freeze caller-owned rows and choose a stable representative for refused
    # duplicate identities; no conflicting row becomes an eligible observation.
    observation_memberships = _ordered_rows(observation_memberships)
    classification_mappings = _ordered_rows(classification_mappings)
    observations = _ordered_rows(observations)
    members, member_duplicates, member_identical, member_conflicting, conflicts = (
        _deduplicate_memberships(observation_memberships)
    )
    mapping_index, mapping_conflicts = _unique_index(
        classification_mappings, "classification_concept_id"
    )
    source, source_conflicts, source_duplicates, duplicate_count, identical_count = (
        _source_observation_index(observations)
    )
    universe_reason = authority._classification_authority_universe_reason(
        classification_mappings
    )
    ambiguous = authority._ambiguous_authorized_mapping_ids(
        classification_mappings, context
    )
    rows: list[dict[str, object]] = []
    for observation_id in sorted(set(members) | set(source)):
        membership = members.get(observation_id)
        observation = source.get(observation_id)
        concept = (
            _optional_text(membership.get("classification_concept_id"))
            if membership is not None
            else None
        )
        mapping = mapping_index.get(concept or "")
        reason = conflicts.get(observation_id)
        if reason is None and observation_id in source_conflicts:
            reason = "conflicting_source_observation"
        if reason is None and observation_id in source_duplicates:
            reason = "duplicate_source_observation"
        if reason is None and membership is None:
            reason = "classification_membership_missing"
        if reason is None and observation is None:
            reason = "missing_source_observation"
        if reason is None and membership is not None:
            reason = _classification_refusal_reason(
                membership,
                mapping,
                concept,
                mapping_conflicts,
                universe_reason,
                ambiguous,
                context,
            )
        if (
            reason is None
            and mapping is not None
            and observation is not None
            and membership is not None
        ):
            reason = _source_identity_refusal_reason(mapping, observation)
            if reason is None:
                reason = _lineage_refusal(membership, observation, context)
        rows.append(
            {
                "observation_id": observation_id,
                "classification_concept_id": concept,
                "review_eligibility": "eligible" if reason is None else "refused",
                "reason_code": reason,
                "membership": membership,
                "source_observation": observation,
                "classification_mapping": mapping,
            }
        )
    eligible = sum(row["review_eligibility"] == "eligible" for row in rows)
    payload = {
        "schema_version": "classification-review-eligibility.v1",
        "scope": "reviewed_source_taxon_membership_only",
        "unassessed": ["counts", "units", "detection", "chronology", "geometry", "ppe"],
        "context": context.as_dict(),
        "classification_authority_manifest_sha256": (
            authority._classification_authority_manifest_sha256()
        ),
        "authority_universe_reason": universe_reason,
        "input_digest": _digest(
            {
                key: sorted(_canonical(row) for row in values)
                for key, values in (
                    ("memberships", observation_memberships),
                    ("mappings", classification_mappings),
                    ("observations", observations),
                )
            }
        ),
        "reconciliation": {
            "input_membership_count": len(observation_memberships),
            "input_observation_count": len(observations),
            "unique_observation_count": len(rows),
            "eligible_observation_count": eligible,
            "refused_observation_count": len(rows) - eligible,
            "duplicate_membership_count": member_duplicates,
            "identical_duplicate_membership_count": member_identical,
            "conflicting_duplicate_membership_count": member_conflicting,
            "duplicate_source_observation_count": duplicate_count,
            "identical_duplicate_source_observation_count": identical_count,
        },
        "rows": rows,
    }
    return ClassificationEligibilityResult(_canonical(payload), _digest(payload))


def _ordered_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    encoded = sorted(
        json.dumps(dict(row), sort_keys=True, separators=(",", ":"), allow_nan=False)
        for row in rows
    )
    return [cast(dict[str, object], json.loads(row)) for row in encoded]


def _lineage_refusal(
    membership: Mapping[str, object],
    observation: Mapping[str, object],
    context: ClassificationReviewContext,
) -> str | None:
    if _optional_text(observation.get("source_family")) != context.source_family:
        return "source_lineage_mismatch"
    country = _optional_text(observation.get("country_code"))
    if country not in _COUNTRY_CODES:
        return "ungoverned_country"
    if country != _optional_text(membership.get("governed_country_code")):
        return "source_lineage_mismatch"
    if (
        _optional_text(observation.get("source_snapshot_id"))
        != authority._CLASSIFICATION_AUTHORITY.source_snapshot_id
        or _optional_text(observation.get("build_id"))
        != authority._CLASSIFICATION_AUTHORITY.build_id
    ):
        return "classification_authority_lineage_mismatch"
    return None
