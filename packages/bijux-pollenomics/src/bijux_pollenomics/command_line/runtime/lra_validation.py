"""CLI delegation to frozen prediction and separate observation-scoring phases."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any, Protocol

from ...analysis.lra.api import LRARefusal
from ...analysis.lra_validation import ValidationRefusal
from ...analysis.lra_validation.experiments import (
    prepare_experiment_predictions,
    prepare_fitted_spatial_predictions,
    prepare_local_pollen_predictions,
    prepare_spatial_block_predictions,
    read_experiment_product,
    score_experiment_predictions,
)
from ...analysis.lra_validation.experiments.configuration import (
    BLOCK_PROFILE,
    FITTED_PROFILE,
    LOCAL_PROFILE,
    PROFILE,
    SOURCE_PROFILE,
    TEMPORAL_PROFILE,
)
from ...analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
    read_member,
)
from ...analysis.lra_validation.observation_uncertainty import (
    ObservationUncertaintyPlan,
    generate_pollen_observation_uncertainty,
    score_pollen_observation_coverage,
)
from ...analysis.lra_validation.temporal.persistence import (
    prepare_temporal_persistence_predictions,
    read_temporal_persistence_predictions,
    score_temporal_persistence_predictions,
)
from .json_inputs import read_object


class _PredictionOperation(Protocol):
    def __call__(
        self,
        spec: Mapping[str, object],
        *,
        input_root: Path,
        cache_root: Path,
        destination: Path,
        workers: int = 1,
    ) -> ExperimentProduct: ...


def run_lra_experiment_command(args: argparse.Namespace) -> int:
    """Return operational status independently of unevaluated scientific acceptance."""
    try:
        if args.command == "prepare-lra-experiment":
            request = read_object(args.request)
            profile = request.get("profile")
            prepare: _PredictionOperation
            if profile == PROFILE or profile == SOURCE_PROFILE:
                prepare = prepare_experiment_predictions
            elif profile == LOCAL_PROFILE:
                prepare = prepare_local_pollen_predictions
            elif profile == FITTED_PROFILE:
                prepare = prepare_fitted_spatial_predictions
            elif profile == BLOCK_PROFILE:
                prepare = prepare_spatial_block_predictions
            elif profile == TEMPORAL_PROFILE:
                prepare = prepare_temporal_persistence_predictions
            else:
                raise ValidationRefusal(
                    "unsupported_experiment_profile",
                    "Declare an implemented experiment profile",
                )
            product = prepare(
                request,
                input_root=args.input_root,
                cache_root=args.cache_root,
                destination=args.output,
                workers=args.max_workers,
            )
            _, manifest = read_experiment_product(
                product.directory, expected_manifest_sha256=product.manifest_sha256
            )
            scientific = manifest["scientific_payload"]
            if not isinstance(scientific, dict):
                raise ValidationRefusal(
                    "invalid_experiment_product", "Missing scientific payload"
                )
            accounting: dict[str, Any] = {
                key: scientific[key]
                for key in (
                    "requested_folds",
                    "requested_predictions",
                    "generated_predictions",
                    "failed_folds",
                    "interrupted",
                    "all_predictions_generated",
                )
            }
            code = (
                130
                if accounting["interrupted"]
                else (0 if accounting["all_predictions_generated"] else 2)
            )
        elif args.command == "score-lra-experiment":
            # Authenticate prediction identity before opening any outcome inventory.
            _, prediction_manifest = read_experiment_product(
                args.product, expected_manifest_sha256=args.expected_manifest_sha256
            )
            temporal = prediction_manifest.get("profile") == TEMPORAL_PROFILE
            if temporal:
                read_temporal_persistence_predictions(
                    args.product,
                    expected_manifest_sha256=args.expected_manifest_sha256,
                )
            score = (
                score_temporal_persistence_predictions
                if temporal
                else score_experiment_predictions
            )
            product = score(
                args.product,
                expected_manifest_sha256=args.expected_manifest_sha256,
                outcome_root=args.outcome_root,
                outcome_inventory=read_object(args.outcome_inventory),
                destination=args.output,
            )
            scores = read_member(product, "scores.json")
            metric_field = "metrics" if temporal else "score"
            if not isinstance(scores, list) or any(
                not isinstance(row, dict) or not isinstance(row.get(metric_field), dict)
                for row in scores
            ):
                raise ValidationRefusal(
                    "invalid_experiment_product", "Missing score ledger"
                )
            counts = Counter(str(row[metric_field]["status"]) for row in scores)
            accounting = {
                "requested_scores": len(scores),
                "score_status_counts": dict(sorted(counts.items())),
            }
            code = 0 if counts.get("scored", 0) == len(scores) else 2
        elif args.command == "prepare-lra-observation-uncertainty":
            plan = ObservationUncertaintyPlan.from_dict(read_object(args.plan))
            product = generate_pollen_observation_uncertainty(
                args.predictions,
                plan,
                evidence_root=args.evidence_root,
                destination=args.output,
            )
            _, manifest = read_experiment_product(
                product.directory, expected_manifest_sha256=product.manifest_sha256
            )
            scientific = manifest["scientific_payload"]
            if not isinstance(scientific, dict):
                raise ValidationRefusal(
                    "invalid_experiment_product", "Missing uncertainty ledger"
                )
            counts = scientific["status_counts"]
            accounting = {
                "requested_units": scientific["requested_units"],
                "status_counts": counts,
            }
            code = (
                130
                if counts.get("not_run", 0)
                else (
                    0
                    if counts.get("generated", 0) == scientific["requested_units"]
                    else 2
                )
            )
        elif args.command == "score-lra-observation-coverage":
            product = score_pollen_observation_coverage(
                args.predictions,
                args.uncertainty,
                args.scores,
                expected_uncertainty_sha256=args.expected_uncertainty_sha256,
                expected_scores_sha256=args.expected_scores_sha256,
                destination=args.output,
            )
            _, manifest = read_experiment_product(
                product.directory, expected_manifest_sha256=product.manifest_sha256
            )
            scientific = manifest["scientific_payload"]
            if not isinstance(scientific, dict):
                raise ValidationRefusal(
                    "invalid_experiment_product", "Missing coverage ledger"
                )
            accounting = {
                key: scientific[key]
                for key in (
                    "requested_units",
                    "coverage_scored_units",
                    "coverage_refused_units",
                )
            }
            code = 0 if scientific["coverage_refused_units"] == 0 else 2
        else:
            raise ValidationRefusal("unknown_experiment_command", str(args.command))
        result = {
            "status": "generated_exploratory",
            "scientific_acceptance": "not_evaluated",
            "directory": str(product.directory),
            "manifest_sha256": product.manifest_sha256,
            "scientific_content_sha256": product.scientific_content_sha256,
            **accounting,
        }
    except (LRARefusal, ValidationRefusal) as exc:
        result = {
            "status": "refused",
            "reason_code": exc.reason_code,
            "detail": str(exc),
        }
        code = 2
    except (OSError, ValueError, TypeError) as exc:
        result = {
            "status": "refused",
            "reason_code": "lra_experiment_io_or_encoding",
            "detail": str(exc),
        }
        code = 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return code
