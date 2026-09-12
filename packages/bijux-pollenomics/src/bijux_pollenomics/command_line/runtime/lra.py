"""Structured LRA command results; scientific refusals use exit code two."""

from __future__ import annotations

import argparse
import json
from typing import Any

from ...analysis.lra.api import LRARefusal, run_lra_request, validate_lra_inputs


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def run_lra_command(args: argparse.Namespace) -> int:
    """Execute one supported request without hiding input or engine failures."""
    try:
        payload = json.loads(
            args.request.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs
        )
        if not isinstance(payload, dict):
            raise LRARefusal("invalid_lra_json", "Request must be a JSON object")
        if args.command == "validate-lra-input":
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
    return 0
