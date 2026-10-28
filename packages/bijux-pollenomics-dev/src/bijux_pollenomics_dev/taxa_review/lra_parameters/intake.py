"""Bind physical review and native projection files for parameter review."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from ..decisions import load_review_json
from ..workflow import read_review
from .projection import build_lra_parameter_review

JsonMap = dict[str, Any]


def _bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read(path: Path, expected: str) -> bytes:
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("Expected source hash must be exact lowercase SHA-256")
    if path.is_symlink() or not path.is_file():
        raise ValueError("Parameter review source must be a regular exact file")
    content = path.read_bytes()
    if _sha(content) != expected:
        raise ValueError("Physical parameter-review source hash differs")
    return content


def bind_lra_parameter_authorities(
    review_directory: Path,
    priority_path: Path,
    provenance_path: Path,
    output_directory: Path,
    *,
    expected_review_sha256: str,
    expected_priority_sha256: str,
    expected_provenance_sha256: str,
) -> tuple[JsonMap, JsonMap, JsonMap, str]:
    """Write receipt-bound IO projections without changing native source reports.

    Lower-level priority/attribution producers describe native source identities.
    The parameter consumer additionally requires exact physical review/priority
    artifact hashes. This boundary verifies those bytes and writes distinct
    projections carrying the required file bindings; original reports stay intact.
    """
    review_path = review_directory / "taxa-review.json"
    review_bytes = _read(review_path, expected_review_sha256)
    priority_bytes = _read(priority_path, expected_priority_sha256)
    provenance_bytes = _read(provenance_path, expected_provenance_sha256)
    review: JsonMap = read_review(review_directory)
    if load_review_json(review_bytes) != review:
        raise ValueError("Completed review differs from pinned physical review")
    priority = load_review_json(priority_bytes)
    provenance = load_review_json(provenance_bytes)
    if "input_file_sha256" in priority or "input_file_sha256" in provenance:
        raise ValueError("Native inputs already carry unsupported file bindings")
    priority_bound = deepcopy(priority)
    priority_bound["input_file_sha256"] = {"full_review": expected_review_sha256}
    priority_bound_bytes = _bytes(priority_bound)
    provenance_bound = deepcopy(provenance)
    provenance_bound["input_file_sha256"] = {
        "full_review": expected_review_sha256,
        "priority": _sha(priority_bound_bytes),
    }
    provenance_bound_bytes = _bytes(provenance_bound)
    provenance_bound_sha256 = _sha(provenance_bound_bytes)
    # The maintained semantic validator checks source snapshots, row ownership,
    # counts and review identities before any bound output is published.
    build_lra_parameter_review(
        priority_bound,
        provenance_bound,
        review,
        provenance_file_sha256=provenance_bound_sha256,
    )
    for path, expected in (
        (review_path, expected_review_sha256),
        (priority_path, expected_priority_sha256),
        (provenance_path, expected_provenance_sha256),
    ):
        _read(path, expected)
    documents = {
        "priority.json": priority_bound_bytes,
        "provenance.json": provenance_bound_bytes,
    }
    receipt: JsonMap = {
        "schema_version": "neotoma-lra-parameter-file-bindings.v1",
        "source_files": {
            "completed_review": expected_review_sha256,
            "native_priority": expected_priority_sha256,
            "native_provenance": expected_provenance_sha256,
        },
        "bound_files": {
            name: {"sha256": _sha(body), "bytes": len(body)}
            for name, body in documents.items()
        },
        "scientific_acceptance": "not_evaluated",
        "canonical_import_allowed": False,
        "publication_allowed": False,
        "scope": "Physical artifact and native semantic bindings only; no taxon/PPE acceptance, reviewer authentication or source rights assigned.",
    }
    if output_directory.exists() or output_directory.is_symlink():
        raise FileExistsError(output_directory)
    output_directory.mkdir(parents=True, exist_ok=False)
    for name, body in documents.items():
        with (output_directory / name).open("xb") as stream:
            stream.write(body)
    with (output_directory / "completion.json").open("xb") as stream:
        stream.write(_bytes(receipt))
    return priority_bound, provenance_bound, review, provenance_bound_sha256


def main() -> int:
    """Bind explicitly pinned completed review and native reports to fresh files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-directory", type=Path, required=True)
    parser.add_argument("--priority", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--review-sha256", required=True)
    parser.add_argument("--priority-sha256", required=True)
    parser.add_argument("--provenance-sha256", required=True)
    args = parser.parse_args()
    bind_lra_parameter_authorities(
        args.review_directory,
        args.priority,
        args.provenance,
        args.output_directory,
        expected_review_sha256=args.review_sha256,
        expected_priority_sha256=args.priority_sha256,
        expected_provenance_sha256=args.provenance_sha256,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
