"""Generate artificial cohort evidence without reading real counts or fitting models."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.optimizer_inputs import (
    cohort_outputs as subject,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.optimizer_inputs import (
    withheld_fold as helpers,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.optimizer_inputs.fixed_starts import (
    STARTS,
)


def raw(value: Any) -> bytes:
    """Encode deterministic synthetic evidence bytes without nonfinite values."""
    return (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()


def pin(value: bytes) -> dict[str, Any]:
    """Return the exact digest and byte length of synthetic evidence bytes."""
    return {
        "path": "artificial",
        "sha256": hashlib.sha256(value).hexdigest(),
        "bytes": len(value),
    }


def _constructed_experiment() -> dict[str, Any]:
    records = [
        "author:BECKHAM",
        "author:BROADOWN",
        "author:CUTHILL2",
        "author:LONGBREACH",
        *[f"author:constructed-site-{index:02d}" for index in range(11)],
    ]
    return {
        "sites": [
            {
                "record_id": record,
                "site_id": record.removeprefix("author:"),
                "identity_keys": [],
                "raw": {"path": record.removeprefix("author:") + "-raw.json"},
                "geometry": {"path": record.removeprefix("author:") + "-geometry.json"},
            }
            for record in records
        ],
        "regional_priority": ["author:BECKHAM", "author:BROADOWN"],
        "support_profile": "constructed-static-support",
        "local_support_radius_m": 1000,
        "request_template": {"taxa": []},
    }


def _constructed_protocol() -> dict[str, Any]:
    experiment = _constructed_experiment()
    records = sorted(site["record_id"] for site in experiment["sites"])
    logical = []
    for target in records:
        train = set(records) - {target}
        anchor = next(
            record for record in experiment["regional_priority"] if record in train
        )
        for local in sorted(train - {anchor}):
            logical.append(
                {
                    "fold_id": "site-group:" + helpers._canonical_sha([target]),
                    "target_record_id": target,
                    "local_record_id": local,
                    "regional_anchor_record_id": anchor,
                    "request_sha256": helpers._canonical_sha([local, anchor]),
                }
            )
    names = [
        role["path"]
        for site in experiment["sites"]
        for role in (site["raw"], site["geometry"])
    ]
    names += [
        "experiment.json",
        "parameters.json",
        "dependency-lock.json",
        "decision.json",
        "source-report.json",
        "chronology.json",
        "taxa.json",
    ]
    return {
        "schema_version": "author-love-cohort-development-protocol.v1",
        "profile": "constructed-fixed-start-cohort",
        "counts": dict(subject.COUNTS),
        "logical_requests": sorted(
            logical, key=lambda row: (row["fold_id"], row["local_record_id"])
        ),
        "inputs": [{"path": name} for name in names],
    }


def bundle() -> tuple[
    dict[str, bytes], dict[str, dict[str, Any]], dict[str, Any], dict[str, bytes]
]:
    """Construct synthetic cohort evidence for declared custody controls."""
    protocol = _constructed_protocol()
    axis = [f"artificial-taxon-{index:02d}" for index in range(30)]
    regional = [0.99999] + [0.0] * 29
    starts = [
        [1 / 30] * 30,
        [0.5 / 30 + 0.5 * value / math.fsum(regional) for value in regional],
    ] + [
        [0.5 / 30 + (0.5 if index == j else 0) for j in range(30)]
        for index in range(30)
    ]
    identities = {row["request_sha256"]: row for row in protocol["logical_requests"]}

    def attempts(row: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "item_id": row["local_record_id"],
                "request_sha256": row["request_sha256"],
                "ring_index": ring,
                "outer_m": [500, 1000][ring],
                "start_id": name,
                "start": start,
                "execution": "new",
                "accepted": True,
                "result": {
                    "success": True,
                    "fun": 0.25,
                    "x": [1 / 30] * 30,
                    "nit": 1,
                    "nfev": 1,
                    "certification_nfev": 1,
                },
                "observed_calls": {"objective": 2, "jacobian": 1},
                "elapsed_seconds": 0.001,
            }
            for ring in range(2)
            for name, start in zip(STARTS, starts, strict=True)
        ]

    prior_items = sorted(
        (
            row
            for row in identities.values()
            if row["regional_anchor_record_id"] == "author:BROADOWN"
        ),
        key=lambda row: row["local_record_id"],
    )
    first_items = [
        row
        for row in prior_items
        if row["local_record_id"] in ("author:CUTHILL2", "author:LONGBREACH")
    ]
    rest_items = [row for row in prior_items if row not in first_items]
    first = [value for row in first_items for value in attempts(row)]
    prior_new = [value for row in rest_items for value in attempts(row)]
    new = [
        value
        for checksum, row in sorted(identities.items())
        if row["regional_anchor_record_id"] == "author:BECKHAM"
        for value in attempts(row)
    ]

    def events(rows: list[dict[str, Any]]) -> bytes:
        lines = []
        for row in rows:
            started = {
                key: row[key]
                for key in (
                    "item_id",
                    "request_sha256",
                    "ring_index",
                    "outer_m",
                    "start_id",
                    "start",
                    "execution",
                )
            }
            lines.extend(
                [
                    raw({"event": "attempt_started", **started}),
                    raw({"event": "attempt_completed", **row}),
                ]
            )
        return b"".join(lines)

    def selections(
        identity: dict[str, Any], population: list[dict[str, Any]], execution: str
    ) -> list[dict[str, Any]]:
        answer = []
        for ring in range(2):
            best = next(
                row
                for row in population
                if row["request_sha256"] == identity["request_sha256"]
                and row["ring_index"] == ring
            )
            x = best["result"]["x"]
            total = sum(x)
            composition = dict(zip(axis, [value / total for value in x], strict=True))
            answer.append(
                {
                    "item_id": best["item_id"],
                    "request_sha256": best["request_sha256"],
                    "ring_index": ring,
                    "attempted": 32,
                    "accepted": 32,
                    "refused": 0,
                    "selected_start_id": best["start_id"],
                    "selected_objective": 0.25,
                    "selected_attempt_sha256": helpers._canonical_sha(best),
                    "execution": execution,
                    "raw_x": x,
                    "raw_sum": total,
                    "composition": composition,
                    "composition_sum": sum(composition.values()),
                    "transform": "Artificial unrounded source-control composition",
                }
            )
        return answer

    previous = {
        "total_attempts": 832,
        "new_attempts": prior_new,
        "failures": [],
        "training": [
            {
                "item_id": row["local_record_id"],
                "request_sha256": row["request_sha256"],
                "regional_cover": regional,
                "selections": selections(
                    row, first + prior_new, "reused" if row in first_items else "new"
                ),
            }
            for row in prior_items
        ],
    }
    bodies = {
        "start_report": raw({"attempts": first}),
        "start_trials": events(first),
        "start_protocol": raw({}),
        "start_receipt": raw({}),
        "development_protocol": raw({}),
    }
    previous["reused_report"] = pin(bodies["start_report"])
    previous["reused_trials"] = pin(bodies["start_trials"])
    bodies["development_training"] = raw(previous)
    bodies["development_trials"] = events(prior_new)
    authority = {
        "original_receipts": {"independent_review": {"sha256": subject.PRIOR_REVIEW}},
        "execution": {"native_exit": 0, "common_exit": 0, "outer_exit": 0},
        "independent_semantics": {
            "attempts": 832,
            "new_attempts": 704,
            "reused_attempts": 128,
            "failures": [],
        },
        "products": {
            role: {"original_reference": pin(bodies["development_" + role])}
            for role in ("training", "trials")
        },
    }
    bodies["development_receipt"] = raw(authority)
    protocol["prior_evidence"] = {key: pin(value) for key, value in bodies.items()}
    source_experiment = _constructed_experiment()
    source_experiment["request_template"]["taxa"] = axis
    inputs = {row["path"]: raw({}) for row in protocol["inputs"]}
    for site in source_experiment["sites"]:
        metadata = {
            "site_id": site["site_id"],
            "sample_id": site["site_id"] + ":artificial",
            "bin_id": "artificial",
            "coordinate": 1500,
            "age_type": "calendar_bp",
            "age_support_bp": [[1250, 1750]],
            "chronology_evidence_id": "artificial",
        }
        inputs[site["raw"]["path"]] = raw(
            {
                "data_kind": "source_observations",
                "taxa": axis,
                "sample": {**metadata, "counts": [1] * 30},
            }
        )
        inputs[site["geometry"]["path"]] = raw({"sample_metadata": metadata})
        for role in ("raw", "geometry"):
            site[role]["sha256"] = pin(inputs[site[role]["path"]])["sha256"]
    inputs["experiment.json"] = raw(source_experiment)
    protocol["inputs"] = [
        {**pin(value), "path": name} for name, value in sorted(inputs.items())
    ]
    pool = {}
    for checksum, identity in identities.items():
        reused = identity["regional_anchor_record_id"] == "author:BROADOWN"
        population = first + prior_new if reused else new
        pool[checksum] = {
            "item_id": identity["local_record_id"],
            "request_sha256": checksum,
            "taxa": axis,
            "regional_cover": regional,
            "regional_fraction_sum": sum(regional),
            "regional_percent_precision_decimals": 3,
            "selections": selections(
                identity, population, "reused" if reused else "new"
            ),
            "execution": "reused" if reused else "new",
        }
    training = {
        "counts": protocol["counts"],
        "logical_requests": protocol["logical_requests"],
        "prior_evidence": protocol["prior_evidence"],
        "numerical_requests": pool,
        "new_attempts": new,
    }
    bodies["training"] = raw(training)
    bodies["trials"] = events(new)
    # Source-control helper computes only metadata/minima; it never calls a model.
    group_by_record = {
        row["target_record_id"]: row["fold_id"] for row in protocol["logical_requests"]
    }
    records = sorted(group_by_record)
    folds = {
        group_by_record[target]: {
            "fold_id": group_by_record[target],
            "train_record_ids": sorted(set(records) - {target}),
            "test_record_ids": [target],
            "train_group_ids": sorted(
                group_by_record[record] for record in records if record != target
            ),
            "test_group_ids": [group_by_record[target]],
        }
        for target in records
    }
    pool_result = {"group_by_record": group_by_record, "folds": folds}
    slots = []
    access = []
    scores = []
    composition = dict(zip(axis, [1 / 30] * 30, strict=True))
    sites = {row["record_id"]: row for row in source_experiment["sites"]}
    for fold_id, fold in sorted(pool_result["folds"].items()):
        logical = [
            row for row in protocol["logical_requests"] if row["fold_id"] == fold_id
        ]
        anchor = logical[0]["regional_anchor_record_id"]
        target = fold["test_record_ids"][0]
        groups = sorted(
            pool_result["group_by_record"][row["local_record_id"]] for row in logical
        )
        for method in ("training_mean", "nearest_site", "inverse_distance_squared"):
            manifest = {
                "schema_version": "lra-heldout-prediction.v1",
                "fold": fold,
                "target_group_id": fold["test_group_ids"][0],
                "pollen_fraction": composition,
                "vegetation_fraction": composition,
                "spatial_method": method,
                "allowed_input_closure": fold["train_record_ids"],
                "input_lineage": dict.fromkeys(fold["train_record_ids"], []),
                "experiment": "all_target_pollen_withheld",
                "uncertainty_status": "deterministic_point_prediction_no_predictive_intervals",
                "scientific_acceptance": "not_evaluated_by_prediction",
                "predictor_group_ids": groups,
            }
            prediction = {
                "fold_id": fold_id,
                "record_id": target,
                "bin_id": "artificial",
                "baseline": method,
                "pollen_fraction": composition,
                "vegetation_fraction": composition,
                "prediction_manifest": manifest,
                "prediction_manifest_sha256": helpers._canonical_sha(manifest),
            }
            geometry = {
                "support_profile": source_experiment["support_profile"],
                "local_support_radius_m": source_experiment["local_support_radius_m"],
                "outer_fold": fold,
                "regional_anchor_record_id": anchor,
                "regional_value_source_record_ids": [anchor],
                "regional_identity_source_record_ids": fold["train_record_ids"],
                "regional_identity_policy": "conservative_all_training_fit_receipts",
                "predictor_group_ids": groups,
                "regional_cover": regional,
                "target_geometry_sha256": sites[target]["geometry"]["sha256"],
            }
            slots.append(
                {
                    "fold_id": fold_id,
                    "record_id": target,
                    "baseline": method,
                    "status": "predicted",
                    "prediction": prediction,
                    "geometry": geometry,
                }
            )
            scores.append(
                {
                    "fold_id": fold_id,
                    "record_id": target,
                    "baseline": method,
                    "target": "pollen_composition",
                    "status": "scored",
                    "taxon_count": 30,
                    "scored_taxon_count": 30,
                    "missing_observed_taxa": [],
                    "observed_total_count": 30,
                    "zero_probability_positive_count": False,
                    "mae_fraction": 0.0,
                    "rmse_fraction": 0.0,
                    "bias_fraction": 0.0,
                    "total_variation": 0.0,
                    "count_conditioned_deviance": 0.0,
                    "signed_error_by_taxon": [[key, 0.0] for key in sorted(axis)],
                }
            )
    frozen = {
        "profile": protocol["profile"],
        "training": pin(bodies["training"]),
        "folds": [pool_result["folds"][key] for key in sorted(pool_result["folds"])],
        "slots": slots,
    }
    bodies["prediction_freeze"] = raw(frozen)
    for fold_id, fold in sorted(pool_result["folds"].items()):
        access.append(
            {
                "fold_id": fold_id,
                "record_id": fold["test_record_ids"][0],
                "prediction_freeze": pin(bodies["prediction_freeze"]),
                "ordering": "complete45_slot_freeze_reopened_before_new_cohort_scoring",
            }
        )
    bodies["outcome_access"] = b"".join(raw(row) for row in access)
    bodies["report"] = raw(
        {
            "schema_version": "author-love-cohort-development.v1",
            "profile": protocol["profile"],
            "counts": protocol["counts"],
            "scientific_acceptance": "not_evaluated",
            "training": pin(bodies["training"]),
            "prediction_freeze": pin(bodies["prediction_freeze"]),
            "failures": [],
            "refused_folds": 0,
            "predicted_folds": 15,
            "scores": scores,
        }
    )
    return (
        bodies,
        {role: pin(value) for role, value in bodies.items()},
        protocol,
        inputs,
    )
