"""Reconstruct every source slot independently of the comparison producer."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
import hashlib
import json
import re
from typing import Any

from .independent_controls import AXIS, COLUMNS
from .independent_sources import (
    depth_pairs,
    literal_count,
    native_samples,
    original_rows,
)

COMMENTS = (
    "Betula",
    "Cyperaceae",
    "Juniperus-type",
    "Pinus diploxylon-type",
    "Gramineae",
)


def canonical_digest(value: object) -> str:
    """Hash the canonical JSON encoding of a source-accounting value."""
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def classified_token(token: str) -> tuple[str, int | None, str | None]:
    """Classify a literal count token while retaining its refusal reason."""
    status, value = literal_count(token)
    if status == "blank":
        return "blank", None, "empty_cell"
    if status == "invalid":
        if "/" in token:
            reason = "unparsed_count_token"
        elif re.fullmatch(
            r"[+-]?(?:s?nan[0-9]*|inf(?:inity)?)", token.strip(), re.IGNORECASE
        ):
            reason = "nonfinite_count"
        else:
            try:
                number = Fraction(token.strip())
            except (ValueError, ZeroDivisionError):
                reason = "unparsed_count_token"
            else:
                reason = "negative_count" if number < 0 else "nonintegral_count"
        return status, None, reason
    return "explicit_zero" if value == 0 else "explicit_positive_integer", value, None


def check_comparison(
    result: dict[str, Any],
    original_body: bytes,
    native_body: bytes,
    *,
    expected_reported: int,
    expected_samples: int,
) -> dict[str, int]:
    """Check complete ownership, literals, preconditions and compact audit hashes."""
    _, _, originals = original_rows(original_body, COLUMNS)
    native = native_samples(native_body, AXIS)
    pairs = depth_pairs(originals, native)
    if len(pairs) != expected_samples:
        raise ValueError("Independent sample population differs")
    owners = []
    slots = []
    for source, target in pairs:
        owner = {
            "native_sample_id": target.sample_id,
            "depth_native_exact": f"{target.depth_native.numerator}/{target.depth_native.denominator}",
            "original_depth_token": source.depth_token,
            "original_row_index": originals.index(source),
        }
        owners.append(owner)
        for position, ((name, taxon_id), column) in enumerate(
            zip(AXIS, COLUMNS, strict=True)
        ):
            token = source.tokens[position]
            status, value, reason = classified_token(token)
            observed = target.values[position]
            agrees = observed is not None and value is not None and observed == value
            slots.append(
                {
                    **owner,
                    "taxon": name,
                    "original_column": column,
                    "native_taxon_id": taxon_id,
                    "original_token": token,
                    "original_status": status,
                    "original_integer_value": value,
                    "original_invalid_reason": reason,
                    "native_reported": observed is not None,
                    "native_value": observed,
                    "comparison_status": "matched_reported_count"
                    if agrees
                    else "reported_count_disagreement"
                    if observed is not None
                    else "absent_native_datum",
                }
            )
    reported = [s for s in slots if s["native_reported"]]
    conflicts = [
        s for s in reported if s["comparison_status"] != "matched_reported_count"
    ]
    absent = [s for s in slots if not s["native_reported"]]
    population_matches = len(reported) == expected_reported
    passes = not conflicts and population_matches
    binding = {
        "original_rows": len(originals),
        "native_samples": len(native),
        "unique_original_depths": len({r.depth_m for r in originals}),
        "unique_native_depths": len({r.depth_native for r in native}),
        "original_to_native_depth_factor": "100",
        "original_depth_unit": "m",
        "native_depth_unit": "not_explicit_in_payload",
        "duplicate_original_depths": [],
        "duplicate_native_depths": [],
        "original_only_depths": [],
        "native_only_depths": [],
        "original_order_strictly_increasing": [r.depth_m for r in originals]
        == sorted(r.depth_m for r in originals),
        "native_order_strictly_increasing": [r.depth_native for r in native]
        == sorted(r.depth_native for r in native),
        "depth_pairs_sha256": canonical_digest(owners),
    }
    comparison = {
        "total_slots": len(slots),
        "native_reported_slots": len(reported),
        "native_absent_slots": len(absent),
        "reported_count_matches": len(reported) - len(conflicts),
        "reported_count_disagreements": len(conflicts),
        "reported_population_matches": population_matches,
        "reported_count_precondition_passed": passes,
        "original_token_status_counts": dict(
            Counter(s["original_status"] for s in slots)
        ),
        "slot_audit_sha256": canonical_digest(slots),
        "reported_disagreement_examples": conflicts[:8],
        "disagreement_examples_limit": 8,
    }
    taxa = []
    for (name, taxon_id), column, comment in zip(AXIS, COLUMNS, COMMENTS, strict=True):
        selected = [s for s in slots if s["taxon"] == name]
        taxa.append(
            {
                "taxon": name,
                "original_column": column,
                "original_epd_comment": comment,
                "native_taxon_id": taxon_id,
                "reported_pairs": sum(s["native_reported"] is True for s in selected),
                "matched_pairs": sum(
                    s["comparison_status"] == "matched_reported_count" for s in selected
                ),
                "absent_native_slots": sum(not s["native_reported"] for s in selected),
                "original_token_status_counts": dict(
                    Counter(s["original_status"] for s in selected)
                ),
            }
        )
    expected = {
        "status": "reported_counts_match"
        if passes
        else "refused_reported_count_correspondence",
        "depth_binding": binding,
        "comparison": comparison,
        "taxon_comparisons": taxa,
        "absence_candidates": absent if passes else [],
        "candidate_classification_status": "enabled_reported_counts_match"
        if passes
        else "withheld_reported_count_conflict",
    }
    for key, expected_value in expected.items():
        if canonical_digest(result[key]) != canonical_digest(expected_value):
            raise ValueError(f"Independent source correspondence differs: {key}")
    return {
        "source_rows_checked": len(originals),
        "native_samples_checked": len(native),
        "slots_checked": len(slots),
        "reported_checked": len(reported),
        "reported_disagreements": len(conflicts),
        "absent_native_checked": len(absent),
    }
