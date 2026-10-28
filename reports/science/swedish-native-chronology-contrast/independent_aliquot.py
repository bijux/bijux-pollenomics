"""Independent Decimal scalar oracle for a declared common-panel counting model."""

from __future__ import annotations

from decimal import Decimal, localcontext
import json
from pathlib import Path
from typing import Any

import numpy as np

JsonMap = dict[str, Any]


def require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError("Independent aliquot oracle: " + reason)


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def review(source: Path, protocol: JsonMap, actual: JsonMap) -> JsonMap:
    """Derive memberships and quotient derivatives without production helpers."""
    with localcontext() as context:
        context.prec = 50
        return _review(source, protocol, actual)


def _review(source: Path, protocol: JsonMap, actual: JsonMap) -> JsonMap:
    native = read(source / "native-results.json")
    original = read(source / "protocol.json")
    edges = original["age_window_edges_cal_bp"]
    p = list(map(decimal, native["ppe"]))
    cp = [decimal(x) ** 2 for x in native["ppe_SD"]]
    axis = ["Betula", "Poaceae"]
    primitives: dict[str, JsonMap] = {}
    expected: list[JsonMap] = []
    # This selection intentionally uses a linear interval scan, not maintained
    # selection/bisect helpers; source ages and count support are rechecked.
    for pair in protocol["fixed_domain"]["pairs"]:
        did, uid = pair["dataset_id"], pair["collection_unit_id"]
        samples = read(source / f"dataset-{did}-sample-eligibility.json")
        for cid in (pair["reference_chronology_id"], pair["alternative_chronology_id"]):
            bins: list[list[str]] = [[] for _ in range(25)]
            for s in samples:
                ages = [
                    a
                    for a in s["typed_calibrated_source_ages"]
                    if a["native_chronology_id"] == cid
                ]
                if len(ages) != 1:
                    continue
                age = ages[0]
                require(
                    age["source_age_type"] == "Calibrated radiocarbon years BP",
                    "age scale",
                )
                point = age["source_point_age"]
                require(
                    type(point) in (int, float) and np.isfinite(point), "nonfinite age"
                )
                windows = [i for i in range(25) if edges[i] <= point < edges[i + 1]]
                require(
                    age["window_index"] == (windows[0] if windows else None),
                    "native age/window",
                )
                if not windows or not all(
                    t in s["strict_unique_literal_parameter_counts"] for t in axis
                ):
                    continue
                n = [
                    s["strict_unique_literal_parameter_counts"][t]["count"]
                    for t in axis
                ]
                require(
                    all(type(x) is int and x >= 0 for x in n), "noninteger native count"
                )
                if sum(n) == 0:
                    continue
                oid = f"{uid}:{did}:{s['native_sample_id']}"
                datum = {
                    "counts": list(map(decimal, n)),
                    "analysis_unit": s["native_analysis_unit_id"],
                    "source_ages": s["typed_calibrated_source_ages"],
                    "reported_NISP": s["reported_pollen_NISP"],
                }
                require(
                    oid not in primitives or primitives[oid] == datum, "native alias"
                )
                primitives[oid] = datum
                bins[windows[0]].append(oid)
            profile = next(
                row
                for row in native["single_dataset_profiles"]
                if row["selected_source_profile"]["native_dataset_id"] == did
                and row["selected_source_profile"]["native_chronology_id"] == cid
            )
            saved = {
                row["window_index"]: row
                for row in profile["conditional_results"]
                if row["physical_profile"] == "metadata_radius_wind_3"
            }
            for w, members in enumerate(bins):
                if not members:
                    require(w not in saved, "empty window")
                    continue
                old = saved[w]
                k = list(map(decimal, old["deposition"][0]))
                require(
                    old["deposition"][0] == pair["deposition"], "factor/source geometry"
                )
                sums = [
                    sum((primitives[m]["counts"][j] for m in members), Decimal(0))
                    for j in range(2)
                ]
                inv = [1 / (k[j] * p[j]) for j in range(2)]
                weights = [sums[j] * inv[j] for j in range(2)]
                W = sum(weights)
                q = [x / W for x in weights]
                # Explicit quotient rule, independent of matrix I-q expression.
                J = [
                    [
                        ((inv[a] if a == j else Decimal(0)) * W - weights[a] * inv[j])
                        / (W * W)
                        for j in range(2)
                    ]
                    for a in range(2)
                ]
                H = [
                    [
                        (-(weights[a] / p[a]) if a == j else Decimal(0)) / W
                        + weights[a] * weights[j] / (p[j] * W * W)
                        for j in range(2)
                    ]
                    for a in range(2)
                ]
                expected.append(
                    {
                        "id": f"{did}:{cid}:{w}",
                        "members": frozenset(members),
                        "k": k,
                        "n": sums,
                        "q": q,
                        "J": J,
                        "H": H,
                        "old": old,
                    }
                )
    require(len(primitives) == 432 and len(expected) == 221, "native population")
    actual_observations = actual["observations"]
    require(
        len(actual_observations) == len(primitives)
        and len({x["observation_id"] for x in actual_observations}) == len(primitives),
        "primitive identity cardinality",
    )
    for row in actual_observations:
        e = primitives[row["observation_id"]]
        require(
            list(map(decimal, row["counts"])) == e["counts"]
            and row["native_analysis_unit_id"] == e["analysis_unit"]
            and row["source_ages"] == e["source_ages"]
            and row["reported_pollen_NISP"] == e["reported_NISP"],
            "primitive source binding",
        )
    require(len(actual["results"]) == 221, "result count")
    for a, e in zip(actual["results"], expected, strict=True):
        require(
            a["result_id"] == e["id"]
            and frozenset(a["observation_ids"]) == e["members"]
            and list(map(decimal, a["deposition"])) == e["k"],
            "result support",
        )
    metrics: dict[str, JsonMap] = {}

    def check(
        field: str, value: Any, expected_value: Decimal, matrix: bool = False
    ) -> None:
        error = abs(decimal(value) - expected_value)
        scale = max(abs(decimal(value)), abs(expected_value))
        if matrix:
            bound = decimal("1e-18") + decimal("5e-10") * scale
            if scale <= decimal("1e-14"):
                bound = min(bound, decimal("5e-18"))
            require(
                error <= bound and error <= decimal("2e-13"), field + " scalar residual"
            )
        else:
            bound = decimal("2e-13")
            require(error <= bound, field + " scalar residual")
        m = metrics.setdefault(
            field,
            {
                "scalars": 0,
                "max_absolute": 0.0,
                "max_relative_with_1e18_floor": 0.0,
                "max_error_to_bound": 0.0,
            },
        )
        m["scalars"] += 1
        m["max_absolute"] = max(m["max_absolute"], float(error))
        m["max_relative_with_1e18_floor"] = max(
            m["max_relative_with_1e18_floor"],
            float(error / max(scale, decimal("1e-18"))),
        )
        m["max_error_to_bound"] = max(m["max_error_to_bound"], float(error / bound))

    observation_positions = {
        x["observation_id"]: i for i, x in enumerate(actual_observations)
    }
    for i, e in enumerate(expected):
        for a in range(2):
            check("cover", actual["cover"][i * 2 + a], e["q"][a])
            check("saved_cover", e["old"]["conditional_panel_cover"][a], e["q"][a])
            for j in range(2):
                check(
                    "ppe_jacobian", actual["ppe_jacobian"][i * 2 + a][j], e["H"][a][j]
                )
            for oid, pos in observation_positions.items():
                for j in range(2):
                    check(
                        "count_jacobian",
                        actual["count_jacobian"][i * 2 + a][pos * 2 + j],
                        e["J"][a][j] if oid in e["members"] else Decimal(0),
                    )
    v = {
        key: row["counts"][0] * row["counts"][1] / sum(row["counts"])
        for key, row in primitives.items()
    }
    # Two measured axes give C_i=v_i[[1,-1],[-1,1]]. This is an
    # independently derived scalar factorization, not a production matrix call.
    oracle = {
        key: [[Decimal(0)] * 442 for _ in range(442)]
        for key in ("counting", "ppe", "total")
    }
    for i, e in enumerate(expected):
        for j, f in enumerate(expected):
            overlap = sum((v[s] for s in e["members"] & f["members"]), Decimal(0))
            for a in range(2):
                for b in range(2):
                    counting = (
                        overlap
                        * (e["J"][a][0] - e["J"][a][1])
                        * (f["J"][b][0] - f["J"][b][1])
                    )
                    ppe = sum(
                        (e["H"][a][t] * cp[t] * f["H"][b][t] for t in range(2)),
                        Decimal(0),
                    )
                    for name, value in (
                        ("counting", counting),
                        ("ppe", ppe),
                        ("total", counting + ppe),
                    ):
                        oracle[name][i * 2 + a][j * 2 + b] = value
                        check(
                            "joint_" + name,
                            actual["covariance"][name][i * 2 + a][j * 2 + b],
                            value,
                            True,
                        )
    positions = {e["id"]: i for i, e in enumerate(expected)}
    pairs = []
    for pair in protocol["fixed_domain"]["pairs"]:
        for w in range(25):
            ids = [
                f"{pair['dataset_id']}:{cid}:{w}"
                for cid in (
                    pair["reference_chronology_id"],
                    pair["alternative_chronology_id"],
                )
            ]
            if all(key in positions for key in ids):
                pairs.append(tuple(positions[key] for key in ids))
    require(
        [list(x) for x in pairs] == [list(x) for x in actual["contrast_pairs"]],
        "matched contrast support",
    )
    identical = 0
    for i, (ref, alt) in enumerate(pairs):
        if (
            expected[ref]["members"] == expected[alt]["members"]
            and expected[ref]["k"] == expected[alt]["k"]
        ):
            identical += 1
        for a in range(2):
            check(
                "contrast_cover",
                actual["contrast_cover"][i * 2 + a],
                expected[alt]["q"][a] - expected[ref]["q"][a],
            )
        for j, (ref2, alt2) in enumerate(pairs):
            for a in range(2):
                for b in range(2):
                    for name, matrix in oracle.items():
                        value = (
                            matrix[alt * 2 + a][alt2 * 2 + b]
                            - matrix[alt * 2 + a][ref2 * 2 + b]
                            - matrix[ref * 2 + a][alt2 * 2 + b]
                            + matrix[ref * 2 + a][ref2 * 2 + b]
                        )
                        check(
                            "contrast_" + name,
                            actual["contrast_covariance"][name][i * 2 + a][j * 2 + b],
                            value,
                            True,
                        )
    marginal = []
    max_reduction = 0.0
    for i, e in enumerate(expected):
        n = e["n"]
        N = sum(n)
        pooled_v = n[0] * n[1] / N
        within_v = sum((v[s] for s in e["members"]), Decimal(0))
        between = sum(
            (
                sum(primitives[s]["counts"])
                * (primitives[s]["counts"][0] / sum(primitives[s]["counts"]) - n[0] / N)
                ** 2
                for s in e["members"]
            ),
            Decimal(0),
        )
        require(
            abs(pooled_v - within_v - between) <= decimal("1e-40"),
            "weighted between composition identity",
        )
        require(between >= 0, "between composition PSD")
        old_count = []
        new_count = []
        old_ppe = []
        for a in range(2):
            derivative = e["J"][a][0] - e["J"][a][1]
            pooled = pooled_v * derivative**2
            new = within_v * derivative**2
            check(
                "saved_pooled_count_marginal",
                e["old"]["counting_covariance"][a][a],
                pooled,
                True,
            )
            check(
                "saved_ppe_marginal",
                e["old"]["shared_ppe_covariance"][a][a],
                oracle["ppe"][i * 2 + a][i * 2 + a],
                True,
            )
            require(
                new <= pooled + decimal("1e-40"),
                "new marginal exceeds pooled conditional variance",
            )
            old_count.append(float(pooled))
            new_count.append(float(new))
            old_ppe.append(float(oracle["ppe"][i * 2 + a][i * 2 + a]))
            max_reduction = max(max_reduction, float(pooled - new))
        marginal.append(
            {
                "result_id": e["id"],
                "old_pooled_count_variance": old_count,
                "new_aliquot_count_variance": new_count,
                "shared_ppe_variance": old_ppe,
                "between_aliquot_composition_coefficient": float(between),
            }
        )
    matrices = {
        key: np.asarray(value, dtype=float)
        for key, value in actual["covariance"].items()
    }
    contrast_matrices = {
        key: np.asarray(value, dtype=float)
        for key, value in actual["contrast_covariance"].items()
    }
    psd = {}
    for name, float_matrix in [
        *matrices.items(),
        *(("contrast_" + k, v) for k, v in contrast_matrices.items()),
    ]:
        scale = float(np.max(np.abs(float_matrix)))
        normalized = float_matrix / scale if scale else float_matrix
        symmetry = float(np.max(np.abs(normalized - normalized.T)))
        eigen = float(np.linalg.eigvalsh(normalized).min())
        require(symmetry <= 1e-12 and eigen >= -1e-10, "matrix symmetry/PSD")
        psd[name] = {
            "scale": scale,
            "max_normalized_asymmetry": symmetry,
            "minimum_normalized_eigenvalue": eigen,
        }
    naive_count_difference = 0.0
    naive_ppe_difference = 0.0
    identical_zero = 0
    for c, (a, b) in enumerate(pairs):
        naive_count = (
            matrices["counting"][a * 2, a * 2] + matrices["counting"][b * 2, b * 2]
        )
        naive_ppe = matrices["ppe"][a * 2, a * 2] + matrices["ppe"][b * 2, b * 2]
        naive_count_difference = max(
            naive_count_difference,
            abs(naive_count - contrast_matrices["counting"][c * 2, c * 2]),
        )
        naive_ppe_difference = max(
            naive_ppe_difference,
            abs(naive_ppe - contrast_matrices["ppe"][c * 2, c * 2]),
        )
        if (
            expected[a]["members"] == expected[b]["members"]
            and expected[a]["k"] == expected[b]["k"]
        ):
            require(
                abs(actual["contrast_cover"][c * 2]) <= 2e-13
                and abs(contrast_matrices["total"][c * 2, c * 2]) <= 1e-18,
                "identical support/response cancellation",
            )
            identical_zero += 1
    require(
        naive_count_difference > 1e-12 and naive_ppe_difference > 1e-12,
        "naive independence negative controls lack sensitivity",
    )
    zero_axis = sum(any(n == 0 for n in row["counts"]) for row in primitives.values())

    def zeros(matrix: np.ndarray) -> int:
        return int(np.count_nonzero(np.diag(matrix) == 0))

    return {
        "status": "passed",
        "precision": 50,
        "comparison_metrics": metrics,
        "matrix_checks": psd,
        "native_sources": 449,
        "selected_primitives": 432,
        "primitive_measured_zero_axis_samples": zero_axis,
        "primitive_degenerate_multinomial_covariances": sum(
            value == 0 for value in v.values()
        ),
        "occupied_results": 221,
        "paired_slots": 106,
        "missing_slots": 19,
        "identical_support_and_response_slots": identical,
        "qualified_zero_contrast_slots": identical_zero,
        "exact_zero_count_marginal_variances": zeros(matrices["counting"]),
        "exact_zero_total_marginal_variances": zeros(matrices["total"]),
        "exact_zero_count_contrast_variances": zeros(contrast_matrices["counting"]),
        "exact_zero_total_contrast_variances": zeros(contrast_matrices["total"]),
        "maximum_count_marginal_variance_reduction": max_reduction,
        "naive_independent_count_variance_max_departure": naive_count_difference,
        "naive_independent_PPE_variance_max_departure": naive_ppe_difference,
        "marginal_conditioning_changes": marginal,
        "interpretation": "Variance reduction follows conditioning on empirical per-aliquot proportions instead of pooled proportions, not improved accuracy. Taxon-zero aliquots can give degenerate plug-in counting covariance and understate finite-sample uncertainty. No interval coverage or chronology-distribution claim.",
    }
