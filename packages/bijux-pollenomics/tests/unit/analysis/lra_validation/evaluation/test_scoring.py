from __future__ import annotations

from dataclasses import replace
import json
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservationChannels,
    ObservedPollenAdmission,
    PollenChannel,
)
from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.evaluation import scoring
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    evaluate_final,
    validate_evaluation_policy,
)

from .support import (
    ACCESS,
    bind_prediction,
    policy_fixture,
    policy_payload,
    rows_fixture,
    scope_fixture,
    typed_policy_fixture,
    typed_rows_fixture,
)


def test_separate_target_success_keeps_independent_denominators() -> None:
    scope = scope_fixture()
    rows = rows_fixture(scope)
    policy = policy_fixture(scope)
    result = evaluate_final(policy, scope=scope, rows=rows)
    assert scoring._evaluate_final_ledger(policy, scope=scope, rows=rows) == result
    payload = json.loads(result.canonical_result_json)
    assert result.status == "passed"
    assert {cell["target"] for cell in payload["cells"]} == {
        "vegetation_cover",
        "pollen_composition",
    }
    assert all(cell["paired_scored_groups"] == 6 for cell in payload["cells"])
    assert payload["scientific_approval_granted"] is False
    assert payload["schema_version"] == "pollenomics-final-evaluation-result.v2"
    assert all("model_fit_sha256" in row for row in payload["paired_evidence"])


def test_typed_sources_emit_v3_without_fitted_baseline_aliases() -> None:
    scope = scope_fixture()
    policy, rows = typed_policy_fixture(scope), typed_rows_fixture(scope)
    result = evaluate_final(policy, scope=scope, rows=rows)
    payload = json.loads(result.canonical_result_json)
    assert payload["schema_version"] == "pollenomics-final-evaluation-result.v3"
    for row in payload["paired_evidence"]:
        assert row["model_source"]["kind"] == "fitted_spatial"
        assert row["baseline_source"]["kind"] == (
            "admitted_reconstruction_training_mean"
        )
        assert not any("fit_sha256" in key for key in row)
        assert {"model_input_ids", "baseline_input_ids"} <= set(row)


def test_typed_and_legacy_prediction_rows_cannot_share_one_result() -> None:
    scope = scope_fixture()
    policy, rows = typed_policy_fixture(scope), typed_rows_fixture(scope)
    legacy = bind_prediction(
        replace(
            rows[0],
            prediction_sha256=None,
            prediction_manifest_json=None,
            source_model=None,
        )
    )
    with pytest.raises(ValidationRefusal, match="cannot mix"):
        evaluate_final(policy, scope=scope, rows=(legacy, *rows[1:]))


def test_outcome_perturbation_changes_only_scores_and_not_frozen_predictions() -> None:
    scope = scope_fixture()
    rows = rows_fixture(scope)
    policy = policy_fixture(scope)
    changed = tuple(
        replace(row, observation=(("a", 0.1), ("b", 0.9)))
        if row.target == "vegetation_cover"
        else row
        for row in rows
    )
    assert [r.prediction_sha256 for r in changed] == [r.prediction_sha256 for r in rows]
    result = json.loads(
        evaluate_final(policy, scope=scope, rows=changed).canonical_result_json
    )
    assert {x["target"]: x["status"] for x in result["cells"]} == {
        "vegetation_cover": "failed",
        "pollen_composition": "passed",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_row",
        "duplicate",
        "changed_prediction",
        "late_prediction",
        "fit_leakage",
        "observation_mismatch",
    ],
)
def test_anti_leak_and_inventory_refusals(mutation: str) -> None:
    scope = scope_fixture()
    rows = rows_fixture(scope)
    if mutation == "missing_row":
        rows = rows[:-1]
    elif mutation == "duplicate":
        rows = (*rows, rows[0])
    elif mutation == "changed_prediction":
        rows = (replace(rows[0], prediction=(("a", 0.7), ("b", 0.3))), *rows[1:])
    elif mutation == "late_prediction":
        rows = (
            bind_prediction(replace(rows[0], prediction_frozen_at=ACCESS)),
            *rows[1:],
        )
    elif mutation == "fit_leakage":
        rows = (
            bind_prediction(replace(rows[0], fit_input_ids=("p0", "p2"))),
            *rows[1:],
        )
    else:
        rows = (replace(rows[0], observation=(("a", 0.7), ("b", 0.3))), *rows[1:])
    with pytest.raises(ValidationRefusal):
        evaluate_final(policy_fixture(scope), scope=scope, rows=rows)


def test_missing_is_not_zero_and_required_interval_is_not_bootstrap() -> None:
    scope = scope_fixture()
    rows = rows_fixture(scope)
    policy = policy_fixture(scope)
    missing = tuple(
        replace(row, observation=(("a", None), ("b", 4)))
        if row.target == "pollen_composition"
        else row
        for row in rows
    )
    result = json.loads(
        evaluate_final(policy, scope=scope, rows=missing).canonical_result_json
    )
    assert result["cells"][1]["status"] == "ineligible"
    no_intervals = tuple(bind_prediction(replace(row, interval=None)) for row in rows)
    assert evaluate_final(policy, scope=scope, rows=no_intervals).status == "ineligible"


def test_zero_count_total_has_distinct_missing_status() -> None:
    scope = scope_fixture()
    rows = tuple(
        replace(row, observation=(("a", 0), ("b", 0)))
        if row.target == "pollen_composition"
        else row
        for row in rows_fixture(scope)
    )
    result = json.loads(
        evaluate_final(
            policy_fixture(scope), scope=scope, rows=rows
        ).canonical_result_json
    )
    assert any(x["status"] == "zero_total_count" for x in result["row_statuses"])
    assert result["cells"][1]["paired_scored_groups"] == 0


def test_buffer_uses_unrounded_wgs84_distance_and_support_refusals() -> None:
    scope = scope_fixture()
    payload = policy_payload(scope)
    payload["minimum_buffer_m"] = 4_000_000
    policy = validate_evaluation_policy(
        payload, scope=scope, first_test_access_at=ACCESS
    )
    result = json.loads(
        evaluate_final(
            policy, scope=scope, rows=rows_fixture(scope)
        ).canonical_result_json
    )
    assert result["status"] == "ineligible"
    assert all(
        x["status"] == "spatial_buffer_violation" for x in result["row_statuses"]
    )


def test_local_pollen_available_supports_only_independent_vegetation() -> None:
    scope = scope_fixture()
    scope = replace(
        scope,
        observation_channels=tuple(
            ObservationChannels(
                site.record_id,
                site.group_id,
                (PollenChannel(site.pollen_observation_id, "a" * 64),),
                (site.vegetation_observation_id,),
            )
            for site in scope.sites
        ),
        dependency_graph=(
            *scope.dependency_graph,
            *((site.pollen_observation_id, ()) for site in scope.sites),
        ),
    )
    payload = policy_payload(scope)
    payload["cells"] = payload["cells"][:1]
    payload["cells"][0]["experiment"] = "local_pollen_available"
    policy = validate_evaluation_policy(
        payload, scope=scope, first_test_access_at=ACCESS
    )
    rows = tuple(
        bind_prediction(
            replace(
                row,
                experiment="local_pollen_available",
                fit_input_ids=(*row.fit_input_ids, "pollen:" + row.record_id[1:]),
                observed_pollen=ObservedPollenAdmission(
                    row.record_id,
                    "g" + row.record_id[1:],
                    (PollenChannel("pollen:" + row.record_id[1:], "a" * 64),),
                ),
            )
        )
        for row in rows_fixture(scope)
        if row.target == "vegetation_cover"
    )
    assert evaluate_final(policy, scope=scope, rows=rows).status == "passed"


def test_frozen_taxon_universe_prevents_dropping_a_dominant_taxon() -> None:
    scope = scope_fixture()
    rows = tuple(
        bind_prediction(
            replace(
                row,
                prediction=(("a", 1.0),),
                observation=(("a", 1.0 if row.target == "vegetation_cover" else 10),),
                interval=None,
            )
        )
        for row in rows_fixture(scope)
    )
    result = json.loads(
        evaluate_final(
            policy_fixture(scope), scope=scope, rows=rows
        ).canonical_result_json
    )
    assert result["status"] == "ineligible"
    assert all(
        row["status"] == "prediction_failed_taxon_denominator"
        for row in result["row_statuses"]
    )
    assert all(cell["failed_prediction_groups"] == 6 for cell in result["cells"])


def test_freeze_adapter_refuses_outcomes_or_existing_bindings() -> None:
    from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
        freeze_evaluation_prediction,
    )

    row = rows_fixture(scope_fixture())[0]
    with pytest.raises(ValidationRefusal):
        freeze_evaluation_prediction(row)
    unbound = replace(
        row,
        observation=None,
        prediction_sha256=None,
        prediction_manifest_json=None,
        prediction_frozen_at=None,
    )
    frozen = freeze_evaluation_prediction(unbound)
    assert frozen.prediction_sha256 is not None
    assert frozen.prediction_frozen_at is not None
    assert frozen.observation is None
    with pytest.raises(ValidationRefusal):
        freeze_evaluation_prediction(frozen)


def test_mismatched_temporal_or_footprint_support_remains_excluded() -> None:
    scope = scope_fixture()
    original = rows_fixture(scope)
    for kind in ("time", "footprint"):
        changed = []
        for row in original:
            assert row.observation_support is not None
            support = (
                replace(row.observation_support, older_bp=101)
                if kind == "time"
                else replace(row.observation_support, footprint_sha256="f" * 64)
            )
            changed.append(replace(row, observation_support=support))
        result = json.loads(
            evaluate_final(
                policy_fixture(scope), scope=scope, rows=tuple(changed)
            ).canonical_result_json
        )
        assert result["status"] == "ineligible"
        assert all(
            row["status"] == "unsupported_observation_support"
            for row in result["row_statuses"]
        )


def test_required_subgroup_has_its_own_denominator_floor() -> None:
    scope = scope_fixture()
    payload = policy_payload(scope)
    payload["cells"][0]["minimum_sites"] = 7
    policy = validate_evaluation_policy(
        payload, scope=scope, first_test_access_at=ACCESS
    )
    result = json.loads(
        evaluate_final(
            policy, scope=scope, rows=rows_fixture(scope)
        ).canonical_result_json
    )
    assert result["cells"][0]["status"] == "ineligible"
    assert result["cells"][1]["status"] == "passed"


def test_modeled_hyde_or_published_reconstruction_is_not_measured_truth() -> None:
    scope = scope_fixture()
    for kind in ("modeled_land_use", "published_reconstruction"):
        rows = tuple(
            replace(row, observation_kind=kind)
            if row.target == "vegetation_cover"
            else row
            for row in rows_fixture(scope)
        )
        with pytest.raises(ValidationRefusal, match="not independent observed"):
            evaluate_final(policy_fixture(scope), scope=scope, rows=rows)


@pytest.mark.parametrize(
    "mutation",
    [
        "latent",
        "no_observation_process",
        "wrong_nominal",
        "bad_bounds",
        "missing_taxon",
    ],
)
def test_interval_semantics_are_checked_before_coverage(mutation: str) -> None:
    scope = scope_fixture()
    rows = rows_fixture(scope)
    row = rows[0]
    assert row.interval is not None
    if mutation == "latent":
        interval = replace(row.interval, uncertainty_kind="latent_composition")
    elif mutation == "no_observation_process":
        interval = replace(row.interval, propagated_sources=("PPE_only",))
    elif mutation == "wrong_nominal":
        interval = replace(row.interval, nominal_coverage=0.95)
    elif mutation == "bad_bounds":
        interval = replace(row.interval, limits=(("a", -0.1, 1), ("b", 0, 1)))
    else:
        interval = replace(row.interval, limits=(("a", 0, 1),))
    changed = (bind_prediction(replace(row, interval=interval)), *rows[1:])
    with pytest.raises(ValidationRefusal):
        evaluate_final(policy_fixture(scope), scope=scope, rows=changed)


def test_external_regional_source_participates_in_buffer_closure() -> None:
    from bijux_pollenomics.analysis.lra_validation.evaluation.api import ExternalInput

    scope = scope_fixture()
    target = scope.sites[2]
    assert target.support is not None
    external = ExternalInput(
        "external-regional-pollen", "observed_source", "e" * 64, target.support
    )
    scope = replace(
        scope,
        external_inputs=(external,),
        dependency_graph=(*scope.dependency_graph, (external.input_id, ())),
    )
    rows = tuple(
        bind_prediction(
            replace(row, fit_input_ids=(*row.fit_input_ids, external.input_id))
        )
        for row in rows_fixture(scope)
    )
    result = json.loads(
        evaluate_final(
            policy_fixture(scope), scope=scope, rows=rows
        ).canonical_result_json
    )
    assert all(
        row["status"] == "spatial_buffer_violation"
        for row in result["row_statuses"]
        if row["key"][1] == "p2"
    )
    assert result["status"] == "failed"


def test_renamed_regional_derivative_does_not_cleanse_heldout_ancestry() -> None:
    from bijux_pollenomics.analysis.lra_validation.evaluation.api import ExternalInput

    scope = scope_fixture()
    external = ExternalInput(
        "renamed-regional-estimate", "training_derived_product", "e" * 64, None
    )
    scope = replace(
        scope,
        external_inputs=(external,),
        dependency_graph=(*scope.dependency_graph, (external.input_id, ("p2",))),
    )
    rows = tuple(
        bind_prediction(replace(row, fit_input_ids=(external.input_id,)))
        for row in rows_fixture(scope)
    )
    with pytest.raises(ValidationRefusal, match="Withheld record"):
        evaluate_final(policy_fixture(scope), scope=scope, rows=rows)


def test_duplicate_key_or_noncanonical_prediction_bytes_refuse() -> None:
    scope = scope_fixture()
    rows = rows_fixture(scope)
    assert rows[0].prediction_manifest_json is not None
    changed = replace(
        rows[0], prediction_manifest_json=rows[0].prediction_manifest_json + " "
    )
    with pytest.raises(ValidationRefusal, match="Frozen prediction bytes"):
        evaluate_final(policy_fixture(scope), scope=scope, rows=(changed, *rows[1:]))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("longitude", 40.0),
        ("latitude", 60.0),
        ("radius_m", 1000.0),
        ("coordinate_uncertainty_m", 100.0),
    ],
)
def test_shared_footprint_hash_cannot_override_contradictory_support(
    field: str, value: float
) -> None:
    scope = scope_fixture()
    rows = []
    for row in rows_fixture(scope):
        assert row.observation_support is not None
        rows.append(
            replace(
                row,
                observation_support=replace(
                    row.observation_support, **dict[str, Any]({field: value})
                ),
            )
        )
    result = json.loads(
        evaluate_final(
            policy_fixture(scope), scope=scope, rows=tuple(rows)
        ).canonical_result_json
    )
    assert result["status"] == "ineligible"
    assert all(
        row["status"] == "unsupported_observation_support"
        for row in result["row_statuses"]
    )


def test_evaluator_uses_shared_geographic_support_arithmetic() -> None:
    from bijux_pollenomics.analysis.lra_validation.evaluation.scoring import _distance
    from bijux_pollenomics.analysis.lra_validation.spatial.support import (
        support_separation,
    )

    scope = scope_fixture()
    target, training = scope.sites[2].support, scope.sites[0].support
    assert target is not None and training is not None
    target = replace(target, radius_m=37, coordinate_uncertainty_m=11)
    training = replace(training, radius_m=41, coordinate_uncertainty_m=13)
    assert (
        _distance(target, training)
        == support_separation(target, training).lower_bound_m
    )
