"""Verify saved conditional ABBO moments, shared-time covariance and extrema."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import numpy as np

from .independent_moments import (
    ATOL,
    RTOL,
    Rational,
    _array_close,
    _close,
    _count_matrix,
    _fraction,
    _require,
    _window,
)
from .independent_sources import AXIS, BINS, PROTOCOL, TAXON_IDS, _native_inputs
from .independent_witnesses import _decimal, _range, _witness


def verify_result(
    repository: Path, source_root: Path, result_path: Path
) -> dict[str, Any]:
    """Observe saved source, exact scalar derivatives and all covariance extrema.

    The numerical oracle conditions on the saved positive transport factors;
    it does not replace their separate quadrature/source qualification.
    Exact bound strings describe the producer's serialized binary64 gradient,
    which is separately compared with independent rational differentiation.
    """
    result = json.loads(result_path.read_text())
    protocol_bytes = (repository / PROTOCOL).read_bytes()
    protocol = json.loads(protocol_bytes)
    _require(
        result["schema_version"] == "abborrtjarnen-ppe-dependence.v1"
        and tuple(result["taxon_axis"]) == AXIS,
        "Result profile or ordered taxon axis differs",
    )
    _require(
        protocol["window_ids"] == list(BINS)
        and tuple(protocol["taxon_axis"]) == AXIS
        and protocol["native_taxon_ids"] == list(TAXON_IDS),
        "Frozen analytical axes differ",
    )
    committed = subprocess.check_output(
        ["git", "-C", str(repository), "show", f"{result['source_commit']}:{PROTOCOL}"]
    )
    _require(
        committed == protocol_bytes, "Protocol differs from the declared source commit"
    )
    pooled, ppe, sd = _native_inputs(repository, source_root, protocol, result)
    _require(
        result["selected_sample_count"] == 29
        and result["sample_status_counts"]
        == dict(Counter(r["status"] for r in result["sample_account"])),
        "Saved sample accounting differs",
    )
    return {
        "status": "passed",
        "producer_source_commit": result["source_commit"],
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "native_samples_checked": 107,
        "selected_native_samples": 29,
        **_numeric_result(result, pooled, ppe, sd),
    }


def _numeric_result(
    result: dict[str, Any],
    pooled: dict[int, tuple[int, ...]],
    ppe: Rational,
    sd: Rational,
) -> dict[str, Any]:
    """Check all fixed-panel moments without importing their producer's math."""
    _require(
        [r["taxon"] for r in result["physical_response"]] == list(AXIS),
        "Transport factor axis differs",
    )
    factors = tuple(_fraction(r["factor"]) for r in result["physical_response"])
    _require(all(x > 0 for x in factors), "Nonpositive conditional transport factor")
    _require(
        all(
            _fraction(r["estimated_absolute_error"]) >= 0
            and r["rigorous_error_bound"] is False
            for r in result["physical_response"]
        ),
        "Quadrature error posture differs",
    )
    _close(
        result["receiver_radius_m"],
        math.sqrt(30000 / math.pi),
        "Declared conditional receiver radius",
    )
    moments = {}
    maximum_error = 0.0
    inverse = tuple(1 / (k * p) for k, p in zip(factors, ppe, strict=True))
    for row in result["windows"]:
        b = row["window_id"]
        cover, h, _ = _window(pooled[b], factors, ppe)
        counting = _count_matrix(pooled[b], inverse, cover)
        productivity = tuple(
            tuple(
                sum(
                    (a * v * s * s for a, v, s in zip(left, right, sd, strict=True)),
                    Fraction(),
                )
                for right in h
            )
            for left in h
        )
        total = tuple(
            tuple(counting[i][j] + productivity[i][j] for j in range(5))
            for i in range(5)
        )
        for field, expected in (
            ("cover", cover),
            ("ppe_gradient", h),
            ("counting_covariance", counting),
            ("ppe_covariance_diagonal", productivity),
            ("total_covariance_diagonal", total),
            (
                "standard_error_diagonal",
                tuple(math.sqrt(float(total[i][i])) for i in range(5)),
            ),
        ):
            maximum_error = max(
                maximum_error, _array_close(row[field], expected, field)
            )
        moments[b] = (cover, h, counting)
    # The off-diagonal time blocks are shared-PPE covariance, not zero and
    # not independent-window parameter variances. Count blocks are disjoint.
    joint = []
    for a in BINS:
        for i in range(5):
            line = []
            for b in BINS:
                for j in range(5):
                    covariance = sum(
                        (
                            x * y * s * s
                            for x, y, s in zip(
                                moments[a][1][i], moments[b][1][j], sd, strict=True
                            )
                        ),
                        Fraction(),
                    )
                    line.append(covariance + (moments[a][2][i][j] if a == b else 0))
            joint.append(line)
    maximum_error = max(
        maximum_error,
        _array_close(
            result["shared_diagonal_joint_covariance"],
            joint,
            "Shared temporal covariance",
        ),
    )
    identities = [(a, b, name) for a, b in combinations(BINS, 2) for name in AXIS]
    _require(
        [
            (r["younger_window_id"], r["older_window_id"], r["taxon"])
            for r in result["contrasts"]
        ]
        == identities,
        "Complete thirty-contrast identity/order differs",
    )
    zero_lower = 0
    minimum_positive_ppe = Decimal("Infinity")
    maximum_witness_gap = 0.0
    for row in result["contrasts"]:
        a, b, name = row["younger_window_id"], row["older_window_id"], row["taxon"]
        i = AXIS.index(name)
        rational_gradient = tuple(
            x - y for x, y in zip(moments[b][1][i], moments[a][1][i], strict=True)
        )
        maximum_error = max(
            maximum_error,
            _array_close(
                row["shared_ppe_gradient"], rational_gradient, "Temporal PPE gradient"
            ),
        )
        g = tuple(_fraction(v) for v in row["shared_ppe_gradient"])
        lengths = tuple(abs(v) * s for v, s in zip(g, sd, strict=True))
        lo, hi = _range(lengths)
        bound = (lo * lo, hi * hi)
        actual_bounds = row["ppe_variance_bounds"]
        _require(
            (actual_bounds["exact_lower"], actual_bounds["exact_upper"])
            == tuple(map(str, bound)),
            "Exact fixed-marginal variance bounds differ",
        )
        _require(
            (actual_bounds["lower"], actual_bounds["upper"])
            == tuple(map(float, bound)),
            "Rounded fixed-marginal bound displays differ",
        )
        zero_lower += lo == 0
        count = moments[a][2][i][i] + moments[b][2][i][i]
        diagonal = sum(
            (v * v * s * s for v, s in zip(rational_gradient, sd, strict=True)),
            Fraction(),
        )
        expected_scalar = {
            "cover_difference_older_minus_younger": moments[b][0][i] - moments[a][0][i],
            "count_variance": count,
            "ppe_variance_diagonal": diagonal,
            "total_variance_diagonal": count + diagonal,
            "upper_witness_total_contrast_variance": count + bound[1],
        }
        for field, scalar_expected in expected_scalar.items():
            maximum_error = max(
                maximum_error, _close(row[field], scalar_expected, field)
            )
        for side, v in zip(("lower", "upper"), bound, strict=True):
            maximum_error = max(
                maximum_error,
                _close(
                    row["total_variance_bounds"][side],
                    count + v,
                    "Total variance bound",
                ),
                _close(
                    row["standard_error_bounds"][side],
                    math.sqrt(float(count + v)),
                    "Standard error bound",
                ),
            )
        for upper in (False, True):
            matrix, scalar, margin = _witness(g, sd, upper=upper, ppe=ppe)
            _require(
                margin is not None and margin > 0,
                "Four-point moment witness is not strictly positive PPE",
            )
            assert margin is not None
            minimum_positive_ppe = min(minimum_positive_ppe, margin)
            _array_close(
                np.diag(matrix).tolist(),
                [s * s for s in sd],
                "Witness marginal variances",
            )
            scale = float(np.max(np.abs(matrix)))
            _require(
                np.linalg.eigvalsh(matrix / scale).min() >= -1e-12
                if scale
                else not np.any(matrix),
                "Gram witness is not PSD at declared floating tolerance",
            )
            with localcontext() as context:
                context.prec = 96
                _require(
                    abs(scalar - _decimal(bound[int(upper)]))
                    <= Decimal("1e-80") * max(Decimal(1), abs(scalar)),
                    "High-precision Gram resultant does not attain bound",
                )
            native_scalar = float(
                np.array(list(map(float, g))) @ matrix @ np.array(list(map(float, g)))
            )
            maximum_witness_gap = max(
                maximum_witness_gap,
                _close(native_scalar, bound[int(upper)], "Float Gram scalar"),
            )
            if upper:
                signed = tuple((-s if v < 0 else s) for v, s in zip(g, sd, strict=True))
                _array_close(
                    row["upper_witness_ppe_covariance"],
                    [[x * y for y in signed] for x in signed],
                    "Producer upper covariance witness",
                )
    _require(
        result["fixed_site_covariance_api_calls"] == 64
        and result["receiver_response_calls"] == 5
        and result["model_fits"] == result["chronology_draws_consumed"] == 0
        and result["historical_core_admission_changed"] is False
        and result["whole_vegetation_or_calibrated_coverage_claim"] is False,
        "Scientific computation scope differs",
    )
    return {
        "windows_checked": 4,
        "taxa_checked": 5,
        "contrasts_checked": 30,
        "joint_covariance_cells_checked": 400,
        "gram_extremal_witnesses": 60,
        "positive_four_point_moment_witnesses": 60,
        "zero_lower_variance_bounds": zero_lower,
        "minimum_positive_ppe_witness_support": str(minimum_positive_ppe),
        "maximum_scalar_or_covariance_error": maximum_error,
        "maximum_float_gram_variance_error": maximum_witness_gap,
        "absolute_tolerance": ATOL,
        "relative_tolerance": RTOL,
        "model_fits": 0,
        "scope": "Conditional fixed-source first-order scalar covariance-class extrema; saved transport factors held fixed, no inferred parameter law, simultaneous region, nonlinear variance bound or field calibration.",
    }
