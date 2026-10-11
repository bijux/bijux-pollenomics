"""Conditional paired bootstrap summaries for a fixed model and external cohort."""

from __future__ import annotations

import json
from random import Random
from statistics import mean
from typing import Any, Literal

from ..channels import assert_channel_inputs
from ..contracts import canonical_json, finite_number, identity_values, manifest_sha256
from ..splits import assert_allowed_inputs
from .contracts import EvaluationResult, EvaluationScope, digest, refuse


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    left = int(position)
    right = min(left + 1, len(ordered) - 1)
    return ordered[left] + (ordered[right] - ordered[left]) * (position - left)


def _scored_payload(result: EvaluationResult, scope: EvaluationScope) -> dict[str, Any]:
    """Validate retained ledger shape without claiming to authenticate outcomes."""
    try:
        payload = json.loads(result.canonical_result_json)
    except (ValueError, TypeError):
        refuse("Malformed retained scored evidence")
    if not isinstance(payload, dict):
        refuse("Scored evidence must be an object")
    version = payload.get("schema_version")
    if version not in {
        "pollenomics-final-evaluation-result.v2",
        "pollenomics-final-evaluation-result.v3",
    }:
        refuse("Unsupported retained final-evaluation result version")
    generic = version == "pollenomics-final-evaluation-result.v3"
    cells = payload.get("cells")
    records = payload.get("paired_evidence")
    if (
        not isinstance(cells, list)
        or not cells
        or not isinstance(records, list)
        or not records
        or any(not isinstance(x, dict) for x in (*cells, *records))
    ):
        refuse("Retained scored cells and paired ledger must be nonempty object lists")
    cell_ids = []
    for cell in cells:
        key = cell.get("cell_id")
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(cell.get("status"), str)
            or cell.get("status") not in {"passed", "failed", "ineligible"}
        ):
            refuse("Malformed scored cell identity or status")
        requested = cell.get("requested_records")
        if type(requested) is not int or requested < 0:
            refuse("Malformed requested-record denominator")
        cell_ids.append(key)
    if len(cell_ids) != len(set(cell_ids)):
        refuse("Duplicate scored cell identity")
    sites = {site.record_id: site for site in scope.sites}
    experiments = {cell["cell_id"]: cell.get("experiment") for cell in payload["cells"]}
    for row in records:
        required = {
            "cell_id",
            "record_id",
            "fold_id",
            "group_id",
            "block_id",
            "model_mae_pp",
            "baseline_mae_pp",
            "improvement_pp",
            "coverage",
            "width_fraction",
        }
        required.update(
            {
                "model_source",
                "baseline_source",
                "model_input_ids",
                "baseline_input_ids",
            }
            if generic
            else {
                "model_fit_sha256",
                "baseline_fit_sha256",
                "model_fit_input_ids",
                "baseline_fit_input_ids",
            }
        )
        if set(row) != required:
            refuse("Paired scored record fields differ from the exact schema")
        if any(
            not isinstance(row[key], str)
            for key in ("cell_id", "record_id", "group_id", "block_id")
        ):
            refuse("Malformed paired scored identity")
        if row["cell_id"] not in cell_ids or row["record_id"] not in sites:
            refuse("Paired score names an unknown cell or record")
        if generic:
            if {
                "model_fit_sha256",
                "baseline_fit_sha256",
                "model_fit_input_ids",
                "baseline_fit_input_ids",
            } & set(row):
                refuse("Generic scored evidence cannot expose fitted-only aliases")
            model_kind = (
                "local_pollen_assimilation"
                if experiments.get(row["cell_id"]) == "local_pollen_available"
                else "fitted_spatial"
            )
            for key, kind in (
                ("model_source", model_kind),
                ("baseline_source", "admitted_reconstruction_training_mean"),
            ):
                source = row[key]
                if (
                    not isinstance(source, dict)
                    or set(source) != {"kind", "sha256"}
                    or source.get("kind") != kind
                ):
                    refuse("Malformed generic source-model identity")
                source_sha256 = source.get("sha256")
                if not isinstance(source_sha256, str):
                    refuse("Malformed generic source-model identity")
                digest(source_sha256)
            input_fields = ("model_input_ids", "baseline_input_ids")
        else:
            if {
                "model_source",
                "baseline_source",
                "model_input_ids",
                "baseline_input_ids",
            } & set(row):
                refuse("Historical v2 evidence cannot contain v3 source fields")
            for key in ("model_fit_sha256", "baseline_fit_sha256"):
                digest(row[key])
            input_fields = ("model_fit_input_ids", "baseline_fit_input_ids")
        for key in input_fields:
            values = identity_values(row[key])
            if not values or (generic and len(values) != len(set(values))):
                refuse("Paired scored training identities cannot be empty or duplicate")
        if (
            not 0 <= finite_number(row["model_mae_pp"]) <= 100
            or not -100 <= finite_number(row["improvement_pp"]) <= 100
        ):
            refuse("Paired scored percentage-point metric is outside its domain")
    return payload


def resample_independent_units(
    result: EvaluationResult,
    *,
    scope: EvaluationScope,
    cell_id: str,
    unit: Literal["site", "block"],
    resamples: int,
    seed: int,
    confidence_level: float,
) -> dict[str, object]:
    """Persist shared unit draws for conditional error/improvement summaries.

    A single external holdout fold, complete scored cohort, and common fitted
    model/inputs are required. Overlapping cross-validation fits are refused.
    The percentile summary does not propagate fitting/PPE/chronology uncertainty
    or establish coverage for a population; these are not predictive intervals.
    """
    if not isinstance(result, EvaluationResult) or not isinstance(
        scope, EvaluationScope
    ):
        refuse("Resampling requires typed scored evidence and scope")
    payload = _scored_payload(result, scope)
    if (
        result.canonical_result_json != canonical_json(payload)
        or payload.get("schema_version")
        not in {
            "pollenomics-final-evaluation-result.v2",
            "pollenomics-final-evaluation-result.v3",
        }
        or payload.get("status") != result.status
        or manifest_sha256(payload) != result.result_sha256
        or payload.get("scope_sha256") != scope.scope_sha256
        or payload.get("split_sha256") != scope.split_sha256
    ):
        refuse("Resampling evidence identity or scope differs")
    if len(scope.folds) != 1:
        refuse("Overlapping-fold cross-validation is not a fixed-model external cohort")
    if (
        unit not in {"site", "block"}
        or type(resamples) is not int
        or not 2 <= resamples <= 100_000
        or type(seed) is not int
        or seed < 0
    ):
        refuse("Resampling needs an explicit unit, bounded integer draw count and seed")
    level = finite_number(confidence_level)
    if not 0 < level < 1:
        refuse("Confidence level must lie strictly between zero and one")
    cells = [x for x in payload["cells"] if x["cell_id"] == cell_id]
    if len(cells) != 1 or cells[0]["status"] == "ineligible":
        refuse("A unique eligible cell is required for conditional resampling")
    records = [x for x in payload["paired_evidence"] if x["cell_id"] == cell_id]
    if (
        len(records) != len({x["record_id"] for x in records})
        or len(records) != cells[0]["requested_records"]
    ):
        refuse("Conditional resampling requires the complete unique scored cohort")
    generic = payload["schema_version"] == "pollenomics-final-evaluation-result.v3"
    if generic and any(
        row["model_source"].get("kind") == "local_pollen_assimilation"
        for row in records
    ):
        refuse("Record-specific local-pollen assimilation is not a fixed-model cohort")
    source_fields = (
        ("model_source", "baseline_source")
        if generic
        else ("model_fit_sha256", "baseline_fit_sha256")
    )
    input_fields = (
        ("model_input_ids", "baseline_input_ids")
        if generic
        else ("model_fit_input_ids", "baseline_fit_input_ids")
    )
    for field in source_fields:
        if len({canonical_json(x[field]) for x in records}) != 1:
            refuse("All cohort predictions must use the same fixed source model")
    for field in input_fields:
        if len({tuple(x[field]) for x in records}) != 1:
            refuse("All cohort predictions must use the same frozen training inputs")
    fold = scope.folds[0]
    observed_ids = {
        key
        for site in scope.sites
        if site.record_id in fold.test_record_ids
        for key in (site.vegetation_observation_id, site.pollen_observation_id)
    }
    for field in input_fields:
        if scope.observation_channels:
            closure = assert_channel_inputs(
                fold,
                records[0][field],
                dict(scope.dependency_graph),
                channels=scope.observation_channels,
                admitted_external_ids=tuple(x.input_id for x in scope.external_inputs),
            )
        else:
            closure = assert_allowed_inputs(
                fold,
                records[0][field],
                dict(scope.dependency_graph),
                admitted_external_ids=tuple(x.input_id for x in scope.external_inputs),
            )
        if set(closure) & observed_ids:
            refuse("Evaluation observations occur in fixed-model training ancestry")
    sites = {x.record_id: x for x in scope.sites}
    independent: dict[str, dict[str, list[dict[str, float]]]] = {}
    for row in records:
        site = sites[row["record_id"]]
        if row["group_id"] != site.group_id or row["block_id"] != site.block_id:
            refuse("Scored unit membership differs from frozen scope")
        key = site.group_id if unit == "site" else site.block_id
        independent.setdefault(key, {}).setdefault(site.group_id, []).append(
            {
                metric: finite_number(row[metric])
                for metric in ("model_mae_pp", "improvement_pp")
            }
        )
    if len(independent) < 2 or resamples * len(independent) > 5_000_000:
        refuse("Insufficient independent units or excessive draw storage requested")
    # Equal records inside groups; resample entire blocks without changing the
    # original equal-group estimand when block sizes differ.
    units = {
        key: {
            "group_count": len(groups),
            **{
                metric: sum(
                    mean(x[metric] for x in values) for values in groups.values()
                )
                for metric in ("model_mae_pp", "improvement_pp")
            },
        }
        for key, groups in sorted(independent.items())
    }
    ids = tuple(units)
    rng = Random(seed)
    draws = tuple(
        tuple(ids[rng.randrange(len(ids))] for _ in ids) for _ in range(resamples)
    )
    distribution = {
        metric: [
            sum(units[key][metric] for key in draw)
            / sum(units[key]["group_count"] for key in draw)
            for draw in draws
        ]
        for metric in ("model_mae_pp", "improvement_pp")
    }
    alpha = (1 - level) / 2
    receipt: dict[str, object] = {
        "schema_version": "pollenomics-conditional-unit-bootstrap.v1",
        "profile": "fixed-model-external-cohort-paired-percentile-v1",
        "result_sha256": result.result_sha256,
        "cell_id": cell_id,
        "unit": unit,
        "independent_unit_count": len(units),
        "resamples": resamples,
        "seed": seed,
        "confidence_level": level,
        "unit_group_sums": units,
        "aggregation_profile": "equal-independent-group-mean-v1",
        "draws": draws,
        "draws_sha256": manifest_sha256(draws),
        "bootstrap_distribution": distribution,
        "intervals": {
            key: {
                "lower": _quantile(values, alpha),
                "upper": _quantile(values, 1 - alpha),
                "units": "percentage_points",
            }
            for key, values in distribution.items()
        },
        "propagated_uncertainty": ["resampling_declared_evaluation_units_only"],
        "not_propagated": [
            "model_fitting",
            "PPE",
            "chronology",
            "reconstruction",
            "prediction_observation_process",
        ],
        "population_coverage_verified": False,
        "predictive_interval": False,
    }
    canonical_json(receipt)
    return receipt
