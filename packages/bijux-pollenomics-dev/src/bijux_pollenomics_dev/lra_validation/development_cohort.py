"""Bind previously exposed development data without reviewed-test admission.

This declaration can authorize a local retained-score audit. It is deliberately
incompatible with the production reviewed evaluation cohort receipt.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import cast

from .development_design import canonical_json

PROFILE = "pollenomics-prior-exposed-development-cohort.v1"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS = {
    "profile",
    "admission_class",
    "outcome_access_status",
    "scientific_acceptance",
    "confirmatory_result",
    "canonical_scope_json",
    "scope_sha256",
    "source_manifest_sha256",
    "admitted_record_ids",
}
_SCOPE_FIELDS = {
    "schema_version",
    "experiment",
    "target",
    "support",
    "split_manifest_sha256",
}


def validate_development_cohort(
    canonical: str,
    digest: str,
    *,
    experiment: object,
    target: object,
    input_hashes: dict[str, object],
) -> str:
    """Return the exact scope digest after enforcing development-only custody."""
    loaded: object = json.loads(canonical)
    if not isinstance(loaded, dict) or set(loaded) != _FIELDS:
        raise ValueError("invalid_development_cohort_fields")
    payload = cast(dict[str, object], loaded)
    if (
        canonical_json(payload) != canonical
        or hashlib.sha256(canonical.encode()).hexdigest() != digest
        or payload["profile"] != PROFILE
        or payload["admission_class"] != "prior_exposed_development_only"
        or payload["outcome_access_status"] != "previously_exposed"
        or payload["scientific_acceptance"] != "not_evaluated"
        or payload["confirmatory_result"] is not False
    ):
        raise ValueError("invalid_development_cohort_claim")
    for name in ("scope_sha256", "source_manifest_sha256"):
        value = payload[name]
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise ValueError("invalid_development_cohort_digest")
    records = payload["admitted_record_ids"]
    if (
        not isinstance(records, list)
        or not records
        or any(not isinstance(value, str) or not value.strip() for value in records)
        or records != sorted(set(records))
    ):
        raise ValueError("invalid_development_cohort_records")
    scope_json = payload["canonical_scope_json"]
    if not isinstance(scope_json, str):
        raise ValueError("invalid_development_cohort_scope")
    scope: object = json.loads(scope_json)
    if (
        not isinstance(scope, dict)
        or set(scope) != _SCOPE_FIELDS
        or canonical_json(scope) != scope_json
        or hashlib.sha256(scope_json.encode()).hexdigest() != payload["scope_sha256"]
        or scope["schema_version"] != "pollenomics-prior-exposed-development-scope.v1"
        or (scope["experiment"], scope["target"]) != (experiment, target)
        or (experiment, target) != ("all_target_pollen_withheld", "pollen_composition")
        or not isinstance(scope["support"], dict)
        or not scope["support"]
        or input_hashes.get("development_source_manifest")
        != payload["source_manifest_sha256"]
        or input_hashes.get("target_support") != payload["scope_sha256"]
        or input_hashes.get("split_manifest") != scope["split_manifest_sha256"]
    ):
        raise ValueError("development_cohort_scope_mismatch")
    return payload["scope_sha256"]
