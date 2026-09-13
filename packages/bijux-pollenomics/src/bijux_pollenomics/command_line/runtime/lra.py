"""Structured LRA command results; scientific refusals use exit code two."""

from __future__ import annotations

import argparse
import json
from typing import Any

from ...analysis.lra.api import (
    LRABatchItem,
    LRABatchLimits,
    LRARefusal,
    run_lra_batch,
    run_lra_request,
    validate_lra_inputs,
)
from .json_inputs import unique_pairs as _unique_pairs


def _run_batch(
    payload: dict[str, Any], args: argparse.Namespace
) -> tuple[dict[str, object], int]:
    if (
        set(payload) != {"schema_version", "items"}
        or payload["schema_version"] != "lra-batch-request.v1"
        or not isinstance(payload["items"], list)
    ):
        raise LRARefusal(
            "invalid_lra_batch_json",
            "Expected lra-batch-request.v1 with an items array",
        )
    items = []
    for item in payload["items"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"item_id", "request"}
            or not isinstance(item["request"], dict)
        ):
            raise LRARefusal(
                "invalid_lra_batch_json", "Each item needs item_id and a request object"
            )
        items.append(LRABatchItem(item["item_id"], item["request"]))
    result = run_lra_batch(
        items,
        input_root=args.input_root,
        cache_root=args.cache_root,
        report_root=args.report_root,
        limits=LRABatchLimits(max_workers=args.max_workers, max_items=args.max_items),
    )
    return result.as_dict(), 130 if result.interrupted else (
        0 if result.all_items_completed else 2
    )


def run_lra_command(args: argparse.Namespace) -> int:
    """Execute one supported request without hiding input or engine failures."""
    if args.command in {
        "prepare-lra-experiment",
        "score-lra-experiment",
        "prepare-lra-observation-uncertainty",
        "score-lra-observation-coverage",
    }:
        from .lra_validation import run_lra_experiment_command

        return run_lra_experiment_command(args)
    exit_code = 0
    try:
        if args.command == "render-lra-report":
            return _render_report(args)
        payload = json.loads(
            args.request.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs
        )
        if not isinstance(payload, dict):
            raise LRARefusal("invalid_lra_json", "Request must be a JSON object")
        if args.command == "run-lra-batch":
            result, exit_code = _run_batch(payload, args)
        elif args.command == "validate-lra-input":
            accepted = validate_lra_inputs(payload, input_root=args.input_root)
            result = {
                "status": "validated_exploratory_input",
                "request_sha256": accepted.sha256,
                "scientific_acceptance": "not_evaluated",
            }
        else:
            product = run_lra_request(
                payload, input_root=args.input_root, destination=args.output
            )
            result = {
                "status": "generated_exploratory",
                "directory": str(product.directory),
                "manifest_sha256": product.manifest_sha256,
                "scientific_content_sha256": product.scientific_content_sha256,
            }
    except LRARefusal as exc:
        print(json.dumps(exc.as_dict(), sort_keys=True))
        return 2
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "refused",
                    "reason_code": "lra_request_io_or_encoding",
                    "detail": str(exc),
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return exit_code


def _render_report(args: argparse.Namespace) -> int:
    from ...reporting.lra_products.api import LRAPresentationRefusal, render_lra_report

    try:
        report = render_lra_report(
            args.product,
            expected_manifest_sha256=args.expected_manifest_sha256,
            geometry_path=args.geometry,
            expected_geometry_sha256=args.expected_geometry_sha256,
            destination=args.output,
            temporal_profile=args.temporal_profile,
        )
    except LRAPresentationRefusal as exc:
        print(
            json.dumps(
                {
                    "status": "refused",
                    "reason_code": exc.reason_code,
                    "detail": str(exc),
                },
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "status": "generated_exploratory",
                "scientific_acceptance": "not_evaluated",
                "directory": str(report.directory),
                "manifest_sha256": report.manifest_sha256,
                "product_manifest_sha256": report.product_manifest_sha256,
                "geometry_sha256": report.geometry_sha256,
                "mapped_site_count": report.mapped_site_count,
                "refused_site_count": report.refused_site_count,
            },
            sort_keys=True,
        )
    )
    return 0
