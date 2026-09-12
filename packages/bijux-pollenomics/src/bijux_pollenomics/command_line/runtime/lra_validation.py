"""CLI delegation to frozen prediction and separate observation-scoring phases."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Any

from ...analysis.lra.api import LRARefusal
from ...analysis.lra_validation import ValidationRefusal
from ...analysis.lra_validation.experiments import (
    prepare_experiment_predictions,
    read_experiment_product,
    score_experiment_predictions,
)
from ...analysis.lra_validation.experiments.outputs import read_member
from .json_inputs import read_object


def run_lra_experiment_command(args: argparse.Namespace) -> int:
    """Return operational status independently of unevaluated scientific acceptance."""
    try:
        if args.command == "prepare-lra-experiment":
            product = prepare_experiment_predictions(
                read_object(args.request),
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
            read_experiment_product(
                args.product, expected_manifest_sha256=args.expected_manifest_sha256
            )
            product = score_experiment_predictions(
                args.product,
                expected_manifest_sha256=args.expected_manifest_sha256,
                outcome_root=args.outcome_root,
                outcome_inventory=read_object(args.outcome_inventory),
                destination=args.output,
            )
            scores = read_member(product, "scores.json")
            if not isinstance(scores, list) or any(
                not isinstance(row, dict) or not isinstance(row.get("score"), dict)
                for row in scores
            ):
                raise ValidationRefusal(
                    "invalid_experiment_product", "Missing score ledger"
                )
            counts = Counter(str(row["score"]["status"]) for row in scores)
            accounting = {
                "requested_scores": len(scores),
                "score_status_counts": dict(sorted(counts.items())),
            }
            code = 0 if counts.get("scored", 0) == len(scores) else 2
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
