"""Build a complete Neotoma taxon/PPE/fall-speed review projection."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Any, cast

from ...source_completion.evidence import digest
from .candidates import PARAMETER_KINDS, USABLE_STATUS, parameter_candidates

_PARAMETER_SOURCES = {"landclim", "lra_reference_resources"}


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
        raise ValueError("Review inputs must be finite JSON data") from exc


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _artifact_sha256(value: object) -> str:
    return hashlib.sha256((_canonical(value) + "\n").encode()).hexdigest()


def _review_artifact_sha256(value: object) -> str:
    content = (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )
    return hashlib.sha256(content.encode()).hexdigest()


def _sha256_identity(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field} is not a lowercase SHA-256 identity")
    return value


def _rows(payload: dict[str, Any], label: str) -> list[dict[str, Any]]:
    value = payload.get("rows")
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{label} rows are malformed")
    return cast(list[dict[str, Any]], value)


def _indexed(
    rows: list[dict[str, Any]], key: str, label: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        identity = row.get(key)
        if (
            not isinstance(identity, str)
            or not identity
            or identity != identity.strip()
        ):
            raise ValueError(f"{label} identity is malformed")
        if identity in result:
            raise ValueError(f"{label} identity is duplicated")
        result[identity] = row
    return result


def _count(payload: dict[str, Any], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} is not a nonnegative integer")
    return value


def _input_hashes(payload: dict[str, Any], label: str) -> dict[str, Any]:
    value = payload.get("input_file_sha256")
    if not isinstance(value, dict):
        raise ValueError(f"{label} input hashes are malformed")
    return cast(dict[str, Any], value)


def _validate_authorities(
    priority: dict[str, Any],
    provenance: dict[str, Any],
    review: dict[str, Any],
    provenance_file_sha256: str,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, str],
]:
    if (
        priority.get("schema_version") != "neotoma-candidate-taxon-review-priority.v2"
        or provenance.get("schema_version") != "neotoma-candidate-taxon-attribution.v1"
        or review.get("schema_version") != "bijux-pollenomics.taxa-review-projection.v1"
    ):
        raise ValueError("Unsupported review authority schema")
    if any(
        payload.get("lra_accepted_samples") != 0
        or payload.get("publication_allowed") is not False
        for payload in (priority, provenance)
    ):
        raise ValueError("Candidate authorities must remain non-admitting")
    if (
        review.get("authority_role") != "review_projection_not_canonical_classification"
        or review.get("scientific_admission_allowed") is not False
        or review.get("canonical_import_supported") is not False
        or review.get("publication_allowed") is not False
    ):
        raise ValueError("Taxa review claim boundary is unsupported")
    review_digest = digest(
        {key: value for key, value in review.items() if key != "bundle_sha256"}
    )
    if review.get("bundle_sha256") != review_digest:
        raise ValueError("Taxa review bundle digest differs from its content")
    priority_inputs = _input_hashes(priority, "Priority")
    provenance_inputs = _input_hashes(provenance, "Provenance")
    review_file_sha256 = _sha256_identity(
        priority_inputs.get("full_review"), "Taxa review source identity"
    )
    if (
        priority.get("review_bundle_sha256") != review_digest
        or provenance.get("review_bundle_sha256") != review_digest
        or provenance_inputs.get("full_review") != review_file_sha256
        or review_file_sha256 != _review_artifact_sha256(review)
    ):
        raise ValueError("Candidate authorities target another taxa review")
    priority_file_sha256 = _sha256_identity(
        provenance_inputs.get("priority"), "Priority source identity"
    )
    if priority_file_sha256 != _artifact_sha256(priority):
        raise ValueError("Candidate provenance targets another priority projection")
    supplied_provenance_sha256 = _sha256_identity(
        provenance_file_sha256, "Externally pinned provenance source identity"
    )
    if supplied_provenance_sha256 != _artifact_sha256(provenance):
        raise ValueError("Externally pinned provenance identity differs from content")
    common = (
        "source_snapshot_id",
        "raw_manifest_sha256",
        "normalized_manifest_sha256",
        "screen_candidate_ids_sha256",
        "candidate_sample_count",
        "candidate_pollen_observation_count",
        "candidate_review_row_count",
    )
    if any(priority.get(field) != provenance.get(field) for field in common):
        raise ValueError("Candidate authority identities or denominators differ")
    priority_rows = _indexed(_rows(priority, "Priority"), "review_row_id", "Priority")
    provenance_rows = _indexed(
        _rows(provenance, "Provenance"), "review_row_id", "Provenance"
    )
    review_rows = _indexed(_rows(review, "Taxa review"), "review_row_id", "Taxa review")
    full_review_row_count = _count(priority, "full_review_row_count")
    if _count(review, "row_count") != len(review_rows) or full_review_row_count != len(
        review_rows
    ):
        raise ValueError("Full taxa-review denominator does not close")
    expected = _count(priority, "candidate_review_row_count")
    if (
        len(priority_rows) != expected
        or len(provenance_rows) != expected
        or set(priority_rows) != set(provenance_rows)
    ):
        raise ValueError("Candidate concept denominator does not close")
    if sum(
        _count(row, "candidate_observation_count") for row in priority_rows.values()
    ) != _count(priority, "candidate_pollen_observation_count"):
        raise ValueError("Candidate observation denominator does not close")
    return (
        priority_rows,
        provenance_rows,
        review_rows,
        {
            "priority": priority_file_sha256,
            "provenance": supplied_provenance_sha256,
            "taxa_review": review_file_sha256,
        },
    )


def build_lra_parameter_review(
    priority: dict[str, Any],
    provenance: dict[str, Any],
    review: dict[str, Any],
    *,
    provenance_file_sha256: str,
) -> dict[str, Any]:
    """Bind every screened concept to parameter authorities without matching them."""
    initial = tuple(_sha256(value) for value in (priority, provenance, review))
    (
        priority_rows,
        provenance_rows,
        review_rows,
        source_file_sha256,
    ) = _validate_authorities(priority, provenance, review, provenance_file_sha256)
    concept_rows = []
    for identity in sorted(priority_rows):
        mass = priority_rows[identity]
        attribution = provenance_rows[identity]
        source = review_rows.get(identity)
        if source is None or source.get("source_family") != "neotoma":
            raise ValueError("Candidate concept is absent from the Neotoma review")
        fields = (
            "source_identity_sha256",
            "source_reported_name",
            "review_state",
            "candidate_observation_count",
        )
        if any(mass.get(field) != attribution.get(field) for field in fields):
            raise ValueError("Candidate mass and provenance rows differ")
        source_evidence = source.get("supporting_evidence")
        if (
            mass.get("source_identity_sha256") != source.get("source_identity_sha256")
            or mass.get("source_reported_name") != source.get("source_reported_name")
            or not isinstance(source_evidence, dict)
            or mass.get("source_unit") != source_evidence.get("source_unit")
            or mass.get("review_state") != "needs_discussion"
        ):
            raise ValueError("Candidate concept differs from its unresolved source row")
        datasets = attribution.get("source_datasets")
        if (
            not isinstance(datasets, list)
            or any(not isinstance(row, dict) for row in datasets)
            or len(datasets) != attribution.get("candidate_dataset_count")
            or sum(
                _count(cast(dict[str, Any], row), "observation_count")
                for row in datasets
            )
            != _count(mass, "candidate_observation_count")
            or sum(
                _count(cast(dict[str, Any], row), "sample_count") for row in datasets
            )
            != _count(mass, "candidate_sample_count")
        ):
            raise ValueError("Candidate dataset attribution does not reconcile")
        concept_rows.append(
            {
                **mass,
                "candidate_dataset_count": attribution["candidate_dataset_count"],
                "source_datasets": datasets,
                "taxon_decision_status": "not_reviewed",
                "ppe_binding_status": "not_reviewed",
                "fall_speed_binding_status": "not_reviewed",
            }
        )

    parameter_rows = []
    for identity, row in sorted(review_rows.items()):
        candidates = row.get("parameter_candidates")
        if not isinstance(candidates, list):
            raise ValueError("Parameter candidate collection is malformed")
        if not candidates:
            continue
        if row.get("source_family") not in _PARAMETER_SOURCES:
            raise ValueError("Unexpected parameter authority source")
        if any(not isinstance(candidate, dict) for candidate in candidates):
            raise ValueError("Parameter candidate collection is malformed")
        raw_candidates = cast(list[dict[str, Any]], candidates)
        if any(
            candidate.get("approval") != "not_established"
            for candidate in raw_candidates
        ):
            raise ValueError("Parameter authority was promoted before review")
        extracted = parameter_candidates(
            cast(str, row["source_family"]), identity, raw_candidates
        )
        capabilities = [
            kind
            for kind in PARAMETER_KINDS
            if any(
                candidate["parameter_kind"] == kind
                and candidate["parsing_status"] == USABLE_STATUS
                for candidate in extracted
            )
        ]
        parameter_rows.append(
            {
                "parameter_record_id": identity,
                "parameter_record_sha256": _sha256(row),
                "source_identity_sha256": row["source_identity_sha256"],
                "source_family": row["source_family"],
                "source_reported_name": row["source_reported_name"],
                "capabilities": capabilities,
                "parameter_candidates": extracted,
                "source_parameter_candidates": raw_candidates,
                "supporting_evidence": row["supporting_evidence"],
                "approval_status": "not_established",
            }
        )
    if not parameter_rows:
        raise ValueError("No parameter authority rows are available for review")
    if not any(row["capabilities"] for row in parameter_rows):
        raise ValueError("No usable PPE or fall-speed parameter is available")

    contract = review.get("classification_contract")
    if not isinstance(contract, dict) or not contract:
        raise ValueError("Classification contract is unavailable")
    payload: dict[str, Any] = {
        "schema_version": "neotoma-lra-parameter-review.v1",
        "reviewer_authority": "declared_not_authenticated",
        "input_content_sha256": {
            "priority": initial[0],
            "provenance": initial[1],
            "taxa_review": initial[2],
        },
        "declared_source_file_sha256": source_file_sha256,
        "provenance_trust_anchor": "externally_supplied_pin_verified_against_content",
        "review_bundle_sha256": review["bundle_sha256"],
        "source_snapshot_id": priority["source_snapshot_id"],
        "raw_manifest_sha256": priority["raw_manifest_sha256"],
        "normalized_manifest_sha256": priority["normalized_manifest_sha256"],
        "screen_candidate_ids_sha256": priority["screen_candidate_ids_sha256"],
        "classification_contract": contract,
        "denominators": {
            "full_review_rows": len(review_rows),
            "candidate_taxon_concepts": len(concept_rows),
            "candidate_samples": priority["candidate_sample_count"],
            "candidate_pollen_observations": priority[
                "candidate_pollen_observation_count"
            ],
            "parameter_authority_rows": len(parameter_rows),
            "projected_review_rows": len(concept_rows) + len(parameter_rows),
            "parameter_authority_capability_counts": dict(
                sorted(
                    Counter(
                        capability
                        for row in parameter_rows
                        for capability in row["capabilities"]
                    ).items()
                )
            ),
        },
        "candidate_taxon_rows": concept_rows,
        "parameter_authority_rows": parameter_rows,
        "parameter_candidate_extraction": "source_specific",
        "taxon_parameter_matching": "not_performed",
        "review_status": "awaiting_qualified_return",
        "lra_accepted_samples": 0,
        "executable_request": None,
        "scientific_acceptance": "not_evaluated",
        "release_acceptance": "not_evaluated",
        "publication_allowed": False,
        "claims_not_made": [
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
    if initial != tuple(_sha256(value) for value in (priority, provenance, review)):
        raise ValueError("Review evidence changed during projection")
    payload["projection_sha256"] = _sha256(payload)
    return cast(dict[str, Any], json.loads(_canonical(payload)))
