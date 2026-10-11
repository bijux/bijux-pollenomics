"""Challenge the exact final-release cell and split-protocol admission boundary."""

from __future__ import annotations

from dataclasses import replace
import json
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservationChannels,
    PollenChannel,
)
from bijux_pollenomics.analysis.lra_validation.contracts import (
    Fold,
    SiteRecord,
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
    site_group_id,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    COHORT_DECISION_PROFILE,
    FINAL_EVALUATION_RELEASE_PROFILE,
    EvaluationPolicy,
    EvaluationScope,
    EvaluationSite,
    FinalEvaluationProtocol,
    FinalEvaluationReleaseAdmission,
    FrozenEvaluationScope,
    Support,
    admit_final_evaluation_release,
    admit_reviewed_evaluation_cohort,
    freeze_evaluation_scope,
    validate_evaluation_policy,
)

from .support import ACCESS, policy_payload


def _records() -> tuple[SiteRecord, ...]:
    return tuple(
        SiteRecord(f"p{index}", f"site:{index}", (), f"block:{index // 2}")
        for index in range(6)
    )


def _frozen(
    by_block: bool,
    *,
    reviewer_id: str = "reviewer:declared",
    supported_observations: bool = False,
) -> FrozenEvaluationScope:
    records = _records()
    sites = tuple(
        EvaluationSite(
            record_id=record.record_id,
            site_id=record.site_id,
            group_id=site_group_id((record.record_id,)),
            block_id=str(record.block_id),
            bin_id="typed-bin",
            strata=(),
            vegetation_observation_id=f"vegetation:{record.record_id}",
            pollen_observation_id=f"pollen:{record.record_id}",
            support=(
                Support(
                    50.0,
                    index * 0.1,
                    10.0,
                    1.0,
                    0.0,
                    100.0,
                    str(index) * 64,
                    "EPSG:4326",
                    "BP",
                    "bounded-footprint-radius-v1",
                    "typed-bp-interval-v1",
                )
                if supported_observations
                else None
            ),
        )
        for index, record in enumerate(records)
    )
    channels = tuple(
        ObservationChannels(
            record_id=record.record_id,
            group_id=site_group_id((record.record_id,)),
            pollen_channels=(
                PollenChannel(
                    f"pollen:{record.record_id}",
                    ("e" if supported_observations else "a") * 64,
                ),
            ),
            vegetation_input_ids=(f"vegetation:{record.record_id}",),
        )
        for record in records
    )
    decisions = {
        "schema_version": COHORT_DECISION_PROFILE,
        "admission_id": "review:release-cohort",
        "reviewer_id": reviewer_id,
        "reviewer_authority": "declared_not_authenticated",
        "decision_date": "2026-09-24",
        "rationale": "Outcome-free identities were reviewed before release admission.",
        "candidate_source_manifest_sha256": "b" * 64,
        "outcome_access_status": "not_started",
        "decisions": [
            {
                "record_id": record.record_id,
                "decision": "admitted",
                "reason_codes": ["reviewed_identity_and_support"],
                "evidence_reference_ids": [f"evidence:{record.record_id}"],
            }
            for record in records
        ],
    }
    cohort = admit_reviewed_evaluation_cohort(
        canonical_json(decisions),
        manifest_sha256(decisions),
        records=records,
        sites=sites,
        observation_channels=channels,
        dependency_graph=tuple(
            [(record.record_id, ()) for record in records]
            + (
                [(f"pollen:{record.record_id}", ()) for record in records]
                if supported_observations
                else []
            )
        ),
        taxa=("a", "b"),
    )
    return freeze_evaluation_scope(
        cohort,
        scope_id="synthetic-release-boundary",
        by_block=by_block,
    )


def _policy(scope: EvaluationScope, *, omit: str | None = None) -> EvaluationPolicy:
    payload = policy_payload(scope)
    base: dict[str, Any] = {
        key: value
        for key, value in payload["cells"][0].items()
        if key not in {"cell_id", "experiment", "target"}
    }
    matrix = (
        ("local-vegetation", "local_pollen_available", "vegetation_cover"),
        (
            "withheld-vegetation",
            "all_target_pollen_withheld",
            "vegetation_cover",
        ),
        ("withheld-pollen", "all_target_pollen_withheld", "pollen_composition"),
    )
    payload["cells"] = [
        dict(base, cell_id=cell_id, experiment=experiment, target=target)
        for cell_id, experiment, target in matrix
        if cell_id != omit
    ]
    return validate_evaluation_policy(payload, scope=scope, first_test_access_at=ACCESS)


def _protocols(
    *, supported_observations: bool = False
) -> tuple[FinalEvaluationProtocol, FinalEvaluationProtocol]:
    grouped = _frozen(False, supported_observations=supported_observations)
    block = _frozen(True, supported_observations=supported_observations)
    return (
        FinalEvaluationProtocol(
            "grouped_outer",
            grouped.scope,
            grouped.cohort_admission,
            _policy(grouped.scope),
            grouped.canonical_split_manifest_json,
            grouped.split_manifest_sha256,
        ),
        FinalEvaluationProtocol(
            "spatial_block",
            block.scope,
            block.cohort_admission,
            _policy(block.scope),
            block.canonical_split_manifest_json,
            block.split_manifest_sha256,
        ),
    )


def test_exact_six_cell_two_protocol_matrix_is_engineering_admitted() -> None:
    admission = admit_final_evaluation_release(_protocols())
    payload = json.loads(admission.canonical_admission_json)
    assert payload["profile"] == FINAL_EVALUATION_RELEASE_PROFILE
    assert payload["engineering_admission"] == "admitted"
    assert payload["empirical_evaluation_performed"] is False
    assert payload["scientific_acceptance"] == "not_evaluated"
    assert (
        payload["cohort_admission_sha256"]
        == payload["protocols"][0]["cohort_admission_sha256"]
    )
    assert len(payload["protocols"]) == 2
    assert sum(len(protocol["cells"]) for protocol in payload["protocols"]) == 6


def test_missing_cell_or_protocol_refuses() -> None:
    grouped, block = _protocols()
    incomplete = replace(grouped, policy=_policy(grouped.scope, omit="withheld-pollen"))
    with pytest.raises(ValidationRefusal, match="exactly local-pollen"):
        admit_final_evaluation_release((incomplete, block))
    with pytest.raises(ValidationRefusal, match="exactly grouped-outer"):
        admit_final_evaluation_release((grouped,))


def test_different_review_admission_between_protocols_refuses() -> None:
    grouped, block = _protocols()
    different = _frozen(True, reviewer_id="reviewer:different")
    changed = replace(block, cohort_admission=different.cohort_admission)
    with pytest.raises(ValidationRefusal, match="same cohort admission"):
        admit_final_evaluation_release((grouped, changed))


@pytest.mark.parametrize("mutation", ["kind", "digest"])
def test_wrong_split_kind_or_digest_refuses(mutation: str) -> None:
    grouped, block = _protocols()
    manifest = json.loads(grouped.canonical_split_manifest_json)
    if mutation == "kind":
        manifest["split_kind"] = "predefined_block"
        changed = replace(
            grouped,
            canonical_split_manifest_json=canonical_json(manifest),
            split_manifest_sha256=manifest_sha256(manifest),
        )
    else:
        changed = replace(grouped, split_manifest_sha256="f" * 64)
    with pytest.raises(ValidationRefusal):
        admit_final_evaluation_release((changed, block))


def test_arbitrary_group_disjoint_fold_is_not_a_canonical_grouped_outer_protocol() -> (
    None
):
    grouped, block = _protocols()
    arbitrary = Fold(
        "arbitrary",
        ("p0", "p1", "p2"),
        ("p3", "p4", "p5"),
        tuple(site_group_id((f"p{index}",)) for index in range(3)),
        tuple(site_group_id((f"p{index}",)) for index in range(3, 6)),
    )
    scope = replace(grouped.scope, folds=(arbitrary,))
    manifest = json.loads(grouped.canonical_split_manifest_json)
    manifest["folds"] = [arbitrary.as_dict()]
    changed = FinalEvaluationProtocol(
        "grouped_outer",
        scope,
        grouped.cohort_admission,
        _policy(scope),
        canonical_json(manifest),
        manifest_sha256(manifest),
    )
    with pytest.raises(ValidationRefusal, match="canonical deterministic"):
        admit_final_evaluation_release((changed, block))


def test_spatial_protocol_refuses_train_test_members_of_one_block() -> None:
    grouped, block = _protocols()
    arbitrary = Fold(
        "shared-block",
        ("p1", "p2", "p3", "p4", "p5"),
        ("p0",),
        tuple(site_group_id((f"p{index}",)) for index in range(1, 6)),
        (site_group_id(("p0",)),),
    )
    scope = replace(block.scope, folds=(arbitrary,))
    manifest = json.loads(block.canonical_split_manifest_json)
    manifest["folds"] = [arbitrary.as_dict()]
    changed = FinalEvaluationProtocol(
        "spatial_block",
        scope,
        block.cohort_admission,
        _policy(scope),
        canonical_json(manifest),
        manifest_sha256(manifest),
    )
    with pytest.raises(ValidationRefusal, match="block-exclusive"):
        admit_final_evaluation_release((grouped, changed))


def test_recomputed_receipt_cannot_add_claims_or_replace_protocols() -> None:
    admission = admit_final_evaluation_release(_protocols())
    original = json.loads(admission.canonical_admission_json)
    for mutation in ("reviewer", "outcome", "protocols"):
        payload = json.loads(json.dumps(original))
        if mutation == "reviewer":
            payload["reviewer_approved"] = True
        elif mutation == "outcome":
            payload["empirical_accuracy"] = 1.0
        else:
            payload["protocols"] = []
        canonical = canonical_json(payload)
        with pytest.raises(ValidationRefusal, match="receipt|protocol"):
            FinalEvaluationReleaseAdmission(canonical, manifest_sha256(payload))
