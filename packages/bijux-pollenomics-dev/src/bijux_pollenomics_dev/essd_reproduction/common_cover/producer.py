"""Conditional BOKE/BUS common-cover fits on an explicit Betula/Ulmus panel."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.likelihood import (
    multisite_likelihood as solver,
)

from ..physical_forward import inputs
from ..physical_forward.inputs import require
from . import cohort
from .cohort import TAXA, load_groups

Fit = Callable[..., solver.MultisiteLikelihoodFit]
LIMITS = [
    "New conditional reconstruction of relative Betula/Ulmus cover, not historical reproduction or whole vegetation. Original exact-panel matched groups remain zero; projection creates these new groups. Original full-panel sample eligibility/exclusions remain: projection never newly admits BOKE samples missing Fraxinus.",
    "Both sites' counts enter each fit. Likelihood and deviance are descriptive in-sample statistics, not independent prediction, vegetation accuracy, transfer validation or chi-square p-values.",
    "Two distinct physical places do not establish independent sampling or common cover. Thirteen windows repeatedly use the same two cores; pooled native samples are not proven homogeneous multinomial trials.",
    "Named calibrated BP point ages retain AD1950 as reference. Missing raw age bounds do not imply certainty. BUS chronology borrows dates from Agerods mosse and Krageholmssjon; no recalibration or chronology uncertainty is fitted.",
    "PPE and saved receiver-annulus K remain fixed. Static metadata disk radii, 3m/s wind, 100km extent and empirical metre-based diffusion coefficient are declared scenarios; no new kernel, geometry/PPE uncertainty or field applicability is established.",
    "Fraxinus_original_panel_count null means Fraxinus is outside the original saved parameter panel, not a measured zero. All reported native pollen mass and original panel mass are retained separately.",
    "Literal taxon/parameter names do not supply human-approved taxonomic equivalence. Historical metadata NR flags and local raw-source custody remain; no redistribution, permission, human review or release approval follows.",
    "Geometry-correct-then-pool means close(sum_site count/(PPE*K)), retaining grain effort. It is not the historical equal-place mean of independently closed inverse covers and does not reproduce prior held-out forward scores.",
    "Numerical stationarity/count-balance and relative-information checks are arithmetic policies, not uncertainty or certified cover-error bounds. Nonconverged candidates are withheld.",
]


def _statistics(counts: np.ndarray, predicted: np.ndarray) -> dict[str, Any]:
    require(
        counts.shape == predicted.shape
        and np.isfinite(predicted).all()
        and np.all(predicted >= 0)
        and np.allclose(predicted.sum(axis=1), 1, rtol=0, atol=1e-14),
        "Closed finite pollen probabilities required",
    )
    positive = counts > 0
    require(np.all(predicted[positive] > 0), "Observed cell probability is zero")
    total = float(counts.sum())
    fractions = counts / counts.sum(axis=1, keepdims=True)
    terms = counts[positive] * np.log(predicted[positive])
    saturated = counts[positive] * np.log(fractions[positive])
    nll = -math.fsum(map(float, terms))
    saturated_nll = -math.fsum(map(float, saturated))
    # Retain signed floating residue rather than clipping an apparent perfect fit.
    deviance = 2 * math.fsum(
        map(float, counts[positive] * np.log(fractions[positive] / predicted[positive]))
    )
    return {
        "predicted_pollen_fraction": predicted.tolist(),
        "negative_log_likelihood_without_combinatorial_constant": nll,
        "mean_negative_log_likelihood": nll / total,
        "saturated_site_negative_log_likelihood": saturated_nll,
        "multinomial_deviance": deviance,
    }


def compare_group(
    group: dict[str, Any],
    responses: list[list[float]],
    fit: Fit = solver.fit_multisite_likelihood,
) -> dict[str, Any]:
    """Use identical measured grain effort for both explicitly defined estimators."""
    counts = [s["projected_counts"] for s in group["sites"]]
    measured = [s["taxon_measured"] for s in group["sites"]]
    # The maintained solver owns strict count/measurement/response admission.
    result = fit(
        counts,
        responses,
        taxon_measured=measured,
        score_tolerance=1e-12,
        relative_count_tolerance=1e-10,
        max_steps=200,
    )
    n, a = np.asarray(counts, dtype=float), np.asarray(responses, dtype=float)
    corrected = np.sum(n / a, axis=0)
    baseline = corrected / corrected.sum()
    pollen = a * baseline
    pollen /= pollen.sum(axis=1, keepdims=True)
    diagnostics = {
        name: getattr(result, name)
        for name in (
            "profile",
            "converged",
            "steps",
            "stop_reason",
            "score_residual",
            "score_tolerance",
            "relative_count_residual",
            "relative_count_tolerance",
            "hessian_condition_number",
            "minimum_relative_information",
            "information_resolution_floor",
        )
    }
    # Nonfinite numerical diagnostics stay explicit without nonstandard JSON tokens.
    diagnostics = {
        k: (v if not isinstance(v, float) or math.isfinite(v) else str(v))
        for k, v in diagnostics.items()
    }
    output = {
        **group,
        "status": "computed" if result.converged else "nonconverged",
        "solver": diagnostics,
        "common_cover_fit": None,
        "geometry_correct_then_pool": {
            "cover": baseline.tolist(),
            **_statistics(n, pollen),
        },
        "baseline_minus_fitted_negative_log_likelihood": None,
    }
    if result.converged:
        fitted = {"cover": result.cover.tolist(), **_statistics(n, result.predicted)}
        require(
            math.isclose(
                fitted["mean_negative_log_likelihood"],
                result.mean_negative_log_likelihood,
                rel_tol=1e-13,
                abs_tol=1e-14,
            ),
            "Actual full likelihood objective differs",
        )
        output["common_cover_fit"] = fitted
        output["baseline_minus_fitted_negative_log_likelihood"] = (
            output["geometry_correct_then_pool"][
                "negative_log_likelihood_without_combinatorial_constant"
            ]
            - fitted["negative_log_likelihood_without_combinatorial_constant"]
        )
    return output


def evaluate(
    loaded: dict[str, Any], fit: Fit = solver.fit_multisite_likelihood
) -> list[dict[str, Any]]:
    responses = [c["response_PPE_times_K"] for c in loaded["cores"]]
    rows = []
    fatal = False
    for group in loaded["groups"]:
        row = {**group, "status": "not_run", "common_cover_fit": None}
        if not fatal:
            try:
                row = compare_group(group, responses, fit)
            except ValidationError as error:
                row.update(
                    status="refused", reason=error.reason_code, detail=str(error)
                )
            except Exception as error:
                fatal = True
                row.update(
                    status="fatal", reason=type(error).__name__, detail=str(error)
                )
        rows.append(row)
    return rows


def _revision(repository: Path) -> str:
    from bijux_pollenomics_lra.models import validation

    dev = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev"
    modules = [
        (sys.modules[__name__], f"{dev}/essd_reproduction/common_cover/producer.py"),
        (inputs, f"{dev}/essd_reproduction/physical_forward/inputs.py"),
        (cohort, f"{dev}/essd_reproduction/common_cover/cohort.py"),
        (
            sources,
            f"{dev}/source_completion/pollen_reconstruction/swedish_static_basin/sources.py",
        ),
        (
            solver,
            "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/likelihood/multisite_likelihood.py",
        ),
        (
            validation,
            "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/models/validation.py",
        ),
    ]
    for module, relative in modules:
        path = Path(module.__file__ or "")
        require(
            path.resolve(strict=True) == path == repository / relative,
            "Consumed scientific module is outside canonical source",
        )
    paths = [relative for _, relative in modules]
    command = ["git", "-C", str(repository)]
    revision = subprocess.check_output(
        [*command, "rev-parse", "HEAD"], text=True, timeout=30
    ).strip()
    for arguments in (
        ["ls-files", "--error-unmatch", "--", *paths],
        ["diff", "--exit-code", revision, "--", *paths],
    ):
        subprocess.run(
            [*command, *arguments], check=True, capture_output=True, timeout=30
        )
    return revision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.absolute()
    require(
        repository.resolve(strict=True) == repository,
        "Physical canonical repository required",
    )
    output = require_absent_artifact_output(repository, args.output)
    revision = _revision(repository)
    loaded = load_groups(repository)
    rows = evaluate(loaded)
    # Reauthenticate the actual raw and retained scientific inputs after calculation.
    for pin in loaded["scientific_inputs"]:
        path = Path(pin["path"])
        relative = (
            str(path.relative_to(repository)) if path.is_absolute() else str(path)
        )
        sources.read_bound(repository, relative, pin)
    require(
        _revision(repository) == revision, "Consumed source changed during execution"
    )
    result = {
        "schema_version": "boke-bus-conditional-multisite-likelihood.v1",
        "source_commit": revision,
        "command": sys.orig_argv,
        "taxa": list(TAXA),
        "age_unit": "calibrated years BP, AD1950 reference",
        "likelihood_effort": "Literal projected integer NISP per site; no equal-site weighting or pseudocounts",
        "baseline": "close(sum_site count_i/(PPE_i*K_site_i))",
        **{k: v for k, v in loaded.items() if k != "groups"},
        "groups": rows,
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "uncertainty_evaluated": False,
        "historical_reproduction_claimed": False,
        "common_field_cover_admitted": False,
        "raw_redistribution_authorized": False,
        "new_kernel_evaluations": 0,
        "limits": LIMITS,
    }
    raw = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= 1024**2, "Essential output exceeds one MiB")
    with output.open("xb") as stream:
        stream.write(raw)
    raise SystemExit(
        1
        if any(r["status"] in {"fatal", "not_run", "nonconverged"} for r in rows)
        else 0
    )


if __name__ == "__main__":
    main()
