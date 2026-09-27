"""Consume independent synthetic pollen through the public REVEALS workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import exp, pi, sqrt
from pathlib import Path
import platform
from typing import cast

import pandas as pd

from bijux_pollenomics_dev.lra_validation.known_landscape import (
    KnownLandscapeReport,
    build_known_landscape_report,
    build_transport_matched_report,
)
from bijux_pollenomics_lra.api import RevealsConfig, ValidationError, run_reveals

JsonObject = dict[str, object]
RECOVERY_TOLERANCE = 5e-6
DEPOSITION_TOLERANCE = 1e-12


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _mae(left: dict[str, float], right: dict[str, float]) -> float:
    return sum(abs(left[taxon] - right[taxon]) for taxon in left) / len(left)


def _gpm_factor(inner: float, outer: float, fall_speed: float) -> float:
    attenuation = 0.25 * 3.0 * sqrt(pi) * 0.12 / (4.0 * fall_speed)
    return exp(-(inner**0.125) / attenuation) - exp(-(outer**0.125) / attenuation)


def _consume(
    source: JsonObject,
    parameters: JsonObject,
    *,
    source_profile: str,
    source_sha256: str,
    control: str,
    transport_matched: bool,
) -> JsonObject:
    truth = cast(dict[str, float], source["true_support_vegetation_fraction"])
    pollen = dict(cast(dict[str, float], source["expected_pollen_fraction"]))
    taxa = list(truth)
    ppe = dict(cast(dict[str, float], parameters["ppe"]))
    fall_speed = dict(cast(dict[str, float], parameters["fall_speed_m_s"]))
    if control == "ppe_misspecification":
        ppe["broadleaf"] *= 0.8
    elif control == "taxon_label_shuffle":
        pollen = {
            taxon: pollen[taxa[(index + 1) % len(taxa)]]
            for index, taxon in enumerate(taxa)
        }

    diameter = (
        int(cast(int, source["basin_diameter_m"]))
        if transport_matched
        else int(2 * cast(float, source["basin_radius_m"]))
    )
    cutoff = float(
        cast(
            float,
            source["region_cutoff_m"]
            if transport_matched
            else source["declared_support_m"],
        )
    )
    factors = {
        taxon: _gpm_factor(diameter, cutoff, fall_speed[taxon]) for taxon in taxa
    }
    corrected = {taxon: pollen[taxon] / (ppe[taxon] * factors[taxon]) for taxon in taxa}
    total = sum(corrected.values())
    expected = {taxon: corrected[taxon] / total for taxon in taxa}
    config = RevealsConfig(
        "peatland",
        diameter,
        distance_weighting="gpm neutral",
        iterations=1,
        region_cutoff_m=cutoff,
        stochastic=False,
        retain_samples=True,
    )
    case: JsonObject = {
        "case_id": f"{source['case_id']}-{control}",
        "source_case_id": source["case_id"],
        "source_profile": source_profile,
        "source_report_sha256": source_sha256,
        "source_case_sha256": hashlib.sha256(_canonical(source)).hexdigest(),
        "source_case": source,
        "control": control,
        "transport_matched": transport_matched,
        "inverse_crime_control": transport_matched,
        "input_semantics": "noise_free_analytic_pollen_weights_not_observed_counts",
        "coordinate_semantics": "synthetic_row_key_not_chronology",
        "production_basin_assumption": "peatland",
        "config": config.as_dict(),
        "true_vegetation_fraction": truth,
        "input_pollen_fraction": pollen,
        "assumed_ppe": ppe,
        "assumed_fall_speed_m_s": fall_speed,
        "independent_expected_deposition": factors,
        "independent_expected_reconstruction_fraction": expected,
        "independent_expected_truth_mae_fraction": _mae(expected, truth),
        "interpretation": (
            "matched_method_calculation_control"
            if control == "matched_parameters"
            else "transport_and_support_mismatch_challenge"
            if not transport_matched
            else "negative_control_on_identical_synthetic_support"
        ),
    }
    table = pd.DataFrame(
        {"synthetic_index": [0.0], **{taxon: [pollen[taxon]] for taxon in taxa}}
    )
    parameter_table = pd.DataFrame(
        {
            "Taxon": taxa,
            "ppe": [ppe[taxon] for taxon in taxa],
            "ppe.error": [0.0] * len(taxa),
            "fallspeed": [fall_speed[taxon] for taxon in taxa],
        }
    )
    try:
        result = run_reveals(table, parameter_table, config)
    except ValidationError as error:
        case.update(status="refused", reason_code=error.reason_code, detail=str(error))
        return case
    assert result.samples is not None
    recovered = dict(zip(taxa, map(float, result.samples[0, 0] / 100), strict=True))
    deposition_error = max(
        abs(float(result.deposition[taxon]) - factors[taxon]) for taxon in taxa
    )
    calculation_error = max(abs(recovered[taxon] - expected[taxon]) for taxon in taxa)
    expected_truth_error = _mae(expected, truth)
    truth_error = _mae(recovered, truth)
    passed = (
        calculation_error <= RECOVERY_TOLERANCE
        and deposition_error <= DEPOSITION_TOLERANCE
    )
    if transport_matched and control == "matched_parameters":
        passed = passed and truth_error <= RECOVERY_TOLERANCE
    else:
        # A negative control must have a known nonzero effect before rounding.
        passed = passed and expected_truth_error > 2 * RECOVERY_TOLERANCE
    case.update(
        status="scored",
        contract_status="passed" if passed else "failed",
        reconstructed_vegetation_fraction=recovered,
        vegetation_mae_fraction=truth_error,
        calculation_max_abs_error_fraction=calculation_error,
        deposition_max_abs_error=deposition_error,
        production_manifest=result.manifest.scientific_identity(),
    )
    return case


def build_reconstruction_challenge() -> KnownLandscapeReport:
    """Run eight predeclared deterministic synthetic reconstructions.

    The generator is independent of production code. Matched GPM controls share
    its mathematical model; finite-cell challenges deliberately do not. Neither
    profile supplies real vegetation observations or held-out spatial accuracy.
    """
    matched = build_transport_matched_report()
    finite = build_known_landscape_report()
    cases: list[JsonObject] = []
    for report, matched_transport in ((matched, True), (finite, False)):
        payload = report.payload()
        sources = cast(list[JsonObject], payload["cases"])
        parameters = cast(JsonObject, payload["true_parameters"])
        for source in sources:
            if not matched_transport and source["case_id"] not in (
                "homogeneous-noise-free",
                "heterogeneous-noise-free",
            ):
                continue
            controls = (
                ("matched_parameters", "ppe_misspecification", "taxon_label_shuffle")
                if matched_transport
                else ("transport_mismatch",)
            )
            for control in controls:
                cases.append(
                    _consume(
                        source,
                        parameters,
                        source_profile=cast(str, payload["profile"]),
                        source_sha256=report.sha256,
                        control=control,
                        transport_matched=matched_transport,
                    )
                )
    scored = [case for case in cases if case["status"] == "scored"]
    payload = {
        "schema_version": "pollenomics-synthetic-reconstruction.v1",
        "profile": "independent-public-reveals-reconstruction-challenge",
        "python": platform.python_version(),
        "prospective_contract": {
            "requested_cases": 8,
            "production_reconstructions": 8,
            "iterations_per_reconstruction": 1,
            "stochastic": False,
            "recovery_tolerance_fraction": RECOVERY_TOLERANCE,
            "recovery_tolerance_basis": "half_unit_of_source_three_decimal_percent_rounding",
            "deposition_absolute_tolerance": DEPOSITION_TOLERANCE,
            "shuffle_rule": "cyclic_shift_pollen_taxon_values_once_keep_truth_and_parameters_fixed",
            "ppe_misspecification_rule": "broadleaf_nominal_ppe_times_0.8",
            "interval_calibration": "not_evaluated",
        },
        "cases": cases,
        "denominators": {
            "requested": 8,
            "attempted": len(cases),
            "predicted": len(scored),
            "scored": len(scored),
            "refused": len(cases) - len(scored),
            "contract_passed": sum(
                case["contract_status"] == "passed" for case in scored
            ),
            "contract_failed": sum(
                case["contract_status"] == "failed" for case in scored
            ),
        },
        "claims": {
            "truth_generator_imports_production_forward_or_inverse": False,
            "production_reconstruction_executed": True,
            "real_observations_used": False,
            "empirical_ecological_accuracy": False,
            "held_out_spatial_accuracy": False,
            "reviewed_ecological_thresholds": False,
            "synthetic_only": True,
        },
    }
    return KnownLandscapeReport(_canonical(payload))


def main() -> int:
    """Write the deterministic consumer result at an explicitly chosen path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = build_reconstruction_challenge()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report.payload(), indent=2, allow_nan=False) + "\n"
    )
    denominator = cast(dict[str, int], report.payload()["denominators"])
    print(
        json.dumps({"output": str(args.output), "sha256": report.sha256, **denominator})
    )
    return 0 if denominator["contract_passed"] == denominator["requested"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
