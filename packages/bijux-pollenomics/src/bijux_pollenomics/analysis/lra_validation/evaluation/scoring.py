"""Recompute separate-target criteria over complete frozen independent-site masks."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
import json
from statistics import mean
from typing import Any, cast

from ..channels import assert_channel_inputs
from ..contracts import (
    Fold,
    ValidationRefusal,
    canonical_json,
    finite_number,
    identity_values,
    manifest_sha256,
    required_identity,
)
from ..metrics import (
    CompositionScore,
    closed_composition,
    score_pollen,
    score_vegetation,
)
from ..spatial.support import support_distance_lower_bound_m
from ..splits import assert_allowed_inputs
from .contracts import (
    AcceptanceCell,
    EvaluationPolicy,
    EvaluationResult,
    EvaluationRow,
    EvaluationScope,
    EvaluationSite,
    PredictiveInterval,
    Support,
    digest,
    refuse,
    validate_frozen_prediction,
)
from .policy import validate_evaluation_policy


def _key(row: EvaluationRow) -> tuple[str, str, str, str, str]:
    return row.fold_id, row.record_id, row.experiment, row.target, row.model_id


def _source(row: EvaluationRow, kind: str) -> dict[str, str]:
    value = row.source_model
    if value is None or value.kind != kind:
        refuse("Paired evaluation source-model kind differs")
    return {"kind": value.kind, "sha256": value.sha256}


def _evidence_row(row: EvaluationRow, generic: bool) -> dict[str, Any]:
    value = asdict(row)
    if not generic:
        value.pop("source_model")
    value["prediction_frozen_at"] = (
        row.prediction_frozen_at.isoformat() if row.prediction_frozen_at else None
    )
    return value


def _composition(values: object) -> dict[str, Any]:
    if not isinstance(values, tuple) or not values:
        refuse("Compositions require explicit immutable named taxon entries")
    result: dict[str, Any] = {}
    for item in values:
        if not isinstance(item, tuple) or len(item) != 2:
            refuse("Malformed taxon entry")
        key = required_identity(item[0])
        if key in result:
            refuse("Duplicate taxon denominator")
        result[key] = item[1]
    return result


def _support_matches(target: Support | None, observed: Support | None) -> bool:
    # A shared footprint hash cannot override contradictory declared geometry,
    # uncertainty, coordinate/age type or temporal support metadata.
    return target is not None and observed is not None and target == observed


def _distance(target: Support, training: Support) -> float:
    return support_distance_lower_bound_m(target, training)


def _fit_closure(
    row: EvaluationRow, site: EvaluationSite, scope: EvaluationScope, fold: Fold
) -> tuple[str, ...]:
    observation_id = (
        site.vegetation_observation_id
        if row.target == "vegetation_cover"
        else site.pollen_observation_id
    )
    observed_ids = {
        key
        for item in scope.sites
        if item.record_id in fold.test_record_ids
        for key in (item.vegetation_observation_id, item.pollen_observation_id)
    }
    local_experiment = row.experiment == "local_pollen_available"
    local_model = local_experiment and (
        row.source_model is None or row.source_model.kind == "local_pollen_assimilation"
    )
    if local_model:
        if row.target != "vegetation_cover" or row.observed_pollen is None:
            refuse(
                "Local pollen mode requires explicit observed pollen and independent vegetation"
            )
        if (
            row.observed_pollen.record_id != site.record_id
            or row.observed_pollen.group_id != site.group_id
        ):
            refuse("Observed pollen admission differs from scored target ownership")
    elif row.observed_pollen is not None:
        refuse("Only a local-pollen assimilation may admit target pollen")
    if local_experiment or scope.observation_channels:
        channels = {item.record_id: item for item in scope.observation_channels}
        sites = {item.record_id: item for item in scope.sites}
        if set(channels) != set(sites) or any(
            item.group_id != sites[key].group_id
            or sites[key].vegetation_observation_id not in item.vegetation_input_ids
            or sites[key].pollen_observation_id
            not in {c.input_id for c in item.pollen_channels}
            for key, item in channels.items()
        ):
            refuse(
                "Scope observation ownership differs from explicit channel catalogue"
            )
        return assert_channel_inputs(
            fold,
            row.fit_input_ids,
            dict(scope.dependency_graph),
            channels=scope.observation_channels,
            observed_pollen=row.observed_pollen,
            admitted_external_ids=tuple(
                item.input_id for item in scope.external_inputs
            ),
        )
    closure = assert_allowed_inputs(
        fold,
        row.fit_input_ids,
        dict(scope.dependency_graph),
        admitted_external_ids=tuple(item.input_id for item in scope.external_inputs),
    )
    if set(closure) & observed_ids or observation_id in closure:
        refuse("A withheld observation occurs in fitted source ancestry")
    return closure


def _interval(
    row: EvaluationRow, observation: dict[str, Any], cell: AcceptanceCell
) -> tuple[float, float] | None:
    interval = row.interval
    if interval is None:
        return None
    if (
        not isinstance(interval, PredictiveInterval)
        or interval.profile_id != cell.interval_profile_id
    ):
        refuse("Predictive interval profile differs from frozen acceptance policy")
    if (
        interval.uncertainty_kind != "predictive_observation"
        or "observation_process" not in identity_values(interval.propagated_sources)
    ):
        refuse(
            "Predictive coverage requires declared observation-process uncertainty, not latent/parameter intervals"
        )
    nominal = finite_number(interval.nominal_coverage)
    if nominal != cell.nominal_predictive_coverage or not identity_values(
        interval.propagated_sources
    ):
        refuse(
            "Predictive interval level or propagated-source declaration is missing/wrong"
        )
    if not isinstance(interval.limits, tuple):
        refuse("Predictive limits require explicit immutable taxon entries")
    limits: dict[str, tuple[float, float]] = {}
    for taxon, lower, upper in interval.limits:
        taxon = required_identity(taxon)
        lo, hi = finite_number(lower), finite_number(upper)
        if taxon in limits or not 0 <= lo <= hi <= 1:
            refuse("Invalid or duplicate predictive interval limits")
        limits[taxon] = (lo, hi)
    if set(limits) != set(observation):
        refuse("Predictive interval and observation taxon denominators differ")
    values = observation
    if row.target == "pollen_composition":
        total = sum(values.values())
        values = {key: value / total for key, value in values.items()}
    return mean(
        float(limits[key][0] <= value <= limits[key][1])
        for key, value in values.items()
    ), mean(hi - lo for lo, hi in limits.values())


def _score_row(
    row: EvaluationRow,
    site: EvaluationSite,
    scope: EvaluationScope,
    fold: Fold,
    policy: EvaluationPolicy,
) -> tuple[CompositionScore | None, str]:
    if row.status not in {"predicted", "prediction_failed", "excluded"}:
        refuse("Unknown prediction status")
    if row.status != "predicted":
        if (
            not isinstance(row.reason, str)
            or not row.reason.strip()
            or row.prediction is not None
        ):
            refuse(
                "Failed/excluded predictions need a reason and no invented composition"
            )
        return None, row.status
    if row.prediction is None or row.prediction_sha256 is None:
        refuse("Predictions require values and an immutable prediction identity")
    digest(row.prediction_sha256)
    if row.source_model is None:
        if row.fitted_model_sha256 is None:
            refuse("Historical predictions require an immutable fitted identity")
        digest(row.fitted_model_sha256)
    else:
        digest(row.source_model.sha256)
    if (
        not isinstance(row.prediction_frozen_at, datetime)
        or row.prediction_frozen_at.utcoffset() is None
        or row.prediction_frozen_at >= policy.first_test_access_at
    ):
        refuse("Prediction freeze must precede first test access")
    if row.interval is not None and not isinstance(row.interval, PredictiveInterval):
        refuse("Predictive intervals must be typed")
    version = validate_frozen_prediction(row)
    if (
        row.source_model is not None
        and version != "pollenomics-evaluation-prediction.v2"
    ):
        refuse("Typed source-model scoring requires a v2 prediction envelope")
    closure = _fit_closure(row, site, scope, fold)
    if row.observation is None:
        return None, "missing_observation"
    if not _support_matches(site.support, row.observation_support):
        return None, "unsupported_observation_support"
    assert site.support is not None
    supports = {x.record_id: x.support for x in scope.sites}
    supports.update(
        {
            x.input_id: x.support
            for x in scope.external_inputs
            if x.role == "observed_source"
        }
    )
    observed_training = set(fold.train_record_ids) | {
        x.input_id
        for x in scope.external_inputs
        if x.role == "observed_source" and x.input_id in closure
    }
    for key in observed_training:
        support = supports[key]
        if support is None:
            return None, "missing_training_support"
        if (
            support.younger_bp != site.support.younger_bp
            or support.older_bp != site.support.older_bp
        ):
            return None, "incompatible_training_time_support"
        if _distance(site.support, support) < policy.minimum_buffer_m:
            return None, "spatial_buffer_violation"
    if (
        row.target == "vegetation_cover"
        and row.observation_reference_id
        not in policy.independent_vegetation_reference_ids
    ):
        refuse(
            "Vegetation observation has no policy-admitted independent measured reference"
        )
    expected_kind = (
        "independent_measured_vegetation"
        if row.target == "vegetation_cover"
        else "heldout_pollen_counts"
    )
    if row.observation_kind != expected_kind:
        refuse(
            "Modeled or published reconstruction comparisons are not independent observed targets"
        )
    predicted, observed = _composition(row.prediction), _composition(row.observation)
    if set(predicted) != set(scope.taxa):
        return None, "prediction_failed_taxon_denominator"
    try:
        closed_composition(predicted)
    except ValidationRefusal:
        return None, "prediction_failed_invalid_output"
    if set(observed) != set(scope.taxa):
        return None, "refused_observation_taxon_denominator"
    try:
        score = (
            score_vegetation(predicted, observed)
            if row.target == "vegetation_cover"
            else score_pollen(predicted, observed)
        )
    except ValidationRefusal:
        return None, "refused_observation_or_prediction"
    return score, score.status


def evaluate_final(
    policy: EvaluationPolicy, *, scope: EvaluationScope, rows: tuple[EvaluationRow, ...]
) -> EvaluationResult:
    """Evaluate supplied held-out evidence; no engineering receipt authenticates review."""
    # Public dataclasses can be manually instantiated: revalidate their declaration.
    checked = validate_evaluation_policy(
        json.loads(policy.canonical_policy_json),
        scope=scope,
        first_test_access_at=policy.first_test_access_at,
    )
    if checked != policy:
        refuse("Policy object differs from its canonical immutable declaration")
    if not isinstance(rows, tuple) or any(
        not isinstance(row, EvaluationRow) for row in rows
    ):
        refuse("Evaluation requires a complete typed immutable row ledger")
    sites = {site.record_id: site for site in scope.sites}
    folds = {fold.fold_id: fold for fold in scope.folds}
    expected: set[tuple[str, str, str, str, str]] = set()
    memberships: dict[str, tuple[tuple[str, str], ...]] = {}
    for cell in policy.cells:
        members = tuple(
            (fold.fold_id, key)
            for fold in scope.folds
            for key in fold.test_record_ids
            if cell.subgroup == "all" or cell.subgroup in sites[key].strata
        )
        memberships[cell.cell_id] = members
        expected.update(
            (fold, key, cell.experiment, cell.target, model)
            for fold, key in members
            for model in (cell.model_id, cell.baseline_id)
        )
    ledger = {_key(row): row for row in rows}
    if len(ledger) != len(rows) or set(ledger) != expected:
        refuse("Requested evidence universe has omitted, duplicate or unexpected rows")
    predicted = [row for row in rows if row.status == "predicted"]
    typed = [row.source_model is not None for row in predicted]
    generic = bool(typed) and all(typed)
    if any(typed) and not generic:
        refuse("A result cannot mix legacy and typed source-model predictions")
    scored = {
        key: _score_row(row, sites[row.record_id], scope, folds[row.fold_id], policy)
        for key, row in ledger.items()
    }
    cells: list[dict[str, Any]] = []
    paired_evidence: list[dict[str, Any]] = []
    for cell in policy.cells:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        failure_groups: set[str] = set()
        exclusion_groups: set[str] = set()
        requested_groups = {sites[key].group_id for _, key in memberships[cell.cell_id]}
        interval_missing = False
        for fold_id, record_id in memberships[cell.cell_id]:
            key = (fold_id, record_id, cell.experiment, cell.target)
            model, baseline = (
                ledger[(*key, cell.model_id)],
                ledger[(*key, cell.baseline_id)],
            )
            if (
                model.observation,
                model.observation_reference_id,
                model.observation_kind,
                model.observation_support,
            ) != (
                baseline.observation,
                baseline.observation_reference_id,
                baseline.observation_kind,
                baseline.observation_support,
            ):
                refuse(
                    "Paired baseline and model must use identical observation values/support"
                )
            score, status = scored[(*key, cell.model_id)]
            base_score, base_status = scored[(*key, cell.baseline_id)]
            site = sites[record_id]
            if any(
                value.startswith("prediction_failed") for value in (status, base_status)
            ):
                failure_groups.add(site.group_id)
            if (
                score is None
                or base_score is None
                or status != "scored"
                or base_status != "scored"
            ):
                exclusion_groups.add(site.group_id)
                continue
            assert (
                score.mae_fraction is not None and base_score.mae_fraction is not None
            )
            interval = _interval(model, _composition(model.observation), cell)
            interval_missing |= interval is None
            item = {
                "cell_id": cell.cell_id,
                "record_id": record_id,
                "fold_id": fold_id,
                "group_id": site.group_id,
                "block_id": site.block_id,
                "model_mae_pp": score.mae_fraction * 100,
                "baseline_mae_pp": base_score.mae_fraction * 100,
                "improvement_pp": (base_score.mae_fraction - score.mae_fraction) * 100,
                "coverage": interval[0] if interval else None,
                "width_fraction": interval[1] if interval else None,
            }
            if generic:
                item.update(
                    model_source=_source(
                        model,
                        "local_pollen_assimilation"
                        if cell.experiment == "local_pollen_available"
                        else "fitted_spatial",
                    ),
                    baseline_source=_source(
                        baseline, "admitted_reconstruction_training_mean"
                    ),
                    model_input_ids=model.fit_input_ids,
                    baseline_input_ids=baseline.fit_input_ids,
                )
            else:
                item.update(
                    model_fit_sha256=model.fitted_model_sha256,
                    baseline_fit_sha256=baseline.fitted_model_sha256,
                    model_fit_input_ids=model.fit_input_ids,
                    baseline_fit_input_ids=baseline.fit_input_ids,
                )
            groups[site.group_id].append(item)
            paired_evidence.append(item)
        count = len(requested_groups)
        block_ids = {x["block_id"] for values in groups.values() for x in values}
        aggregate = {
            key: mean(mean(item[key] for item in values) for values in groups.values())
            if groups
            else None
            for key in ("model_mae_pp", "baseline_mae_pp", "improvement_pp")
        }
        coverage = (
            mean(
                mean(item["coverage"] for item in values) for values in groups.values()
            )
            if groups and not interval_missing
            else None
        )
        width = (
            mean(
                mean(item["width_fraction"] for item in values)
                for values in groups.values()
            )
            if groups and not interval_missing
            else None
        )
        enough = (
            len(groups) >= cell.minimum_sites and len(block_ids) >= cell.minimum_blocks
        )
        criteria = {
            "minimum_independent_units": enough,
            "maximum_mae": aggregate["model_mae_pp"] is not None
            and aggregate["model_mae_pp"] <= cell.maximum_mae_pp,
            "minimum_baseline_improvement": aggregate["improvement_pp"] is not None
            and aggregate["improvement_pp"] >= cell.minimum_baseline_improvement_pp,
            "maximum_prediction_failure_fraction": count > 0
            and len(failure_groups) / count <= cell.maximum_prediction_failure_fraction,
            "maximum_exclusion_fraction": count > 0
            and len(exclusion_groups) / count <= cell.maximum_exclusion_fraction,
            "predictive_coverage": coverage is not None
            and abs(coverage - cell.nominal_predictive_coverage)
            <= cell.coverage_tolerance,
        }
        status = (
            "ineligible"
            if not enough or coverage is None
            else "passed"
            if all(criteria.values())
            else "failed"
        )
        cells.append(
            {
                "cell_id": cell.cell_id,
                "target": cell.target,
                "experiment": cell.experiment,
                "status": status,
                "requested_records": len(memberships[cell.cell_id]),
                "requested_independent_groups": count,
                "paired_scored_groups": len(groups),
                "paired_scored_blocks": len(block_ids),
                "failed_prediction_groups": len(failure_groups),
                "excluded_or_unpaired_groups": len(exclusion_groups),
                "aggregation_profile": "equal-independent-group-mean-v1",
                "criteria": criteria,
                "scores": aggregate,
                "predictive_coverage": coverage,
                "predictive_mean_width_fraction": width,
            }
        )
    status = (
        "ineligible"
        if any(x["status"] == "ineligible" for x in cells)
        else "failed"
        if any(x["status"] == "failed" for x in cells)
        else "passed"
    )
    result = {
        "schema_version": (
            "pollenomics-final-evaluation-result.v3"
            if generic
            else "pollenomics-final-evaluation-result.v2"
        ),
        "status": status,
        "policy_sha256": policy.policy_sha256,
        "first_test_access_at": policy.first_test_access_at.isoformat(),
        "scope_sha256": scope.scope_sha256,
        "split_sha256": scope.split_sha256,
        "evidence_sha256": manifest_sha256(
            [_evidence_row(row, generic) for row in rows]
        ),
        "cells": cells,
        "paired_evidence": paired_evidence,
        "row_statuses": [
            {"key": list(key), "status": value[1]}
            for key, value in sorted(scored.items())
        ],
        "review_authenticity_verified": False,
        "scientific_approval_granted": False,
        "aggregate_intervals_are_predictive_intervals": False,
    }
    return EvaluationResult(
        canonical_json(result), manifest_sha256(result), cast(Any, status)
    )
