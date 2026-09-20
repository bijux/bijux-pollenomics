"""Synthetic thresholds demonstrate code behavior, not an approved benchmark."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime
from typing import Any, Literal

from bijux_pollenomics.analysis.lra_validation.contracts import (
    Fold,
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    EvaluationPolicy,
    EvaluationRow,
    EvaluationScope,
    EvaluationSite,
    PredictiveInterval,
    Support,
    validate_evaluation_policy,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.contracts import (
    _authenticated_source_model,
    prediction_payload,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FITTED_METHOD,
)

ACCESS = datetime(2020, 2, 1, tzinfo=UTC)
FROZEN = datetime(2020, 1, 15, tzinfo=UTC)


def scope_fixture() -> EvaluationScope:
    sites = tuple(
        EvaluationSite(
            record_id=f"p{i}",
            site_id=f"site{i}",
            group_id=f"g{i}",
            block_id=f"b{i}",
            bin_id="typed-bin",
            strata=("synthetic-country",),
            vegetation_observation_id=f"vegetation:{i}",
            pollen_observation_id=f"pollen:{i}",
            support=Support(
                50.0,
                i * 0.1 if i < 2 else 10 + i * 0.1,
                10,
                1,
                0,
                100,
                str(i) * 64,
                "EPSG:4326",
                "BP",
                "bounded-footprint-radius-v1",
                "typed-bp-interval-v1",
            ),
        )
        for i in range(8)
    )
    fold = Fold(
        "external",
        ("p0", "p1"),
        tuple(f"p{i}" for i in range(2, 8)),
        ("g0", "g1"),
        tuple(f"g{i}" for i in range(2, 8)),
    )
    return EvaluationScope(
        "synthetic-unreviewed",
        sites,
        (fold,),
        tuple((f"p{i}", ()) for i in range(8)),
        ("a", "b"),
    )


def policy_payload(scope: EvaluationScope) -> dict[str, Any]:
    cell = {
        "experiment": "all_target_pollen_withheld",
        "model_id": "model",
        "baseline_id": "mean",
        "subgroup": "all",
        "maximum_mae_pp": 1.0,
        "minimum_baseline_improvement_pp": 1.0,
        "minimum_sites": 2,
        "minimum_blocks": 2,
        "maximum_prediction_failure_fraction": 0.0,
        "maximum_exclusion_fraction": 0.0,
        "nominal_predictive_coverage": 0.8,
        "coverage_tolerance": 0.21,
        "interval_profile_id": "synthetic-only-interval",
    }
    return {
        "schema_version": "pollenomics-final-evaluation.v2",
        "status": "frozen",
        "scope_manifest_sha256": scope.scope_sha256,
        "split_manifest_sha256": scope.split_sha256,
        "locked_at": "2020-01-01T00:00:00Z",
        "review_reference": "synthetic-test-declaration-no-scientific-review",
        "cells": [
            dict(cell, cell_id=target, target=target)
            for target in ("vegetation_cover", "pollen_composition")
        ],
        "minimum_buffer_m": 1000.0,
        "spatial_support_policy": "same-footprint-wgs84-buffer-lower-bound-v1",
        "temporal_support_policy": "exact-typed-bp-interval-v1",
        "zero_missing_policy": "closed-fractions-missing-unscored-no-pseudocount-v1",
        "multiplicity_policy": "all-predeclared-cells-no-p-values-v1",
        "independent_vegetation_reference_ids": ["synthetic-measured-reference"],
    }


def policy_fixture(scope: EvaluationScope) -> EvaluationPolicy:
    return validate_evaluation_policy(
        policy_payload(scope), scope=scope, first_test_access_at=ACCESS
    )


def bind_prediction(row: EvaluationRow) -> EvaluationRow:
    envelope = {
        "schema_version": "pollenomics-evaluation-prediction.v1",
        "fold_id": row.fold_id,
        "record_id": row.record_id,
        "model_id": row.model_id,
        "target": row.target,
        "experiment": row.experiment,
        "prediction": row.prediction,
        "fitted_model_sha256": row.fitted_model_sha256,
        "fit_input_ids": row.fit_input_ids,
        "frozen_at": row.prediction_frozen_at.isoformat()
        if row.prediction_frozen_at
        else None,
        "interval": asdict(row.interval) if row.interval else None,
        "observed_pollen": asdict(row.observed_pollen) if row.observed_pollen else None,
    }
    return replace(
        row,
        prediction_manifest_json=canonical_json(envelope),
        prediction_sha256=manifest_sha256(envelope),
    )


def rows_fixture(scope: EvaluationScope) -> tuple[EvaluationRow, ...]:
    result = []
    for site in scope.sites[2:]:
        targets: tuple[Literal["vegetation_cover", "pollen_composition"], ...] = (
            "vegetation_cover",
            "pollen_composition",
        )
        for target in targets:
            for model in ("model", "mean"):
                point = 0.6 if model == "model" else 0.5
                interval = (
                    PredictiveInterval(
                        "synthetic-only-interval",
                        0.8,
                        (
                            "observation_process",
                            "synthetic-placeholder-no-real-coverage-claim",
                        ),
                        "predictive_observation",
                        (("a", 0.4, 0.8), ("b", 0.2, 0.6)),
                    )
                    if model == "model"
                    else None
                )
                row = EvaluationRow(
                    fold_id="external",
                    record_id=site.record_id,
                    model_id=model,
                    target=target,
                    experiment="all_target_pollen_withheld",
                    status="predicted",
                    prediction=(("a", point), ("b", 1 - point)),
                    observation=(("a", 0.6), ("b", 0.4))
                    if target == "vegetation_cover"
                    else (("a", 6), ("b", 4)),
                    observation_reference_id="synthetic-measured-reference",
                    observation_kind="independent_measured_vegetation"
                    if target == "vegetation_cover"
                    else "heldout_pollen_counts",
                    observation_support=site.support,
                    prediction_sha256=None,
                    prediction_manifest_json=None,
                    fitted_model_sha256=("a" if model == "model" else "b") * 64,
                    prediction_frozen_at=FROZEN,
                    fit_input_ids=("p0", "p1"),
                    interval=interval,
                )
                result.append(bind_prediction(row))
    return tuple(result)


def typed_policy_fixture(scope: EvaluationScope) -> EvaluationPolicy:
    declaration = policy_payload(scope)
    for cell in declaration["cells"]:
        cell["model_id"] = FITTED_METHOD
        cell["baseline_id"] = "training_mean"
    return validate_evaluation_policy(
        declaration, scope=scope, first_test_access_at=ACCESS
    )


def typed_rows_fixture(scope: EvaluationScope) -> tuple[EvaluationRow, ...]:
    result = []
    for original in rows_fixture(scope):
        fitted = original.model_id == "model"
        assert original.fitted_model_sha256 is not None
        row = replace(
            original,
            model_id=FITTED_METHOD if fitted else "training_mean",
            prediction_sha256=None,
            prediction_manifest_json=None,
            fitted_model_sha256=original.fitted_model_sha256 if fitted else None,
            source_model=_authenticated_source_model(
                "fitted_spatial" if fitted else "admitted_reconstruction_training_mean",
                original.fitted_model_sha256,
            ),
        )
        envelope = prediction_payload(row)
        result.append(
            replace(
                row,
                prediction_manifest_json=canonical_json(envelope),
                prediction_sha256=manifest_sha256(envelope),
            )
        )
    return tuple(result)
