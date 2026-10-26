"""Run the bounded declared chronology and its actual frozen pollen consumer."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

import numpy as np

from bijux_pollenomics_dev.ci.atlas_media.process_execution import run_bounded_argv
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..depth_order import abborrtjarne_prediction_sensitivity as frozen
from .inputs import CURVE_SHA256, FULL_CURVE_SHA256, PROTOCOL, read_inputs
from .posterior import physical_ages, score_draws
from .sampler_accuracy import ACCURACY_PROTOCOL, account, prefix_checks, prepare_case


def _output_bytes(destination: Path) -> int:
    return sum(path.stat().st_size for path in destination.rglob("*") if path.is_file())


def _revision(repository: Path) -> str:
    revision = frozen._revision(repository)
    files = [
        PROTOCOL,
        ACCURACY_PROTOCOL,
        *[
            path.relative_to(repository)
            for path in Path(__file__).parent.iterdir()
            if path.suffix in {".py", ".R", ".cpp"}
        ],
    ]
    prefix = ["git", "-C", str(repository)]
    subprocess.run(
        [*prefix, "ls-files", "--error-unmatch", "--", *map(str, files)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*prefix, "diff", "--exit-code", revision, "--", *map(str, files)],
        check=True,
        capture_output=True,
    )
    return revision


def run(
    repository: Path,
    source_root: Path,
    library: Path,
    oracle_summary: Path,
    output: Path,
    *,
    sampler_accuracy: bool = False,
) -> dict[str, Any]:
    """Retain native rows, exact selection, independent ages and all score refusals."""
    revision = _revision(repository)
    destination = require_absent_artifact_output(repository, output)
    oracle = json.loads(oracle_summary.read_text())
    oracle_gap = oracle.get("maximum_native_corrected_helper_gap")
    if (
        oracle.get("passed") is not True
        or oracle.get("source_version") != "4.0.2"
        or oracle.get("model_fits") != 0
        or oracle.get("absolute_tolerance") != 1e-8
        or oracle.get("source_support_refusals") != 4
        or oracle.get("fixture_cases") != 6
        or oracle.get("comparison_rows") != 64
        or oracle.get("relative_tolerance") != 0
        or type(oracle_gap) not in (int, float)
        or not np.isfinite(oracle_gap)
        or not 0 <= oracle_gap <= 1e-8
    ):
        raise ValueError(
            "The independently qualified native likelihood oracle is required"
        )
    case = read_inputs(repository, source_root)
    qualification = None
    if sampler_accuracy:
        case, qualification = prepare_case(repository, library, case)
        baseline = (repository / qualification["original_directory"]).resolve()
        if destination.resolve().is_relative_to(baseline):
            raise ValueError(
                "Sampler accuracy output must not modify the old directory"
            )
    retained = case.protocol["execution"].get("requested_ssize_per_chain", 4000)
    curve = library / "rintcal/extdata/3Col_intcal20.14C"
    full_curve = library / "rintcal/extdata/intcal20.14c"
    if (
        hashlib.sha256(curve.read_bytes()).hexdigest() != CURVE_SHA256
        or hashlib.sha256(full_curve.read_bytes()).hexdigest() != FULL_CURVE_SHA256
    ):
        raise ValueError("Qualified IntCal20 curve bytes differ")
    destination.mkdir()
    runtime = destination / "runtime"
    runtime.mkdir()
    case_path = destination / "core-input.json"
    case_path.write_text(
        json.dumps(
            {
                "protocol": case.protocol,
                "controls": case.controls,
                "sample_ids": case.sample_ids,
                "depths": case.depths.tolist(),
                **(
                    {"sampler_accuracy": qualification, "repository": str(repository)}
                    if qualification is not None
                    else {}
                ),
            },
            indent=2,
        )
        + "\n"
    )
    environment = (
        f"R_LIBS_USER={library}",
        "R_LIBS_SITE=",
        "R_ENVIRON_USER=/dev/null",
        "R_PROFILE_USER=/dev/null",
        f"TMPDIR={runtime}",
        "OMP_NUM_THREADS=1",
        "OPENBLAS_NUM_THREADS=1",
        "VECLIB_MAXIMUM_THREADS=1",
    )
    command = (
        "/usr/bin/time",
        "-l",
        "/usr/bin/env",
        *environment,
        "Rscript",
        "--vanilla",
        str(Path(__file__).with_name("fit.R")),
        str(library),
        str(case_path),
        str(destination),
    )
    # The existing bounded executor uses temporary streams; keep those in this
    # run's owned artifact directory rather than a system temporary location.
    print(f"source_commit={revision} command={command!r}", flush=True)
    previous_tempdir = tempfile.tempdir
    try:
        tempfile.tempdir = str(runtime)
        completed = run_bounded_argv(
            command, cwd=destination, timeout_seconds=600, max_output_bytes=2 * 1024**2
        )
    finally:
        tempfile.tempdir = previous_tempdir
    (destination / "r-stdout.txt").write_bytes(completed.stdout)
    (destination / "r-stderr.txt").write_bytes(completed.stderr)
    result: dict[str, Any] = {
        "schema_version": "abborrtjarnen-bacon-physical-rate-result.v1",
        "source_commit": revision,
        "command": list(command),
        "exit_status": completed.returncode,
        "timed_out": completed.timed_out,
        "elapsed_seconds": completed.duration_seconds,
        "protocol": str(PROTOCOL),
        "input_sha256": case.protocol["source_inputs"],
        "controls": case.controls,
        "fit_identities": case.fit_identities,
        "native_oracle": str(oracle_summary),
        "scientific_status": "refused_native_execution",
        "requested_chain_seeds": case.protocol["execution"]["seeds"],
    }
    if qualification is not None:
        result.update(
            protocol=str(ACCURACY_PROTOCOL),
            original_model_protocol=str(PROTOCOL),
            sampler_accuracy_qualification=account(qualification),
            requested_draws=32000,
            conditional_sampler_diagnostics_passed=False,
            consumer_status="not_run_native_execution",
        )
    measured = re.search(rb"([0-9]+)\s+maximum resident set size", completed.stderr)
    result["measured_peak_rss_bytes"] = int(measured[1]) if measured else None
    if completed.returncode != 0 or completed.timed_out:
        partial_path = destination / "fit-summary.json"
        partial = (
            json.loads(partial_path.read_text()) if partial_path.is_file() else None
        )
        result["partial_fit_account"] = partial
        produced = (
            {row["seed"] for row in partial.get("chains", [])} if partial else set()
        )
        result["chain_accounting"] = [
            {
                "seed": seed,
                "status": "saved_states_and_ages_produced"
                if seed in produced
                else "active_incomplete_execution"
                if partial and partial.get("active_seed") == seed
                else "no_completed_or_active_chain_record",
            }
            for seed in case.protocol["execution"]["seeds"]
        ]
        (destination / "report.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    fit = json.loads((destination / "fit-summary.json").read_text())
    if [chain["seed"] for chain in fit["chains"]] != case.protocol["execution"][
        "seeds"
    ]:
        raise ValueError("Exact original two-seed complete chain axis differs")
    prepared = []
    chains = []
    all_scores = []
    for chain in fit["chains"]:
        native_path = Path(chain["native_output"])
        if not native_path.is_relative_to(destination):
            raise ValueError("Native model output escaped its owned run")
        raw = np.loadtxt(native_path)
        if (
            chain["sections"] != 51
            or (qualification is not None and chain.get("raw_rows") != 19501)
            or raw.shape != (retained + 3501, chain["sections"] + 3)
            or (
                chain["first_native_row"],
                chain["last_native_row"],
                chain["retained_rows"],
            )
            != (3502, retained + 3501, retained)
        ):
            raise ValueError("Native state population or frozen row selection differs")
        first, stop = chain["first_native_row"] - 1, chain["last_native_row"]
        states = raw[first:stop, :-1]
        with gzip.open(native_path.parents[1] / "ages.csv.gz", "rt") as stream:
            header = stream.readline().strip().split(",")
            ages = np.loadtxt(stream, delimiter=",")
        if header != list(case.sample_ids) or ages.shape != (retained, 107):
            raise ValueError("Joint chronology sample/iteration axes differ")
        if not np.all(np.isfinite(ages)) or np.any(np.diff(ages, axis=1) < 0):
            raise ValueError("Joint chronology ages are nonfinite or nonmonotone")
        independent = physical_ages(
            states, case.depths, chain["top_depth_cm"], chain["section_thickness_cm"]
        )
        residual = float(np.max(np.abs(independent - ages)))
        if residual > 1e-8:
            raise ValueError(
                "Independent physical-age integration exceeds frozen tolerance"
            )
        prepared.append((chain, ages, residual, first))
    diagnostics_pass = bool(
        fit["age_diagnostics"]["qualified"]
        and fit["free_parameter_diagnostics"]["qualified"]
    )
    if qualification is not None:
        checks = prefix_checks(repository, destination, qualification)
        prefixes_passed = all(row["matched"] for row in checks)
        peak = result["measured_peak_rss_bytes"]
        resource_pass = (
            peak is not None
            and peak <= 1_500_000_000
            and completed.duration_seconds <= 600
        )
        output_bytes = _output_bytes(destination)
        resource_pass = resource_pass and output_bytes <= 100_000_000
        qualified = prefixes_passed and diagnostics_pass and resource_pass
        result["sampler_accuracy_qualification"].update(
            prefix_checks=checks,
            prefixes_passed=prefixes_passed,
            diagnostics_pass=diagnostics_pass,
            qualified=qualified,
            score_interpretation_permitted=qualified,
        )
        result.update(
            fit=fit,
            conditional_sampler_diagnostics_passed=qualified,
            output_bytes_before_report=output_bytes,
        )
        if not qualified:
            result.update(
                scientific_status="refused_sampler_prefix"
                if not prefixes_passed
                else "refused_mcmc_diagnostics"
                if not diagnostics_pass
                else "refused_sampler_resources",
                consumer_status="not_run_prefix_qualification"
                if not prefixes_passed
                else "not_run_sampler_qualification",
                chains=[
                    {**chain, "independent_maximum_absolute_age_residual": residual}
                    for chain, _, residual, _ in prepared
                ],
                chain_accounting=[
                    {
                        "seed": chain["seed"],
                        "status": "saved_states_and_ages_produced_consumer_withheld",
                    }
                    for chain, _, _, _ in prepared
                ],
            )
            if _revision(repository) != revision:
                raise ValueError("Sampler accuracy source changed during execution")
            prepare_case(repository, library, read_inputs(repository, source_root))
            (destination / "report.json").write_text(
                json.dumps(result, indent=2, allow_nan=False) + "\n"
            )
            return result
        result["consumer_status"] = "computed_after_sampler_qualification"
    for chain, ages, residual, first in prepared:
        native_path = Path(chain["native_output"])
        scores, population, support = score_draws(
            ages, case.counts, case.predictions, frozen.BINS
        )
        score_path = native_path.parents[1] / "draw-scores.csv.gz"
        with gzip.open(score_path, "wt", newline="") as stream:
            writer = csv.writer(stream)
            fields = [
                field
                for bin_id in frozen.BINS
                for field in (
                    f"bin_{bin_id}_sample_count",
                    f"bin_{bin_id}_pooled_closed16_count",
                    f"bin_{bin_id}_status",
                )
            ]
            writer.writerow(["chain_seed", "native_row", *fields, *frozen.METHODS])
            for index, row in enumerate(scores):
                detail: list[int | str] = []
                for sample_count, mass in support[index]:
                    status = (
                        "scored"
                        if mass > 0
                        else "nonempty_zero_mass"
                        if sample_count > 0
                        else "empty"
                    )
                    detail.extend((int(sample_count), int(mass), status))
                writer.writerow(
                    [
                        chain["seed"],
                        index + first + 1,
                        *detail,
                        *[
                            float(value)
                            if np.isfinite(value)
                            else "refused_incomplete_bin"
                            for value in row
                        ],
                    ]
                )
        chains.append(
            {
                **chain,
                "population": population,
                "independent_maximum_absolute_age_residual": residual,
            }
        )
        all_scores.append(scores)
    combined = np.concatenate(all_scores)
    complete = np.all(np.isfinite(combined), axis=1)
    eligible = combined[complete]
    descriptive: dict[str, Any] = {}
    for i, method in enumerate(frozen.METHODS):
        descriptive[method] = {
            "complete_draws": len(eligible),
            "mean_mae": float(np.mean(eligible[:, i])) if len(eligible) else None,
            "quantiles_025_50_975": np.quantile(
                eligible[:, i], [0.025, 0.5, 0.975]
            ).tolist()
            if len(eligible)
            else None,
            "strict_lowest_score_fraction_of_all_requested_draws": float(
                np.sum(
                    np.all(
                        eligible[:, i, None] < np.delete(eligible, i, axis=1), axis=1
                    )
                )
            )
            / len(combined)
            if len(eligible)
            else 0.0,
        }
    result.update(
        scientific_status="conditional_model_diagnostics_passed"
        if diagnostics_pass
        else "refused_mcmc_diagnostics",
        conditional_sampler_diagnostics_passed=diagnostics_pass,
        fit=fit,
        chains=chains,
        requested_draws=len(combined),
        complete_four_bin_draws=int(complete.sum()),
        incomplete_draw_fraction=float(np.mean(~complete)),
        saved_ensemble_descriptors=descriptive,
        interpretation="Only ABBO target chronology varies. Scores and ranking frequencies concern saved quantized states, fixed exposed predictions/counts, and the explicitly declared conditional model; incomplete draws stay in the all-draw denominator. Failed diagnostics prohibit a qualified posterior interpretation.",
    )
    result["chain_accounting"] = [
        {"seed": chain["seed"], "status": "saved_states_ages_and_consumer_produced"}
        for chain in chains
    ]
    if (
        result["measured_peak_rss_bytes"] is None
        or result["measured_peak_rss_bytes"] > 1_500_000_000
    ):
        result.update(
            scientific_status="refused_memory_budget_or_missing_measurement",
            conditional_sampler_diagnostics_passed=False,
        )
    if (
        _revision(repository) != revision
        or hashlib.sha256(curve.read_bytes()).hexdigest() != CURVE_SHA256
        or hashlib.sha256(full_curve.read_bytes()).hexdigest() != FULL_CURVE_SHA256
    ):
        raise ValueError("Consumed source or curve changed during execution")
    read_inputs(repository, source_root)
    total_bytes = _output_bytes(destination)
    if total_bytes > (100_000_000 if qualification is not None else 30_000_000):
        result.update(
            scientific_status="refused_output_budget",
            conditional_sampler_diagnostics_passed=False,
        )
    if qualification is not None:
        prepare_case(repository, library, read_inputs(repository, source_root))
        if not result["conditional_sampler_diagnostics_passed"]:
            result["sampler_accuracy_qualification"].update(
                qualified=False, score_interpretation_permitted=False
            )
            result["consumer_status"] = "computed_then_refused_final_resources"
            result.pop("saved_ensemble_descriptors", None)
    result["output_bytes_before_report"] = total_bytes
    (destination / "report.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    return result


def main() -> int:
    """Execute one committed source profile through the owned foreground command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--oracle-summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--sampler-accuracy",
        action="store_true",
        help="Run only the separately frozen 16000-row-per-seed prefix qualification",
    )
    args = parser.parse_args()
    result = run(
        args.repository.absolute(),
        args.source_root,
        args.library.absolute(),
        args.oracle_summary,
        args.output.absolute(),
        sampler_accuracy=args.sampler_accuracy,
    )
    print(
        json.dumps(
            {
                "scientific_status": result["scientific_status"],
                "elapsed_seconds": result["elapsed_seconds"],
            }
        ),
        flush=True,
    )
    return 0 if result["exit_status"] == 0 and not result["timed_out"] else 1


if __name__ == "__main__":
    sys.exit(main())
