"""Separate ledger correspondence from exact saved finite-Q certificates."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import numpy as np

from .independent_certificates import (
    check_record,
    check_total,
    matrix,
    principal_minors,
    rational,
)
from .independent_quadratic_forms import (
    AXIS,
    BINS,
    Array,
    compare_forms,
    quadratic_forms,
    scalar_axes,
)
from .independent_sources import PROTOCOL, parameters, read_inputs, read_ledger


def reference_values(reference: dict[str, Any]) -> list[dict[str, float]]:
    """Read the already qualified fixed age/count terms on their own axes."""
    source = reference["conditional_on_complete"]
    components = source["covariance_components"]
    result = [
        {
            "mean": source["mean"][i],
            "fixed_age_variance": components["age"][i][i],
            "fixed_count_variance": components["count"][i][i],
            "diagonal_ppe_variance": components["shared_ppe"][i][i],
        }
        for i in range(20)
    ]
    expected = [(a, b, name) for a, b in combinations(BINS, 2) for name in AXIS]
    if [
        (row["younger_window_id"], row["older_window_id"], row["taxon"])
        for row in source["contrasts"]
    ] != expected:
        raise ValueError("Qualified scalar contrast axes differ")
    result.extend(
        {
            "mean": row["mean_difference"],
            "fixed_age_variance": row["variance_components"]["age"],
            "fixed_count_variance": row["variance_components"]["count"],
            "diagonal_ppe_variance": row["variance_components"]["shared_ppe"],
        }
        for row in source["contrasts"]
    )
    return result


def check_search(
    record: dict[str, Any], q: Array, configuration: dict[str, Any]
) -> None:
    """Check the fixed search account without rerunning candidate optimization."""
    attempts = record["search_attempts"]
    zero = not q.any()
    if len(attempts) != (0 if zero else 8):
        raise ValueError("Fixed candidate-search population differs")
    for k, row in enumerate(attempts, 1):
        initial = [2 * math.pi * ((k * m) % 17) / 17 for m in (1, 3, 7)]
        if (
            row["start_id"] != k
            or row["initial_angles"] != initial
            or type(row["candidate_admitted"]) is not bool
        ):
            raise ValueError("Fixed deterministic angle starts differ")
        if "iterations" in row and not 0 <= row["iterations"] <= 200:
            raise ValueError("Candidate iteration bound differs")
        if row["candidate_admitted"] and (
            row["candidate_id"] != f"angle_{k}"
            or len(row["final_angles"]) != 3
            or not all(math.isfinite(v) for v in row["final_angles"])
        ):
            raise ValueError("Admitted candidate account differs")
    expected_candidates = (
        1 if zero else 9 + sum(row["candidate_admitted"] for row in attempts)
    )
    if record["candidate_count"] != expected_candidates:
        raise ValueError("Retained candidate count differs")
    if (
        record["dual_source"] not in ("gershgorin", "candidate_stationarity_padding")
        or not 1 <= record["padding_checks"] <= 14
        or record["padding_exponent"] not in (None, *configuration["padding_exponents"])
    ):
        raise ValueError("Fixed dual-padding/fallback account differs")


def check_scalars(
    result: dict[str, Any],
    expected: Array,
    reference: dict[str, Any],
    configuration: dict[str, Any],
) -> dict[str, Any]:
    """Check fifty scalar forms, endpoint certificates and saved summary counts."""
    rows = result["scalars"]
    if [row["scalar_id"] for row in rows] != scalar_axes():
        raise ValueError("Fifty scalar output/contrast identities differ")
    gap = compare_forms([row["Q"] for row in rows], expected)
    fixed = reference_values(reference)
    exact_checks = 0
    statuses: Counter[str] = Counter()
    endpoints: Counter[str] = Counter()
    displays: Counter[str] = Counter()
    attempts = 0
    maximum_diagonal_gap = 0.0
    maximum_normalized_gap = Fraction(0)
    for row, source in zip(rows, fixed, strict=True):
        if any(row[k] != v for k, v in source.items()):
            raise ValueError("Qualified fixed mean/age/count/diagonal term changed")
        if any(type(v) not in (int, float) for qrow in row["Q"] for v in qrow):
            raise ValueError("Saved Q must contain finite binary64 numeric values")
        q = tuple(tuple(rational(v) for v in qrow) for qrow in row["Q"])
        diagonal_gap = abs(
            float(np.trace(np.asarray(row["Q"], dtype=float)))
            - source["diagonal_ppe_variance"]
        )
        if diagonal_gap > 1e-12 or row["diagonal_correspondence_gap"] != diagonal_gap:
            raise ValueError("Qualified diagonal PPE baseline differs")
        maximum_diagonal_gap = max(maximum_diagonal_gap, diagonal_gap)
        trace = sum((q[i][i] for i in range(4)), Fraction(0))
        if row["status"] == "refused_covariance_form":
            symmetric = all(q[i][j] == q[j][i] for i in range(4) for j in range(4))
            if symmetric and (trace > 0 or not any(any(r) for r in q)):
                raise ValueError("Valid finite Q was refused without a domain reason")
            if any(
                row[k] is not None
                for k in ("minimum", "maximum", "total_variance_outer_interval")
            ):
                raise ValueError("Refused finite Q has invented certificates")
            display = row["standard_deviation_display"]
            if (
                display["status"] != "refused_covariance_form"
                or display["lower"] is not None
                or display["upper"] is not None
            ):
                raise ValueError("Refused finite Q has an invented SD display")
        else:
            q = matrix(row["Q"])
            q_minors = principal_minors(q)
            q_masks = {
                sum(1 << i for i in indices): value
                for indices, value in q_minors.items()
            }
            if [rational(v) for v in row["Q_principal_minors_exact"]] != [
                q_masks[i] for i in range(1, 16)
            ] or row["finite_Q_exact_psd"] is not all(
                value >= 0 for value in q_minors.values()
            ):
                raise ValueError("Saved finite-Q roundoff/PSD account differs")
            if rational(row["normalization_trace_exact"]) != trace:
                raise ValueError("Finite Q normalization trace differs")
            certificates = {
                name: check_record(q, row[name], name)
                for name in ("minimum", "maximum")
            }
            for name, checked in certificates.items():
                check_search(
                    row[name], np.asarray(row["Q"], dtype=float), configuration
                )
                endpoints[row[name]["status"]] += 1
                attempts += len(row[name]["search_attempts"])
                maximum_normalized_gap = max(
                    maximum_normalized_gap, checked["normalized_gap"]
                )
                exact_checks += 1
            if (
                certificates["minimum"]["outer"] > certificates["minimum"]["primal"]
                or certificates["minimum"]["primal"] > certificates["maximum"]["outer"]
                or certificates["minimum"]["outer"] > certificates["maximum"]["primal"]
            ):
                raise ValueError("Exact scalar extremal ordering differs")
            expected_status = (
                "tight_global_enclosure"
                if all(c["tight"] for c in certificates.values())
                else "certified_loose_enclosure"
            )
            if row["status"] != expected_status:
                raise ValueError("Combined scalar tight/loose status differs")
            check_total(certificates, row)
        statuses[row["status"]] += 1
        displays[row["standard_deviation_display"]["status"]] += 1
    expected_summary = {
        "scalar_count": 50,
        "component_count": 20,
        "contrast_count": 30,
        "status_counts": dict(statuses),
        "endpoint_status_counts": dict(endpoints),
        "sd_display_status_counts": dict(displays),
        "maximum_diagonal_correspondence_gap": maximum_diagonal_gap,
        "optimizer_attempts": attempts,
    }
    if result["summary"] != expected_summary:
        raise ValueError("Saved complete result summary differs")
    return {
        "scalars_checked": 50,
        "exact_endpoint_certificates_checked": exact_checks,
        "exact_principal_minors_checked": 15 * exact_checks,
        "maximum_independent_Q_absolute_gap": gap,
        "maximum_diagonal_correspondence_gap": maximum_diagonal_gap,
        "maximum_normalized_primal_dual_gap_exact": str(maximum_normalized_gap),
        "status_counts": dict(statuses),
        "sd_display_status_counts": dict(displays),
    }


def verify_result(repository: Path, result_path: Path) -> dict[str, Any]:
    """Verify the saved covariance-sensitivity result against its bound inputs."""
    inputs = read_inputs(repository)
    result_body = result_path.read_bytes()
    result = json.loads(result_body)
    protocol = inputs.protocol
    committed = subprocess.check_output(
        ["git", "-C", str(repository), "show", f"{result['source_commit']}:{PROTOCOL}"]
    )
    if (
        committed != (repository / PROTOCOL).read_bytes()
        or result["input_sha256"] != inputs.hashes
    ):
        raise ValueError("Producer source protocol/input identities differ")
    if (
        result["schema_version"] != "abborrtjarnen-age-ppe-dependence.v1"
        or result["status"] != "common_ppe_covariance_sensitivity"
    ):
        raise ValueError("Saved common-covariance schema/status differs")
    if result["native_population"] != {
        "rows": 32000,
        "complete": 31999,
        "undefined": 1,
        "samples": 107,
    }:
        raise ValueError("Saved common-covariance population differs")
    expected_parameters = [
        {
            "taxon": p["name"],
            "native_taxon_id": p["native_taxon_id"],
            "ppe": p["ppe"],
            "published_sd": p["published_sd"],
        }
        for p in inputs.reference["parameters"][:4]
    ]
    if result["parameter_axis"] != expected_parameters or result["fixed_parameter"] != {
        "taxon": "Poaceae",
        "native_taxon_id": 417,
        "ppe": 1.0,
        "published_sd": 0.0,
        "output_uncertainty_retained": True,
    }:
        raise ValueError("Free parameter/fixed reference axis differs")
    if (
        result["model_fits"] != 0
        or result["new_ppe_draws"] != 0
        or any(
            result[k] is not False
            for k in (
                "raw_count_or_age_inputs_read",
                "distribution_law_adopted",
                "field_calibration_or_coverage_claim",
                "one_covariance_attains_all_scalar_extrema",
            )
        )
    ):
        raise ValueError("Saved conditional scientific scope differs")
    if (
        result["precision_and_scope"] != protocol["precision_and_scope"]
        or result["rights_and_use"] != protocol["rights_and_use"]
        or any(
            result["environment"][k] != v for k, v in protocol["environment"].items()
        )
    ):
        raise ValueError("Saved precision/environment/use scope differs")
    if (
        not math.isfinite(result["elapsed_seconds"])
        or not 0 <= result["elapsed_seconds"] <= 180
        or len(result_body) > 10_000_000
    ):
        raise ValueError("Producer declared result resource bound differs")
    ppe, sd = parameters(inputs.reference)
    population = read_ledger(inputs.ledger, inputs.reference)
    expected = quadratic_forms(population.covers, ppe, sd)
    checked = check_scalars(result, expected, inputs.reference, protocol["search"])
    inputs.unchanged()
    if result_path.read_bytes() != result_body:
        raise ValueError("Saved result changed during verification")
    return {
        "status": "passed",
        "producer_source_commit": result["source_commit"],
        "result_sha256": hashlib.sha256(result_body).hexdigest(),
        "saved_rows_checked": population.rows,
        "conditional_complete_rows": len(population.covers),
        "chain_complete_counts": population.chains,
        **checked,
        "model_fits": 0,
        "new_raw_count_or_age_reads": False,
        "certificate_scope": "Exact rational enclosures of saved finite Q; numerical ledger-to-Q correspondence checked separately; no field coverage or simultaneous attained extrema.",
    }
