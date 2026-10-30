"""Independently bind recorded original zeros to a separate analytical panel."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
from typing import Any

from ..abborrtjarnen_source_counts.independent_controls import (
    AXIS as COUNT_AXIS,
)
from ..abborrtjarnen_source_counts.independent_controls import (
    COLUMNS,
)
from ..abborrtjarnen_source_counts.independent_result import (
    canonical_digest,
    check_comparison,
)
from ..abborrtjarnen_source_counts.independent_sources import (
    depth_pairs,
    literal_count,
    original_rows,
)
from ..abborrtjarnen_source_counts.independent_sources import (
    native_samples as exact_native,
)
from .independent_sources import AXIS, Sample

NATIVE_PROFILE = "neotoma_explicit_five_taxon"
SOURCE_PROFILE = "pangaea_recorded_zeros_local_nc"
SOURCE_PROTOCOL = Path(
    "reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/source-supported-counts/protocol.json"
)


def recorded_zero_panels(
    original_body: bytes,
    native_body: bytes,
    qualified: dict[str, Any],
    native: dict[int, Sample],
    *,
    expected_samples: int = 107,
    expected_reported: int = 527,
) -> tuple[dict[int, Sample], list[dict[str, Any]]]:
    """Require complete raw correspondence before admitting literal source zeros."""
    check_comparison(
        qualified,
        original_body,
        native_body,
        expected_samples=expected_samples,
        expected_reported=expected_reported,
    )
    if qualified["status"] != "reported_counts_match":
        raise ValueError("Reported source-count precondition did not pass")
    _, _, original = original_rows(original_body, COLUMNS)
    exact = exact_native(native_body, COUNT_AXIS)
    joined = depth_pairs(original, exact)
    if {row.sample_id for row in exact} != set(native):
        raise ValueError("Analytical/native owner populations differ")
    support = []
    analytical = {}
    for source, target in joined:
        sample = native[target.sample_id]
        if (
            sample.panel != target.values
            or Fraction(str(sample.depth)) != target.depth_native
        ):
            raise ValueError("Native panel or exact source depth differs")
        panel = list(sample.panel)
        for index, (name, taxon_id) in enumerate(COUNT_AXIS):
            if panel[index] is not None:
                continue
            if literal_count(source.tokens[index]) != ("zero", 0):
                raise ValueError("Absent native datum has no literal original zero")
            panel[index] = 0
            support.append(
                {
                    "native_sample_id": target.sample_id,
                    "depth_native_exact": f"{target.depth_native.numerator}/{target.depth_native.denominator}",
                    "original_depth_token": source.depth_token,
                    "original_row_index": original.index(source),
                    "taxon": name,
                    "original_column": COLUMNS[index],
                    "native_taxon_id": taxon_id,
                    "original_token": source.tokens[index],
                    "original_status": "explicit_zero",
                    "original_integer_value": 0,
                    "original_invalid_reason": None,
                    "native_reported": False,
                    "native_value": None,
                    "comparison_status": "absent_native_datum",
                }
            )
        analytical[target.sample_id] = replace(sample, panel=tuple(panel))
    if support != qualified["absence_candidates"]:
        raise ValueError(
            "Qualified source support differs from exact native-missing set"
        )
    missing = {
        (sample.sample_id, name)
        for sample in native.values()
        for name, n in zip(AXIS, sample.panel, strict=True)
        if n is None
    }
    if missing != {(row["native_sample_id"], row["taxon"]) for row in support}:
        raise ValueError("Original zeros do not cover exactly the native missing set")
    return analytical, support


def prepare_recorded_profile(
    repository: Path,
    source_root: Path,
    protocol: dict[str, Any],
    result: dict[str, Any],
    native: dict[int, Sample],
    identities: dict[str, str],
) -> tuple[dict[int, Sample], list[dict[str, Any]]]:
    """Bind additive profile metadata to exact raw source-supported panels."""
    proof_path = protocol["source_count_result"]
    verification_path = protocol["source_count_verification"]
    proof = json.loads((repository / proof_path).read_bytes())
    verified = json.loads((repository / verification_path).read_bytes())
    expected = {
        "status": "verified",
        "source_rows_checked": 107,
        "native_samples_checked": 107,
        "slots_checked": 535,
        "reported_checked": 527,
        "reported_disagreements": 0,
        "absent_native_checked": 8,
        "morphological_comments_checked": 5,
        "source_inputs_checked": 3,
        "model_fits": 0,
        "producer_source_commit": protocol["source_count_commit"],
        "observer_source_commit": protocol["source_count_commit"],
        "result_sha256": identities[f"repository/{proof_path}"],
    }
    if (
        any(verified.get(k) != v for k, v in expected.items())
        or proof["source_commit"] != protocol["source_count_commit"]
    ):
        raise ValueError("Qualified source-count evidence identity differs")
    if len(proof["input_sha256"]) != 3 or any(
        identities.get(k) != v for k, v in proof["input_sha256"].items()
    ):
        raise ValueError("Recorded-zero proof and analytical raw sources differ")
    original = source_root / "epd/pangaea/abbo-pollen-profile-pangaea-738429.tsv"
    current = (
        source_root
        / "neotoma/dataset-19913/2026-10-26T185139Z/dataset-19913.download.json"
    )
    analytical, support = recorded_zero_panels(
        original.read_bytes(), current.read_bytes(), proof, native
    )
    if len(support) != 8 or any(c["original_token"] != "0" for c in support):
        raise ValueError("Frozen source-zero token population differs")
    owner_keys = (
        "native_sample_id",
        "depth_native_exact",
        "original_depth_token",
        "original_row_index",
        "original_column",
        "native_taxon_id",
        "taxon",
    )
    if (
        list(owner_keys) != protocol["zero_owner_fields"]
        or canonical_digest([{k: c[k] for k in owner_keys} for c in support])
        != protocol["expected_zero_owners_sha256"]
    ):
        raise ValueError("Frozen source-zero owners differ")
    if (
        proof["depth_binding"]["depth_pairs_sha256"],
        proof["comparison"]["slot_audit_sha256"],
    ) != (protocol["depth_pairs_sha256"], protocol["slot_audit_sha256"]):
        raise ValueError("Frozen complete source-count audits differ")
    expected_support = {
        "count_profile": SOURCE_PROFILE,
        "native_complete_panels": sum(
            all(n is not None for n in s.panel) for s in native.values()
        ),
        "native_missing_panels": sum(
            any(n is None for n in s.panel) for s in native.values()
        ),
        "analytical_complete_panels": sum(
            all(n is not None for n in s.panel) for s in analytical.values()
        ),
        "recorded_source_zero_slots": len(support),
        "original_count_correspondence": {
            "result": proof_path,
            "independent_check": verification_path,
        },
        "rights_and_correspondence": protocol["rights_and_correspondence"],
    }
    if (
        result["count_profile"] != SOURCE_PROFILE
        or result["source_support"] != expected_support
    ):
        raise ValueError("Saved additive analytical source profile differs")
    return analytical, support
