"""Whole-site temporal folds and exact train-only uniform request sharing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra.api import LRABatchItem
from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import make_request
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")
WINDOWS = {4: (13, 750, 1250, 1000), 6: (14, 1750, 2250, 2000)}


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def build(
    spec: SourceExperimentSpec, prepared: Path, window: int, profile: dict[str, Any]
) -> dict[str, Any]:
    """Decode training channels only; actual request counts are observed, not assumed."""
    if type(window) is not int or window not in WINDOWS:
        raise ValueError("Declared temporal window4/6 required")
    n, younger, older, label = WINDOWS[window]
    template: dict[str, Any] = spec.template()
    if (
        len(spec.sites) != n
        or spec.baselines != BASELINES
        or spec.local_ring_count != 2
        or spec.local_support_radius_m != 1000
        or spec.support_profile != "same-outer-radius-homogeneous-v1"
        or template["taxa"] != profile["taxa"]
        or len(template["taxa"]) != 30
        or digest(template["parameters"]) != profile["parameters_sha256"]
        or template["configuration"] != profile["configuration"]
        or template["method_profile"] != "ring-taxon-preserving"
        or template["temporal_matching"]["bins"]
        != [
            {
                "bin_id": "author-TW" + str(window),
                "younger_bp": younger,
                "older_bp": older,
            }
        ]
    ):
        raise ValueError(
            "Admitted constrained physical profile/window must be unchanged"
        )
    if tuple(
        site.record.record_id for site in spec.sites
    ) != spec.regional_priority or any(
        site.record.record_id != "author:" + site.record.site_id for site in spec.sites
    ):
        raise ValueError("Source site/core identity and priority required")
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    if len(folds) != n or any(len(fold.test_record_ids) != 1 for fold in folds):
        raise ValueError(
            "One admitted representation per whole physical site/window required"
        )
    by_record = {site.record.record_id: site for site in spec.sites}
    groups = {
        record: fold.test_group_ids[0]
        for fold in folds
        for record in fold.test_record_ids
    }
    numerical: dict[str, LRABatchItem] = {}
    contexts: list[dict[str, Any]] = []
    logical: list[dict[str, Any]] = []
    consumed_pollen: set[str] = set()
    consumed_geometry: set[str] = set()
    for fold in folds:
        anchor = next(
            record
            for record in spec.regional_priority
            if record in fold.train_record_ids
        )
        predictors = tuple(
            by_record[record]
            for record in fold.train_record_ids
            if groups[record] != groups[anchor]
        )
        if len(predictors) != n - 2:
            raise ValueError(
                "Training-only anchor and local whole-site population differs"
            )
        local_pollen: set[str] = set()
        local_geometry: set[str] = set()
        context: dict[str, Any] = {
            "fold": fold,
            "anchor": by_record[anchor],
            "predictors": predictors,
            "requests": [],
        }
        for site in predictors:
            payload = make_request(
                spec,
                site,
                by_record[anchor],
                fold,
                prepared,
                consumed_pollen=local_pollen,
                consumed_geometry=local_geometry,
            )
            validate_request(payload, input_root=prepared)
            request = LRABatchItem(site.record.record_id, payload)
            batch = LRABatchItem("request:" + request.request_sha256, payload)
            previous = numerical.setdefault(request.request_sha256, batch)
            if (
                previous.canonical_request != batch.canonical_request
                or not {site.record.record_id, anchor}.issubset(fold.train_record_ids)
                or set(fold.test_record_ids) & local_pollen
            ):
                raise ValueError("Request identity or train/target separation differs")
            context["requests"].append(request.request_sha256)
            logical.append(
                {
                    "fold_id": fold.fold_id,
                    "target_record_id": fold.test_record_ids[0],
                    "local_record_id": site.record.record_id,
                    "regional_anchor_record_id": anchor,
                    "request_sha256": request.request_sha256,
                }
            )
        contexts.append(context)
        consumed_pollen.update(local_pollen)
        consumed_geometry.update(local_geometry)
    manifest = {
        "schema_version": "author-love-temporal-request-manifest.v1",
        "window": window,
        "folds": [fold.as_dict() for fold in folds],
        "logical_requests": logical,
        "numerical_requests": [
            {"request_sha256": checksum, "batch_item_id": item.item_id}
            for checksum, item in sorted(numerical.items())
        ],
        "counts": {
            "sites": n,
            "folds": len(folds),
            "logical_requests": len(logical),
            "unique_requests": len(numerical),
            "prediction_slots": n * len(BASELINES),
        },
        "forecast_unique_requests": 2 * n - 3,
        "forecast_matches_actual": len(numerical) == 2 * n - 3,
        "source_time_label_bp": label,
        "independence": "Site/core group IDs persist across windows; grids, repeats and periods are ancestry, not additional independent sites.",
    }
    return {
        "manifest": manifest,
        "contexts": contexts,
        "numeric": numerical,
        "groups": groups,
        "consumed_pollen": consumed_pollen,
        "consumed_geometry": consumed_geometry,
    }
