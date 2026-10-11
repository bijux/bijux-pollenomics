"""Validate complete taxon/PPE/fall-speed returns without admitting LRA input."""

from __future__ import annotations

from collections import Counter
from datetime import date
import hashlib
import json
import math
from typing import Any, cast

from .projection import build_lra_parameter_review

_DECISION_FIELDS = {
    "review_row_id",
    "source_identity_sha256",
    "disposition",
    "accepted_taxon_name",
    "accepted_taxon_rank",
    "lra_model_taxon_id",
    "primary_group_id",
    "primary_subgroup_id",
    "role_ids",
    "ppe_binding",
    "fall_speed_binding",
    "reviewer_id",
    "decision_date",
    "rationale",
    "evidence_reference_ids",
}
_BINDING_FIELDS = {
    "parameter_record_id",
    "parameter_record_sha256",
    "parameter_candidate_id",
    "parameter_candidate_sha256",
    "source_value_text",
    "source_value",
    "source_units",
    "normalized_value",
    "normalized_units",
    "reference_taxon",
    "source_uncertainty_text",
    "source_uncertainty_value",
    "applicability_domain",
    "normalization_rationale",
}


def _canonical(value: object) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("Decision inputs must be finite JSON data") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _identity(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field} must be an exact nonempty string")
    return value


def _identity_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an identity array")
    result = [_identity(item, field) for item in value]
    if result != sorted(result) or len(result) != len(set(result)):
        raise ValueError(f"{field} must contain unique identities in canonical order")
    return result


def _number(value: object, field: str, *, positive: bool) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or (result <= 0 if positive else result < 0):
        raise ValueError(f"{field} is outside its supported finite range")
    return result


def _vocabulary(projection: dict[str, Any]) -> tuple[dict[str, set[str]], set[str]]:
    contract = projection.get("classification_contract")
    if not isinstance(contract, dict):
        raise ValueError("Projection classification contract is malformed")
    hierarchy = cast(dict[str, Any], contract.get("hierarchy", {}))
    raw_groups = hierarchy.get("groups")
    role_vocabulary = cast(dict[str, Any], contract.get("role_vocabulary", {}))
    if not isinstance(raw_groups, list):
        raise ValueError("Projection classification hierarchy is malformed")
    groups: dict[str, set[str]] = {}
    for raw in raw_groups:
        if not isinstance(raw, dict):
            raise ValueError("Projection classification group is malformed")
        group_id = _identity(raw.get("group_id"), "group_id")
        subgroups = raw.get("subgroups")
        if not isinstance(subgroups, list):
            raise ValueError("Projection classification subgroup is malformed")
        if group_id in groups:
            raise ValueError("Projection classification group is duplicated")
        groups[group_id] = {
            _identity(cast(dict[str, Any], value).get("subgroup_id"), "subgroup_id")
            for value in subgroups
            if isinstance(value, dict)
        }
        if len(groups[group_id]) != len(subgroups):
            raise ValueError("Projection classification subgroup is duplicated")
    roles = set()
    for key in ("ecological_roles", "crop_evidence_roles"):
        values = role_vocabulary.get(key)
        if not isinstance(values, list):
            raise ValueError("Projection role vocabulary is malformed")
        for value in values:
            role = value.get("role_id") if isinstance(value, dict) else value
            roles.add(_identity(role, "role_id"))
    return groups, roles


def _binding(
    value: object,
    *,
    kind: str,
    authorities: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _BINDING_FIELDS:
        raise ValueError(f"{kind} binding fields differ from the exact schema")
    binding = cast(dict[str, Any], value)
    record_id = _identity(binding["parameter_record_id"], "parameter_record_id")
    record = authorities.get(record_id)
    if record is None or kind not in record.get("capabilities", []):
        raise ValueError(f"{kind} binding targets an unsupported parameter record")
    if binding["parameter_record_sha256"] != record["parameter_record_sha256"]:
        raise ValueError(f"{kind} binding targets stale parameter evidence")
    raw_candidates = record.get("parameter_candidates")
    if not isinstance(raw_candidates, list) or any(
        not isinstance(candidate, dict) for candidate in raw_candidates
    ):
        raise ValueError("Projection parameter candidates are malformed")
    candidates = {
        cast(dict[str, Any], candidate).get("parameter_candidate_id"): cast(
            dict[str, Any], candidate
        )
        for candidate in raw_candidates
    }
    candidate_id = _identity(
        binding["parameter_candidate_id"], "parameter_candidate_id"
    )
    candidate = candidates.get(candidate_id)
    if (
        candidate is None
        or candidate.get("parameter_kind") != kind
        or candidate.get("parsing_status") != "usable_finite_positive"
    ):
        raise ValueError(f"{kind} binding targets an unusable parameter candidate")
    if binding["parameter_candidate_sha256"] != candidate.get(
        "parameter_candidate_sha256"
    ):
        raise ValueError(f"{kind} binding targets a stale parameter candidate")
    for field in (
        "source_value_text",
        "source_value",
        "source_units",
        "source_uncertainty_text",
        "source_uncertainty_value",
    ):
        if binding[field] != candidate.get(field):
            raise ValueError(f"{kind} binding differs from selected source evidence")
    normalized = _number(
        binding["normalized_value"], f"{kind} normalized value", positive=True
    )
    if normalized != candidate.get("source_value"):
        raise ValueError(f"{kind} normalized value lacks selected source evidence")
    if binding["normalized_units"] != candidate.get("source_units"):
        raise ValueError(
            f"{kind} normalized units differ from selected source evidence"
        )
    if kind == "ppe":
        _identity(binding["reference_taxon"], "reference_taxon")
    elif binding["reference_taxon"] is not None:
        raise ValueError("Fall-speed binding must not invent a reference taxon")
    uncertainty = binding["source_uncertainty_value"]
    if uncertainty is not None:
        _number(uncertainty, f"{kind} source uncertainty", positive=False)
    _identity(binding["applicability_domain"], "applicability_domain")
    _identity(binding["normalization_rationale"], "normalization_rationale")
    return binding


def _validate_projection(projection: dict[str, Any]) -> None:
    supplied = projection.get("projection_sha256")
    expected = _digest(
        {key: value for key, value in projection.items() if key != "projection_sha256"}
    )
    if (
        projection.get("schema_version") != "neotoma-lra-parameter-review.v1"
        or supplied != expected
        or projection.get("reviewer_authority") != "declared_not_authenticated"
        or projection.get("review_status") != "awaiting_qualified_return"
        or projection.get("parameter_candidate_extraction") != "source_specific"
        or projection.get("taxon_parameter_matching") != "not_performed"
        or projection.get("provenance_trust_anchor")
        != "externally_supplied_pin_verified_against_content"
        or projection.get("lra_accepted_samples") != 0
        or projection.get("executable_request") is not None
        or projection.get("scientific_acceptance") != "not_evaluated"
        or projection.get("release_acceptance") != "not_evaluated"
        or projection.get("publication_allowed") is not False
    ):
        raise ValueError("LRA parameter projection identity or claim boundary differs")


def validate_lra_parameter_decisions(
    projection: dict[str, Any],
    returned: dict[str, Any],
    *,
    priority: dict[str, Any],
    provenance: dict[str, Any],
    review: dict[str, Any],
    provenance_file_sha256: str,
) -> dict[str, Any]:
    """Validate returned intent against a rebuilt, externally pinned projection."""
    projection_initial = _digest(projection)
    returned_initial = _digest(returned)
    authority_initial = tuple(
        _digest(value) for value in (priority, provenance, review)
    )
    rebuilt = build_lra_parameter_review(
        priority,
        provenance,
        review,
        provenance_file_sha256=provenance_file_sha256,
    )
    if _canonical(projection) != _canonical(rebuilt):
        raise ValueError("Projection differs from its pinned source rebuild")
    projection = rebuilt
    _validate_projection(projection)
    if (
        set(returned)
        != {
            "schema_version",
            "projection_sha256",
            "reviewer_authority",
            "decisions",
        }
        or returned.get("schema_version") != "neotoma-lra-parameter-decisions.v1"
        or returned.get("projection_sha256") != projection["projection_sha256"]
        or returned.get("reviewer_authority") != "declared_not_authenticated"
    ):
        raise ValueError("Returned decisions target an unsupported projection")
    raw_concepts = projection.get("candidate_taxon_rows")
    raw_parameters = projection.get("parameter_authority_rows")
    raw_decisions = returned.get("decisions")
    if (
        not isinstance(raw_concepts, list)
        or not isinstance(raw_parameters, list)
        or not isinstance(raw_decisions, list)
        or any(not isinstance(value, dict) for value in raw_concepts)
        or any(not isinstance(value, dict) for value in raw_parameters)
        or any(not isinstance(value, dict) for value in raw_decisions)
    ):
        raise ValueError("Projection or decision rows are malformed")
    concepts = {
        cast(dict[str, Any], row)["review_row_id"]: cast(dict[str, Any], row)
        for row in raw_concepts
    }
    authorities = {
        cast(dict[str, Any], row)["parameter_record_id"]: cast(dict[str, Any], row)
        for row in raw_parameters
    }
    if len(concepts) != len(raw_concepts) or len(authorities) != len(raw_parameters):
        raise ValueError("Projection contains duplicate source identities")
    groups, roles = _vocabulary(projection)
    seen: set[str] = set()
    validated = []
    disposition_counts: Counter[str] = Counter()
    for raw in cast(list[dict[str, Any]], raw_decisions):
        if set(raw) != _DECISION_FIELDS:
            raise ValueError("Returned decision fields differ from the exact schema")
        identity = _identity(raw["review_row_id"], "review_row_id")
        source = concepts.get(identity)
        if source is None or identity in seen:
            raise ValueError("Returned decision identity is unknown or duplicated")
        seen.add(identity)
        if raw["source_identity_sha256"] != source["source_identity_sha256"]:
            raise ValueError("Returned decision targets stale source evidence")
        reviewer = _identity(raw["reviewer_id"], "reviewer_id")
        rationale = _identity(raw["rationale"], "rationale")
        evidence = _identity_list(raw["evidence_reference_ids"], "evidence references")
        if not evidence:
            raise ValueError("Every returned decision requires evidence")
        decision_date = _identity(raw["decision_date"], "decision_date")
        try:
            parsed = date.fromisoformat(decision_date)
        except ValueError as exc:
            raise ValueError("Decision date must be an ISO calendar date") from exc
        if parsed.isoformat() != decision_date:
            raise ValueError("Decision date must use canonical ISO form")
        disposition = raw["disposition"]
        if disposition not in {"retained_intent", "excluded_intent", "unresolved"}:
            raise ValueError("Decision disposition is unsupported")
        role_ids = _identity_list(raw["role_ids"], "role_ids")
        if any(role not in roles for role in role_ids):
            raise ValueError("Decision uses an unknown ecological role")
        group = raw["primary_group_id"]
        subgroup = raw["primary_subgroup_id"]
        if disposition == "retained_intent":
            for field in (
                "accepted_taxon_name",
                "accepted_taxon_rank",
                "lra_model_taxon_id",
                "primary_group_id",
                "primary_subgroup_id",
            ):
                _identity(raw[field], field)
            if group not in groups or subgroup not in groups[cast(str, group)]:
                raise ValueError("Decision group and subgroup do not belong together")
            ppe = _binding(raw["ppe_binding"], kind="ppe", authorities=authorities)
            fall_speed = _binding(
                raw["fall_speed_binding"],
                kind="fall_speed",
                authorities=authorities,
            )
        else:
            if (
                any(
                    raw[field] is not None
                    for field in (
                        "accepted_taxon_name",
                        "accepted_taxon_rank",
                        "lra_model_taxon_id",
                        "primary_group_id",
                        "primary_subgroup_id",
                        "ppe_binding",
                        "fall_speed_binding",
                    )
                )
                or role_ids
            ):
                raise ValueError(
                    "Non-retained decisions must not carry accepted mappings"
                )
            ppe = None
            fall_speed = None
        disposition_counts[cast(str, disposition)] += 1
        validated.append(
            {
                **raw,
                "ppe_binding": ppe,
                "fall_speed_binding": fall_speed,
                "reviewer_id": reviewer,
                "rationale": rationale,
            }
        )
    if seen != set(concepts) or len(validated) != len(concepts):
        raise ValueError("Returned decisions do not close the candidate denominator")
    if [row["review_row_id"] for row in validated] != sorted(seen):
        raise ValueError("Returned decisions must use canonical source-identity order")
    payload: dict[str, Any] = {
        "schema_version": "neotoma-lra-parameter-decision-validation.v1",
        "projection_sha256": projection["projection_sha256"],
        "reviewer_authority": "declared_not_authenticated",
        "decision_count": len(validated),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "decisions": validated,
        "qualified_scientific_review_verified": False,
        "canonical_import_allowed": False,
        "lra_accepted_samples": 0,
        "executable_request": None,
        "scientific_acceptance": "not_evaluated",
        "release_acceptance": "not_evaluated",
        "publication_allowed": False,
        "claims_not_made": [
            "reviewer_authentication",
            "taxon_acceptance",
            "ppe_acceptance",
            "fall_speed_acceptance",
            "compatible_pollen_denominator",
            "chronology_selection",
            "basin_geometry_admission",
            "numerical_lra_execution",
            "scientific_acceptance",
            "release_acceptance",
        ],
    }
    if (
        projection_initial != _digest(projection)
        or returned_initial != _digest(returned)
        or authority_initial
        != tuple(_digest(value) for value in (priority, provenance, review))
    ):
        raise ValueError("Decision evidence changed during validation")
    payload["validation_sha256"] = _digest(payload)
    return cast(dict[str, Any], json.loads(_canonical(payload)))
