from __future__ import annotations


from tests.support.repository import REPOSITORY_ROOT
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.sead.collection import (
    SEAD_GOVERNED_ACQUISITION_ID,
)
from bijux_pollenomics.collection.sources.sead.evidence.claims import (
    build_sead_chronology_claim_bundle,
)
from bijux_pollenomics.collection.sources.sead.evidence.reader import (
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    governed_sead_evidence_root,
    read_validated_sead_evidence_document,
)

pytestmark = pytest.mark.generated_artifacts

_REPOSITORY_ROOT = REPOSITORY_ROOT
_ACQUISITION_ROOT = (
    _REPOSITORY_ROOT / "data/sead/raw/acquisitions" / SEAD_GOVERNED_ACQUISITION_ID
)
_EVIDENCE_ROOT = governed_sead_evidence_root(_REPOSITORY_ROOT / "data")


def test_admitted_sead_claims_reconcile_and_match_the_generated_bundle() -> None:
    bundle = build_sead_chronology_claim_bundle(_ACQUISITION_ROOT)
    authoritative = read_validated_sead_evidence_document(
        _EVIDENCE_ROOT,
        "chronology_claims.json",
        expected_run_id=SEAD_GOVERNED_ACQUISITION_ID,
        expected_manifest_sha256=SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )

    assert bundle["claim_count"] == 25_109
    assert bundle["country_counts"] == {
        "DK": 1_939,
        "FI": 59,
        "NO": 468,
        "SE": 22_643,
    }
    assert bundle["claim_type_counts"] == {
        "analysis_entity_age": 641,
        "dating_range": 7_377,
        "dendrochronology": 6_947,
        "geochronology": 87,
        "relative_period": 10_057,
    }
    assert bundle["comparability_counts"] == {
        "comparable": 14_324,
        "context_only": 10_144,
        "unresolved": 641,
    }
    assert bundle["chronology_eligibility_counts"] == {
        "eligible": 14_324,
        "refused": 10_785,
    }
    assert bundle["propagation_status"] == "refused"
    assert bundle["propagation_reason_code"] == "source_classification_not_accepted"
    assert authoritative["propagation_status"] == "refused"
    assert (
        authoritative["propagation_reason_code"] == "source_classification_not_accepted"
    )
    assert authoritative["claim_count"] == bundle["claim_count"]
    source_claims = cast(list[dict[str, object]], bundle["claims"])
    authoritative_claims = cast(list[dict[str, object]], authoritative["claims"])
    assert [claim["chronology_claim_id"] for claim in authoritative_claims] == [
        claim["chronology_claim_id"] for claim in source_claims
    ]
    assert all(
        claim["propagation_eligibility"] == "refused"
        and isinstance(claim["observation_relation_id"], str)
        and claim["propagation_reason_codes"]
        in (
            ["source_classification_not_accepted"],
            ["source_native_observation_unavailable_at_analysis_entity"],
        )
        for claim in authoritative_claims
    )


def test_every_sead_claim_retains_subject_geography_and_raw_parent_identity() -> None:
    bundle = build_sead_chronology_claim_bundle(_ACQUISITION_ROOT)
    claims = cast(list[dict[str, object]], bundle["claims"])

    assert all(claim["country_code"] in {"SE", "DK", "NO", "FI"} for claim in claims)
    assert all(isinstance(claim["site_uuid"], str) for claim in claims)
    assert all(isinstance(claim["analysis_entity_id"], int) for claim in claims)
    assert all(isinstance(claim["source_payload_sha256"], str) for claim in claims)
    assert all(
        claim["selection_rule_version"] == "sead-retain-all-source-chronologies-v1"
        for claim in claims
    )
    eligible = [
        claim for claim in claims if claim["chronology_eligibility"] == "eligible"
    ]
    assert len(eligible) == 14_324
    assert all(isinstance(claim["younger_bp"], int) for claim in eligible)
    assert all(isinstance(claim["older_bp"], int) for claim in eligible)
