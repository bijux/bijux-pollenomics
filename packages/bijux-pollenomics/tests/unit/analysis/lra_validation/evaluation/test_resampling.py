"""Independent-unit bootstrap retains paired draws and refuses CV pseudo-replication."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    evaluate_final,
    resample_independent_units,
)

from .support import bind_prediction, policy_fixture, rows_fixture, scope_fixture


def test_fixed_external_cohort_keeps_shared_deterministic_draws() -> None:
    scope = scope_fixture()
    result = evaluate_final(
        policy_fixture(scope), scope=scope, rows=rows_fixture(scope)
    )
    first = resample_independent_units(
        result,
        scope=scope,
        cell_id="vegetation_cover",
        unit="site",
        resamples=100,
        seed=17,
        confidence_level=0.8,
    )
    assert first == resample_independent_units(
        result,
        scope=scope,
        cell_id="vegetation_cover",
        unit="site",
        resamples=100,
        seed=17,
        confidence_level=0.8,
    )
    assert first["independent_unit_count"] == 6
    assert first["predictive_interval"] is False
    assert first["population_coverage_verified"] is False
    assert isinstance(first["draws"], tuple)
    assert len(first["draws"]) == 100


def test_taxa_and_repeated_samples_do_not_inflate_units() -> None:
    scope = scope_fixture()
    result = evaluate_final(
        policy_fixture(scope), scope=scope, rows=rows_fixture(scope)
    )
    receipt = resample_independent_units(
        result,
        scope=scope,
        cell_id="vegetation_cover",
        unit="block",
        resamples=10,
        seed=3,
        confidence_level=0.8,
    )
    assert receipt["independent_unit_count"] == 6
    assert isinstance(receipt["unit_group_sums"], dict)
    assert set(receipt["unit_group_sums"]) == {f"b{i}" for i in range(2, 8)}


def test_noncommon_fitted_models_refuse_even_with_six_test_sites() -> None:
    scope = scope_fixture()
    rows = rows_fixture(scope)
    rows = (bind_prediction(replace(rows[0], fitted_model_sha256="c" * 64)), *rows[1:])
    result = evaluate_final(policy_fixture(scope), scope=scope, rows=rows)
    with pytest.raises(ValidationRefusal, match="same fixed"):
        resample_independent_units(
            result,
            scope=scope,
            cell_id="vegetation_cover",
            unit="site",
            resamples=10,
            seed=3,
            confidence_level=0.8,
        )


def test_unknown_or_ineligible_cell_and_bad_draw_declarations_refuse() -> None:
    scope = scope_fixture()
    result = evaluate_final(
        policy_fixture(scope), scope=scope, rows=rows_fixture(scope)
    )
    with pytest.raises(ValidationRefusal):
        resample_independent_units(
            result,
            scope=scope,
            cell_id="absent",
            unit="site",
            resamples=10,
            seed=3,
            confidence_level=0.8,
        )
    with pytest.raises(ValidationRefusal):
        resample_independent_units(
            result,
            scope=scope,
            cell_id="vegetation_cover",
            unit="site",
            resamples=True,
            seed=3,
            confidence_level=0.8,
        )


def test_bootstrap_cannot_accept_a_changed_scored_receipt() -> None:
    scope = scope_fixture()
    result = evaluate_final(
        policy_fixture(scope), scope=scope, rows=rows_fixture(scope)
    )
    payload = json.loads(result.canonical_result_json)
    payload["paired_evidence"][0]["model_mae_pp"] = 99
    changed = replace(result, canonical_result_json=json.dumps(payload))
    with pytest.raises(ValidationRefusal, match="identity"):
        resample_independent_units(
            changed,
            scope=scope,
            cell_id="vegetation_cover",
            unit="site",
            resamples=10,
            seed=3,
            confidence_level=0.8,
        )


def test_unequal_blocks_preserve_the_equal_site_group_estimand() -> None:
    scope = scope_fixture()
    scope = replace(
        scope,
        sites=tuple(
            replace(site, block_id="b2") if 2 <= i < 7 else site
            for i, site in enumerate(scope.sites)
        ),
    )
    rows = tuple(
        bind_prediction(replace(row, prediction=(("a", 0.7), ("b", 0.3))))
        if row.model_id == "model" and row.record_id != "p7"
        else row
        for row in rows_fixture(scope)
    )
    result = evaluate_final(policy_fixture(scope), scope=scope, rows=rows)
    receipt = resample_independent_units(
        result,
        scope=scope,
        cell_id="vegetation_cover",
        unit="block",
        resamples=100,
        seed=19,
        confidence_level=0.8,
    )
    draws = receipt["draws"]
    distribution = receipt["bootstrap_distribution"]
    assert isinstance(draws, tuple) and isinstance(distribution, dict)
    assert any(set(draw) == {"b2", "b7"} for draw in draws)
    for draw, estimate in zip(draws, distribution["model_mae_pp"], strict=True):
        expected = 50 / 6 if set(draw) == {"b2", "b7"} else 10 if draw[0] == "b2" else 0
        assert estimate == pytest.approx(expected)


def test_valid_overlapping_fold_scores_do_not_become_independent_bootstrap() -> None:
    from bijux_pollenomics.analysis.lra_validation.contracts import Fold

    scope = scope_fixture()
    second = Fold(
        "second",
        ("p2", "p3"),
        ("p0", "p1", "p4", "p5", "p6", "p7"),
        ("g2", "g3"),
        ("g0", "g1", "g4", "g5", "g6", "g7"),
    )
    scope = replace(scope, folds=(*scope.folds, second))
    rows = list(rows_fixture(scope))
    prototypes = rows[:4]
    sites = {x.record_id: x for x in scope.sites}
    for key in second.test_record_ids:
        for row in prototypes:
            rows.append(
                bind_prediction(
                    replace(
                        row,
                        fold_id="second",
                        record_id=key,
                        fit_input_ids=second.train_record_ids,
                        observation_support=sites[key].support,
                        fitted_model_sha256="d" * 64,
                    )
                )
            )
    result = evaluate_final(policy_fixture(scope), scope=scope, rows=tuple(rows))
    assert result.status == "passed"
    with pytest.raises(ValidationRefusal, match="Overlapping-fold"):
        resample_independent_units(
            result,
            scope=scope,
            cell_id="vegetation_cover",
            unit="site",
            resamples=10,
            seed=3,
            confidence_level=0.8,
        )


@pytest.mark.parametrize(
    "mutation",
    ["empty", "missing_key", "unknown_record", "wrong_type", "invalid_metric"],
)
def test_rehashed_malformed_retained_ledger_refuses(mutation: str) -> None:
    from bijux_pollenomics.analysis.lra_validation.contracts import (
        canonical_json,
        manifest_sha256,
    )

    scope = scope_fixture()
    result = evaluate_final(
        policy_fixture(scope), scope=scope, rows=rows_fixture(scope)
    )
    payload = json.loads(result.canonical_result_json)
    if mutation == "empty":
        payload["paired_evidence"] = []
    elif mutation == "missing_key":
        del payload["paired_evidence"][0]["model_mae_pp"]
    elif mutation == "unknown_record":
        payload["paired_evidence"][0]["record_id"] = "unknown"
    elif mutation == "wrong_type":
        payload["paired_evidence"][0]["model_fit_input_ids"] = "p0"
    else:
        payload["paired_evidence"][0]["model_mae_pp"] = -1
    altered = replace(
        result,
        canonical_result_json=canonical_json(payload),
        result_sha256=manifest_sha256(payload),
    )
    with pytest.raises(ValidationRefusal):
        resample_independent_units(
            altered,
            scope=scope,
            cell_id="vegetation_cover",
            unit="site",
            resamples=10,
            seed=3,
            confidence_level=0.8,
        )


def test_fixed_cohort_preserves_explicit_training_pollen_channel_admission() -> None:
    from bijux_pollenomics.analysis.lra_validation.channels import (
        ObservationChannels,
        PollenChannel,
    )

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
    rows = tuple(
        bind_prediction(replace(row, fit_input_ids=("pollen:0", "pollen:1")))
        for row in rows_fixture(scope)
    )
    result = evaluate_final(policy_fixture(scope), scope=scope, rows=rows)
    assert result.status == "passed"
    receipt = resample_independent_units(
        result,
        scope=scope,
        cell_id="vegetation_cover",
        unit="site",
        resamples=10,
        seed=3,
        confidence_level=0.8,
    )
    assert receipt["independent_unit_count"] == 6
