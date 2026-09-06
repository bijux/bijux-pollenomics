"""Reconcile governed SEAD chronology claims by country."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from ....evidence.sources.sead import (
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    governed_sead_evidence_root,
    read_validated_sead_evidence_document,
)
from ...release_evidence.models import _COUNTRIES
from .model import DerivedCount


def sead_chronology_claim_values(
    root: Path, metric: str
) -> dict[str, DerivedCount] | None:
    """Derive country posture from the validated governed SEAD claims."""
    if metric != "chronology_eligibility":
        return None
    try:
        document = read_validated_sead_evidence_document(
            governed_sead_evidence_root(root / "data"),
            "chronology_claims.json",
            expected_run_id=SEAD_GOVERNED_EVIDENCE_RUN_ID,
            expected_manifest_sha256=SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        )
    except (OSError, TypeError, ValueError):
        return None
    if (
        document.get("schema_version") != "sead-chronology-claim-bundle.v1"
        or document.get("propagation_status") != "refused"
        or document.get("propagation_reason_code")
        != "source_classification_not_accepted"
    ):
        return None
    claims = document.get("claims")
    if not isinstance(claims, list):
        return None
    counts = {
        country: {"accepted": 0, "unresolved": 0, "refused": 0}
        for country in _COUNTRIES
    }
    for claim in claims:
        if not isinstance(claim, Mapping):
            return None
        country = claim.get("country_code")
        comparability = claim.get("comparability_status")
        eligibility = claim.get("chronology_eligibility")
        if country not in counts:
            return None
        if comparability == "comparable" and eligibility == "eligible":
            bucket = "accepted"
        elif comparability in {"context_only", "refused"} and eligibility == "refused":
            bucket = "refused"
        elif comparability == "unresolved" and eligibility == "refused":
            bucket = "unresolved"
        else:
            return None
        counts[cast(str, country)][bucket] += 1
    values = {}
    for country, partition in counts.items():
        accepted = partition["accepted"]
        unresolved = partition["unresolved"]
        refused = partition["refused"]
        values[country] = DerivedCount(
            candidate=accepted + unresolved + refused,
            eligible=accepted + refused,
            accepted=accepted,
            unresolved=unresolved,
            excluded=0,
            refused=refused,
        )
    declared_count = document.get("claim_count")
    if (
        isinstance(declared_count, bool)
        or not isinstance(declared_count, int)
        or declared_count != sum(value.candidate for value in values.values())
    ):
        return None
    return values
