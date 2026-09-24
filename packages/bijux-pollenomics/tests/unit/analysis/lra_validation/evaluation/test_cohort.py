"""Verify decision-bound cohorts freeze value-free evaluation scopes."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservationChannels,
    PollenChannel,
)
from bijux_pollenomics.analysis.lra_validation.contracts import (
    SiteRecord,
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
    site_group_id,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    COHORT_ADMISSION_PROFILE,
    COHORT_DECISION_PROFILE,
    EvaluationSite,
    FrozenEvaluationScope,
    ReviewedEvaluationCohort,
    admit_reviewed_evaluation_cohort,
    freeze_evaluation_scope,
)


def _inputs() -> tuple[
    tuple[SiteRecord, ...],
    tuple[EvaluationSite, ...],
    tuple[ObservationChannels, ...],
]:
    records = (
        SiteRecord("record:a", "site:a", (), "north"),
        SiteRecord("record:b", "site:b", ("record:c",), "south"),
        SiteRecord("record:c", "site:c", (), "south"),
    )
    groups = {
        "record:a": site_group_id(("record:a",)),
        "record:b": site_group_id(("record:b", "record:c")),
        "record:c": site_group_id(("record:b", "record:c")),
    }
    sites = tuple(
        EvaluationSite(
            record_id=record.record_id,
            site_id=record.site_id,
            group_id=groups[record.record_id],
            block_id=str(record.block_id),
            bin_id="bin:1000bp",
            strata=("country:SE",),
            vegetation_observation_id=f"vegetation:{record.record_id}",
            pollen_observation_id=f"pollen:{record.record_id}",
            support=None,
        )
        for record in records
    )
    channels = tuple(
        ObservationChannels(
            record_id=record.record_id,
            group_id=groups[record.record_id],
            pollen_channels=(
                PollenChannel(f"pollen-input:{record.record_id}", "a" * 64),
            ),
            vegetation_input_ids=(f"vegetation-input:{record.record_id}",),
        )
        for record in records
    )
    return records, sites, channels


def _decision_manifest() -> dict[str, object]:
    return {
        "schema_version": COHORT_DECISION_PROFILE,
        "admission_id": "review:declared-cohort",
        "reviewer_id": "reviewer:declared",
        "reviewer_authority": "declared_not_authenticated",
        "decision_date": "2026-09-24",
        "rationale": "Identity and support decisions were recorded before outcomes.",
        "candidate_source_manifest_sha256": "b" * 64,
        "outcome_access_status": "not_started",
        "decisions": [
            {
                "record_id": record_id,
                "decision": "admitted",
                "reason_codes": ["reviewed_identity_and_support"],
                "evidence_reference_ids": [f"evidence:{record_id}"],
            }
            for record_id in ("record:a", "record:b", "record:c")
        ]
        + [
            {
                "record_id": "record:refused",
                "decision": "refused",
                "reason_codes": ["independent_vegetation_not_admitted"],
                "evidence_reference_ids": ["evidence:refusal"],
            }
        ],
    }


def _cohort(
    manifest: dict[str, object] | None = None,
    *,
    records: tuple[SiteRecord, ...] | None = None,
    sites: tuple[EvaluationSite, ...] | None = None,
    channels: tuple[ObservationChannels, ...] | None = None,
) -> ReviewedEvaluationCohort:
    default_records, default_sites, default_channels = _inputs()
    records = default_records if records is None else records
    sites = default_sites if sites is None else sites
    channels = default_channels if channels is None else channels
    payload = _decision_manifest() if manifest is None else manifest
    return admit_reviewed_evaluation_cohort(
        canonical_json(payload),
        manifest_sha256(payload),
        records=records,
        sites=sites,
        observation_channels=channels,
        dependency_graph=tuple((record.record_id, ()) for record in records),
        taxa=("taxon:a", "taxon:b"),
    )


@pytest.mark.parametrize(
    "by_block,kind,folds",
    [(False, "leave_one_site_group_out", 2), (True, "predefined_block", 2)],
)
def test_decision_bound_cohort_freezes_canonical_scope(
    by_block: bool, kind: str, folds: int
) -> None:
    frozen = freeze_evaluation_scope(
        _cohort(), scope_id="scope:reviewed", by_block=by_block
    )
    admission = json.loads(frozen.canonical_admission_json)
    split = json.loads(frozen.canonical_split_manifest_json)
    assert admission["profile"] == COHORT_ADMISSION_PROFILE
    assert admission["reviewer_authority"] == "declared_not_authenticated"
    assert admission["empirical_evaluation_performed"] is False
    assert admission["scientific_acceptance"] == "not_evaluated"
    assert split["split_kind"] == kind
    assert len(frozen.scope.folds) == folds


def test_stale_manifest_and_per_record_review_mutation_refuse_or_rebind() -> None:
    payload = _decision_manifest()
    canonical = canonical_json(payload)
    records, sites, channels = _inputs()

    def admit(canonical_json_value: str, sha256: str) -> ReviewedEvaluationCohort:
        return admit_reviewed_evaluation_cohort(
            canonical_json_value,
            sha256,
            records=records,
            sites=sites,
            observation_channels=channels,
            dependency_graph=tuple((record.record_id, ()) for record in records),
            taxa=("taxon:a", "taxon:b"),
        )

    with pytest.raises(ValidationRefusal, match="digest"):
        admit(canonical, "f" * 64)
    changed = json.loads(canonical)
    changed["decisions"][-1]["reason_codes"] = ["different_refusal_reason"]
    rebound = admit(canonical_json(changed), manifest_sha256(changed))
    assert rebound.decision_manifest_sha256 != _cohort().decision_manifest_sha256
    reordered = json.loads(canonical)
    reordered["decisions"].reverse()
    with pytest.raises(ValidationRefusal, match="canonical record order"):
        admit(canonical_json(reordered), manifest_sha256(reordered))


def test_record_site_channel_universe_and_derived_groups_refuse() -> None:
    cohort = _cohort()
    with pytest.raises(ValidationRefusal, match="universes"):
        freeze_evaluation_scope(
            _cohort(sites=cohort.sites[:-1]),
            scope_id="scope:missing-site",
            by_block=False,
        )
    wrong_site = replace(cohort.sites[0], group_id=site_group_id(("record:b",)))
    with pytest.raises(ValidationRefusal, match="canonically derived"):
        freeze_evaluation_scope(
            _cohort(sites=(wrong_site, *cohort.sites[1:])),
            scope_id="scope:wrong-group",
            by_block=False,
        )


def test_input_permutation_retains_scope_and_admission_identity() -> None:
    cohort = _cohort()
    permuted = _cohort(
        records=tuple(reversed(cohort.records)),
        sites=tuple(reversed(cohort.sites)),
        channels=tuple(reversed(cohort.observation_channels)),
    )
    first = freeze_evaluation_scope(cohort, scope_id="scope:same", by_block=False)
    second = freeze_evaluation_scope(permuted, scope_id="scope:same", by_block=False)
    assert first.scope.scope_sha256 == second.scope.scope_sha256
    assert first.admission_sha256 == second.admission_sha256
    assert first.canonical_split_manifest_json == second.canonical_split_manifest_json


def test_cohort_and_frozen_scope_cannot_be_caller_forged() -> None:
    cohort = _cohort()
    frozen = freeze_evaluation_scope(cohort, scope_id="scope:factory", by_block=False)
    with pytest.raises(ValidationRefusal, match="canonical manifest factory"):
        ReviewedEvaluationCohort(
            cohort.canonical_decision_manifest_json,
            cohort.decision_manifest_sha256,
            cohort.admitted_record_ids,
            cohort.refused_record_ids,
            cohort.records,
            cohort.sites,
            cohort.observation_channels,
            cohort.dependency_graph,
            cohort.taxa,
            cohort.external_inputs,
        )
    with pytest.raises(ValidationRefusal, match="reviewed factory"):
        FrozenEvaluationScope(
            frozen.scope,
            frozen.canonical_split_manifest_json,
            frozen.split_manifest_sha256,
            frozen.cohort_admission,
        )
