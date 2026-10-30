"""Analytical BOKE three-taxon/BUS two-taxon conditional reconstruction."""

from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import json
import math
from pathlib import Path
import sys
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources,
)
from bijux_pollenomics_lra.models.errors import ValidationError

from ..physical_forward import inputs
from ..physical_forward.inputs import require
from . import cohort, counting

AXIS = ["Betula", "Fraxinus", "Ulmus"]
SWEDISH_REPORT = cohort.SWEDISH_REPORT
PROFILE = "boke-three-bus-two-conditional-measured-panels-v1"
LIMITS = [
    "New conditional reconstruction on declared measured panels: BOKE Betula/Fraxinus/Ulmus and BUS Betula/Ulmus. BUS Fraxinus remains unmeasured, not zero or predicted. Relative three-taxon cover is not whole vegetation.",
    "The BOKE multinomial factors into its conditional Betula/Ulmus likelihood and a Fraxinus-versus-panel-remainder binomial. The free Fraxinus coordinate saturates the latter at every Betula/Ulmus cover ratio. The profiled ratio and likelihood deviance therefore retain the original two-taxon result; the extra grains do not add cross-site confirmation of that ratio or Fraxinus.",
    "Both cores' exposed counts enter the original fit. These are descriptive in-sample likelihoods, not withheld prediction, ecological accuracy, a preferred field model, historical reproduction or chi-square p-values. Original sample exclusions, age windows, native count units, source rights and geometry limitations remain.",
    "Full-panel raw negative log likelihood omits multinomial combinatorial constants. Its mean uses the larger measured-grain denominator and must not be compared with the projected mean as an improvement. The fitted Fraxinus binomial contribution cancels in the corresponding saturated-model deviance.",
    "The model conditions on each declared measured panel. Recorded counts within a panel must follow that multinomial observation model; selective reporting or heterogeneous pooled samples are not validated by this calculation. BOKE alone identifies Fraxinus relative to the other two taxa.",
    "No three-taxon uncertainty interval is calculated. The earlier projected counting sets are not joint intervals for this composition. PPE, saved non-rigorous quadrature, geometry, chronology and common-field-cover assumptions remain fixed or unqualified; no fits, kernels or count-tail evaluations are added.",
]


def _domain(condition: object, message: str) -> None:
    if not condition:
        raise ValidationError(message, reason_code="measured_panel_domain")


def _positive(value: object) -> float:
    _domain(type(value) in (int, float), "Numerical response required")
    assert isinstance(value, (int, float))
    try:
        result = float(value)
    except OverflowError as error:
        raise ValidationError("Response is not representable") from error
    _domain(math.isfinite(result) and result > 0, "Finite positive response required")
    return result


def _nll(counts: list[int], probabilities: list[float]) -> float:
    _domain(
        len(counts) == len(probabilities)
        and all(math.isfinite(p) and 0 <= p <= 1 for p in probabilities)
        and math.isclose(math.fsum(probabilities), 1, rel_tol=0, abs_tol=1e-14),
        "Finite closed panel probabilities required",
    )
    _domain(
        all(n == 0 or p > 0 for n, p in zip(counts, probabilities, strict=True)),
        "Observed cell probability is zero",
    )
    return -math.fsum(
        n * math.log(p) for n, p in zip(counts, probabilities, strict=True) if n
    )


def complete_panel(
    group: dict[str, Any], responses: list[list[float]], fraxinus_response: float
) -> dict[str, Any]:
    """Profile the one BOKE-only coordinate; never fit or impute a BUS cell."""
    _domain(
        group.get("status") == "computed" and group["solver"].get("converged") is True,
        "A converged original point fit is required",
    )
    _domain(len(group["sites"]) == 2, "Exactly BOKE and BUS sites required")
    boke, bus = group["sites"]
    _domain(
        boke["core"] == "BOKE"
        and bus["core"] == "BUS"
        and boke["original_axis"] == AXIS
        and bus["original_axis"] == ["Betula", "Ulmus"]
        and boke["taxon_measured"] == bus["taxon_measured"] == [True, True]
        and all(type(v) is bool for s in (boke, bus) for v in s["taxon_measured"])
        and bus["Fraxinus_original_panel_count"] is None,
        "Exact measured BOKE3/BUS2 panels required",
    )
    nb, ns = boke["original_counts"], bus["original_counts"]
    _domain(
        type(nb) is list
        and type(ns) is list
        and len(nb) == 3
        and len(ns) == 2
        and all(type(n) is int and 0 <= n < 2**53 for n in [*nb, *ns]),
        "Exact nonnegative integer measured counts required",
    )
    nbu, nf = nb[0] + nb[2], nb[1]
    total = sum(nb) + sum(ns)
    _domain(nbu > 0 and total < 2**53, "Positive BOKE B/U effort required")
    _domain(
        boke["projected_counts"] == [nb[0], nb[2]]
        and bus["projected_counts"] == ns
        and boke["Fraxinus_original_panel_count"] == nf
        and boke["original_panel_N"] == sum(nb)
        and bus["original_panel_N"] == sum(ns)
        and boke["projected_panel_N"] == nbu
        and bus["projected_panel_N"] == sum(ns),
        "Original/projected panel count conservation failed",
    )
    _domain(
        type(responses) is list
        and len(responses) == 2
        and all(type(a) is list and len(a) == 2 for a in responses),
        "Response axes differ",
    )
    a = [[_positive(v) for v in row] for row in responses]
    af = _positive(fraxinus_response)
    fitted = group["common_cover_fit"]
    cover = fitted["cover"]
    _domain(
        type(cover) is list
        and len(cover) == 2
        and all(type(v) in (int, float) for v in cover),
        "Original numerical B/U cover required",
    )
    try:
        values = [float(v) for v in cover]
    except OverflowError as error:
        raise ValidationError("Original cover is not representable") from error
    _domain(
        all(math.isfinite(v) and 0 <= v <= 1 for v in values)
        and math.isclose(math.fsum(values), 1, rel_tol=0, abs_tol=1e-14),
        "Original closed B/U cover required",
    )
    r = Fraction.from_float(values[0])
    # Exact binary64 response inputs and integer counts avoid intermediate
    # overflow in the analytical nuisance-coordinate transformation.
    ab, au, f = map(Fraction.from_float, (*a[0], af))
    effective = ab * r + au * (1 - r)
    s = Fraction(nf, nbu) * effective / f
    completed = [float(v / (1 + s)) for v in (r, s, 1 - r)]
    _domain(
        all(
            value == 0 or rounded > 0
            for value, rounded in zip((r, s, 1 - r), completed, strict=True)
        ),
        "Positive completed cover is not representable",
    )
    probabilities = []
    for row in a:
        first = Fraction.from_float(row[0]) * r
        second = Fraction.from_float(row[1]) * (1 - r)
        probabilities.append(
            [float(first / (first + second)), float(second / (first + second))]
        )
    q = Fraction(nf, nbu + nf)
    # Evaluate the actual returned binary64 cover, preserving tiny rounding
    # residues in the factorization diagnostics instead of replacing them.
    returned = list(map(Fraction.from_float, completed))
    weights = [v * response for v, response in zip(returned, (ab, f, au), strict=True)]
    boke_p = [float(weight / sum(weights)) for weight in weights]
    bus_weights = [
        Fraction.from_float(a[1][0]) * returned[0],
        Fraction.from_float(a[1][1]) * returned[2],
    ]
    bus_p = [float(weight / sum(bus_weights)) for weight in bus_weights]
    projected_nll = _nll([nb[0], nb[2]], probabilities[0]) + (
        _nll(ns, probabilities[1]) if sum(ns) else 0.0
    )
    entropy = _nll([nf, nbu], [float(q), float(1 - q)])
    full_nll = _nll(nb, boke_p) + (_nll(ns, bus_p) if sum(ns) else 0.0)
    saturated = _nll(nb, [n / sum(nb) for n in nb]) + (
        _nll(ns, [n / sum(ns) for n in ns]) if sum(ns) else 0.0
    )
    deviance = 2 * (full_nll - saturated)
    residuals = {
        "full_minus_projected_and_binomial_nll": full_nll - (projected_nll + entropy),
        "projected_minus_original_nll": projected_nll
        - fitted["negative_log_likelihood_without_combinatorial_constant"],
        "full_minus_original_deviance": deviance - fitted["multinomial_deviance"],
    }
    _domain(
        abs(residuals["full_minus_projected_and_binomial_nll"]) <= 1e-9
        and abs(residuals["projected_minus_original_nll"]) <= 1e-9
        and abs(residuals["full_minus_original_deviance"]) <= 1e-8,
        "Analytical likelihood factorization differs from original fit",
    )
    return {
        "window_cal_bp": group["window_cal_bp"],
        "status": "computed",
        "sites": group["sites"],
        "profile": PROFILE,
        "common_relative_cover": completed,
        "original_B_over_B_plus_U_cover": float(r),
        "BOKE_predicted_measured_panel": boke_p,
        "BUS_predicted_measured_panel_on_common_axis": [
            bus_p[0],
            None,
            bus_p[1],
        ],
        "taxon_measured_on_common_axis": [[True, True, True], [True, False, True]],
        "full_measured_grains": total,
        "original_projected_grains": nbu + sum(ns),
        "retained_Fraxinus_grains": nf,
        "negative_log_likelihood_without_combinatorial_constant": full_nll,
        "mean_negative_log_likelihood_per_full_measured_grain": full_nll / total,
        "saturated_panel_negative_log_likelihood": saturated,
        "profiled_Fraxinus_binomial_negative_log_likelihood": entropy,
        "original_projected_negative_log_likelihood": fitted[
            "negative_log_likelihood_without_combinatorial_constant"
        ],
        "multinomial_deviance": deviance,
        "original_projected_deviance": fitted["multinomial_deviance"],
        "factorization_residuals": residuals,
    }


def read_response(repository: Path, point: dict[str, Any]) -> dict[str, Any]:
    """Reuse source-owned full-panel response admission for the point consumer."""
    return cohort.read_full_response(repository, point)


def _revision(repository: Path) -> str:
    dev = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev"
    modules = [
        (
            sys.modules[__name__],
            f"{dev}/essd_reproduction/common_cover/measured_panels.py",
        ),
        (counting, f"{dev}/essd_reproduction/common_cover/counting.py"),
        (cohort, f"{dev}/essd_reproduction/common_cover/cohort.py"),
        (inputs, f"{dev}/essd_reproduction/physical_forward/inputs.py"),
        (
            sources,
            f"{dev}/source_completion/pollen_reconstruction/swedish_static_basin/sources.py",
        ),
    ]
    for module, relative in modules:
        path = Path(module.__file__ or "")
        require(
            path.resolve(strict=True) == path == repository / relative,
            "Consumed module is outside canonical source",
        )
    paths = [relative for _, relative in modules]
    revision = counting._git(repository, "rev-parse", "HEAD").decode().strip()
    counting._git(repository, "ls-files", "--error-unmatch", "--", *paths)
    counting._git(repository, "diff", "--exit-code", revision, "--", *paths)
    return revision


def main() -> None:
    """Validate canonical sources and write the declared measured-panel account."""
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
    point, identity = counting.read_point_report(repository)
    counting.authenticate_inputs(repository, point)
    response = read_response(repository, point)
    rows = []
    for group in point["groups"]:
        try:
            rows.append(
                complete_panel(
                    group,
                    [c["response_PPE_times_K"] for c in point["cores"]],
                    response["response_PPE_times_K"][1],
                )
            )
        except ValidationError as error:
            rows.append(
                {
                    "window_cal_bp": group["window_cal_bp"],
                    "status": "refused",
                    "reason": error.reason_code,
                    "detail": str(error),
                }
            )
    for pin in point["scientific_inputs"]:
        path = Path(pin["path"])
        relative = (
            str(path.relative_to(repository)) if path.is_absolute() else str(path)
        )
        sources.read_bound(repository, relative, pin)
    _, final_identity = counting.read_point_report(repository)
    require(
        final_identity == identity and _revision(repository) == revision,
        "Consumed source changed during calculation",
    )
    result = {
        "schema_version": "boke-bus-conditional-measured-panels.v1",
        "source_commit": revision,
        "command": sys.orig_argv,
        "point_report": identity,
        "profile": PROFILE,
        "taxa": AXIS,
        "age_unit": point["age_unit"],
        "boke_original_response": response,
        "scientific_inputs": point["scientific_inputs"],
        "original_source_epochs": point["original_source_epochs"],
        "unmatched": point["unmatched"],
        "groups": rows,
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "new_optimizer_runs": 0,
        "reused_B_U_point_fits": sum(r["status"] == "computed" for r in rows),
        "analytic_profile_completions": sum(r["status"] == "computed" for r in rows),
        "new_kernel_evaluations": 0,
        "new_count_tail_evaluations": 0,
        "three_taxon_uncertainty_evaluated": False,
        "historical_reproduction_claimed": False,
        "common_field_cover_admitted": False,
        "raw_redistribution_authorized": False,
        "development_exposed": True,
        "factorization_absolute_tolerances": {"nll": 1e-9, "deviance": 1e-8},
        "limits": LIMITS,
        "original_point_limits": point["limits"],
    }
    raw = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= 1024**2, "Essential output exceeds one MiB")
    with output.open("xb") as stream:
        stream.write(raw)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
