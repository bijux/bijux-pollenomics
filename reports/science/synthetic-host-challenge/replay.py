"""Check the retained host challenge's count and vegetation arithmetic."""

from __future__ import annotations

import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
TAXA = ("broadleaf", "conifer", "open_land")


def main() -> None:
    report = json.loads((HERE / "report.json").read_text())
    if (
        report["status"] != "engineering_diagnostic_only"
        or tuple(report["taxa"]) != TAXA
    ):
        raise ValueError("Host challenge scope changed")
    count = report["counts"]
    pollen = report["input_pollen_fraction"]
    effort = report["counting_effort"]
    if (
        set(count) != set(TAXA)
        or set(pollen) != set(TAXA)
        or sum(count.values()) != effort
    ):
        raise ValueError("Host challenge pollen denominator changed")
    maximum = max(abs(count[taxon] / effort - pollen[taxon]) for taxon in TAXA)
    if not math.isclose(
        maximum,
        report["max_count_quantization_residual_fraction"],
        abs_tol=1e-15,
        rel_tol=0,
    ):
        raise ValueError("Count quantization residual differs")
    spatial = report["spatial_support"]
    if (
        spatial["host_basin_diameter_m"] != 2 * spatial["oracle_basin_radius_m"]
        or spatial["host_region_cutoff_m"] != spatial["oracle_extent_m"]
        or spatial["matching_kind"] != "declared_geometry_only"
    ):
        raise ValueError("Synthetic geometry declaration differs")
    truth = report["true_support_vegetation_fraction"]
    if set(truth) != set(TAXA) or not math.isclose(
        sum(truth.values()), 1.0, abs_tol=1e-12
    ):
        raise ValueError("Synthetic truth axis differs")
    for name in ("correct_parameters", "misspecified_ppe"):
        row = report[name]
        cover = row["estimated_cover_fraction"]
        residual = row["residual_fraction"]
        if set(cover) != set(TAXA) or set(residual) != set(TAXA):
            raise ValueError(f"{name}: taxon axis differs")
        if (
            row["status"] != "generated_exploratory"
            or row["reader_manifest_sha256"] != row["manifest_sha256"]
        ):
            raise ValueError(f"{name}: product-reader identity differs")
        for taxon in TAXA:
            if not math.isclose(
                cover[taxon] - truth[taxon], residual[taxon], abs_tol=1e-12
            ):
                raise ValueError(f"{name}: residual differs")
        measured_mae = sum(abs(residual[taxon]) for taxon in TAXA) / 3
        if not math.isclose(measured_mae, row["mae_fraction"], abs_tol=1e-12):
            raise ValueError(f"{name}: vegetation error differs")
        total = sum(cover.values())
        if (
            not math.isclose(total, row["cover_sum_fraction"], abs_tol=1e-12)
            or not math.isclose(
                abs(total - 1), row["closure_error_fraction"], abs_tol=1e-12
            )
            or row["closure_error_fraction"] > row["rounding_closure_bound_fraction"]
        ):
            raise ValueError(f"{name}: cover closure differs")
    difference = (
        report["misspecified_ppe"]["mae_fraction"]
        - report["correct_parameters"]["mae_fraction"]
    )
    if not math.isclose(
        difference, report["misspecified_minus_correct_mae_fraction"], abs_tol=1e-12
    ):
        raise ValueError("PPE comparison differs")
    if report["tampered_raw_evidence"] != {
        "reason_code": "evidence_digest_mismatch",
        "status": "refused",
    }:
        raise ValueError("Tamper refusal differs")
    print(
        "host challenge arithmetic verified: three taxa, two parameter requests, one refused tamper"
    )


if __name__ == "__main__":
    main()
