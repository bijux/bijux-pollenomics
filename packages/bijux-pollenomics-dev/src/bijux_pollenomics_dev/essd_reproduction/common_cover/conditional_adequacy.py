"""Exact conditional adequacy of fixed-response two-site count models.

For independent X_s~Bin(N_s,p_s), with odds(p_s)=a_sB/a_sU * v/(1-v),
conditioning on M=X_1+X_2 cancels v. On lo=max(0,M-N_2)..hi=min(N_1,M),
weights are choose(N_1,k)*choose(N_2,M-k)*omega**k, where
omega=a_1B*a_2U/(a_1U*a_2B). For exact supplied binary64 omega=P/Q,
the equivalent integer weights use P**(k-lo)*Q**(hi-k). The recurrence
streams these integers with checked exact division; no fitted parameter or
asymptotic reference distribution is involved. Both tails INCLUDE the observed
allocation. Their doubled smaller value, capped at one, is a conservative
two-sided p-value. Decisions use exact rationals, never rounded displays.

The independent homogeneous binomial assumption is stronger than the earlier
Bonferroni count-region assumptions and is NOT established for pooled native
samples. These exposed development comparisons do not validate field sampling,
common cover, chronology, geometry, PPE, source rights or vegetation accuracy.
Thirteen prespecified windows retain separate results and conservative
Bonferroni decisions; the latter needs no independence BETWEEN windows.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Context, Decimal
from fractions import Fraction
import io
from math import comb
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
from bijux_pollenomics_lra.models import validation
from bijux_pollenomics_lra.models.errors import ValidationError

from ..physical_forward import inputs
from . import cohort, count_admission

MAX_SITE_COUNT = 10_000
MAX_INTEGER_BITS = 1_000_000
WINDOW_COUNT = 13
ALPHA = Fraction(1, 20)
DISPLAY_DIGITS = 40
PROFILE = "two-site-fixed-response-inclusive-conditional-tails-v1"
CSV_FIELDS = (
    "window_younger_cal_bp",
    "window_older_cal_bp",
    "status",
    "reason",
    "boke_Betula",
    "boke_Ulmus",
    "boke_Fraxinus",
    "boke_original_panel_N",
    "bus_Betula",
    "bus_Ulmus",
    "bus_original_panel_N",
    "bus_Fraxinus_measured",
    "boke_sample_count",
    "bus_sample_count",
    "boke_response_Betula",
    "boke_response_Ulmus",
    "bus_response_Betula",
    "bus_response_Ulmus",
    "conditional_Betula_total",
    "boke_Betula_support_lower",
    "boke_Betula_support_upper",
    "fixed_response_odds_exact",
    "left_tail_lower",
    "left_tail_upper",
    "right_tail_lower",
    "right_tail_upper",
    "p_value_lower",
    "p_value_upper",
    "p_le_0_05",
    "p_le_0_05_div_13",
)


def _domain(
    condition: object, message: str, reason: str = "conditional_count_domain"
) -> None:
    if not condition:
        raise ValidationError(message, reason_code=reason)


@dataclass(frozen=True)
class ConditionalTest:
    """Exact probabilities; uninformative singleton outcomes are not evidence of fit."""

    status: str
    reason: str
    odds: Fraction
    support: tuple[int, int]
    total_betula: int
    left_tail: Fraction
    right_tail: Fraction
    p_value: Fraction


def conditional_test(
    counts: object, responses: object, *, taxon_measured: object
) -> ConditionalTest:
    """Test one declared pair without fitting or selecting positive effort.

    Zero effort at one site or a singleton conditional support is explicitly
    uninformative (p=1). Two empty sites refuse. Counts must be measured,
    finite nonnegative integers; positive responses are preserved as binary64.
    Fixed count/bit ceilings bound exact arithmetic before comb/pow allocation.
    """
    count_admission.require_unmasked(taxon_measured, "taxon_measured")
    mask = np.asarray(taxon_measured, dtype=object)
    _domain(
        mask.shape == (2, 2)
        and all(isinstance(x, (bool, np.bool_)) and bool(x) for x in mask.flat),
        "Every taxon at both sites must be explicitly measured",
    )
    n = count_admission.matrix(counts, "counts")
    a = count_admission.matrix(responses, "responses")
    _domain(n.shape == a.shape == (2, 2), "Exactly two sites and two taxa required")
    _domain(
        np.all(n >= 0) and np.all(n == np.floor(n)),
        "Integer nonnegative counts required",
    )
    _domain(np.all(a > 0), "Fixed responses must be positive")
    first, second = (tuple(int(x) for x in row) for row in n)
    n1, n2 = sum(first), sum(second)
    _domain(max(n1, n2) <= MAX_SITE_COUNT, "Site count exceeds fixed ceiling")
    _domain(
        n1 + n2 > 0, "Both sites have zero effort", "conditional_no_count_information"
    )
    b1, b2 = first[0], second[0]
    m = b1 + b2
    lo, hi = max(0, m - n2), min(n1, m)
    f = [[Fraction.from_float(float(x)) for x in row] for row in a]
    odds = f[0][0] * f[1][1] / (f[0][1] * f[1][0])
    p, q = odds.numerator, odds.denominator
    bits = (
        n1
        + n2
        + (hi - lo) * max(p.bit_length(), q.bit_length())
        + (hi - lo + 1).bit_length()
        + 1
    )
    _domain(
        bits <= MAX_INTEGER_BITS,
        "Exact conditional weight budget exceeded",
        "conditional_integer_budget",
    )
    weight = comb(n1, lo) * comb(n2, m - lo) * q ** (hi - lo)
    total = left = right = 0
    for k in range(lo, hi + 1):
        total += weight
        if k <= b1:
            left += weight
        if k >= b1:
            right += weight
        if k < hi:
            numerator = weight * (n1 - k) * (m - k) * p
            denominator = (k + 1) * (n2 - m + k + 1) * q
            weight, remainder = divmod(numerator, denominator)
            _domain(remainder == 0 and weight > 0, "Integer recurrence lost exactness")
    uninformative = n1 == 0 or n2 == 0 or lo == hi
    return ConditionalTest(
        "uninformative" if uninformative else "computed",
        "zero_effort_site"
        if n1 == 0 or n2 == 0
        else "singleton_conditional_support"
        if lo == hi
        else "",
        odds,
        (lo, hi),
        m,
        Fraction(left, total),
        Fraction(right, total),
        min(Fraction(1), Fraction(2 * min(left, right), total)),
    )


def decimal_bounds(value: Fraction) -> tuple[str, str]:
    """Outward decimal probabilities; tiny positive tails never become float zero."""
    _domain(0 <= value <= 1, "Probability outside [0,1]")
    result = []
    for rounding in (ROUND_FLOOR, ROUND_CEILING):
        context = Context(
            prec=DISPLAY_DIGITS, rounding=rounding, Emin=-10_000_000, Emax=10_000_000
        )
        display = context.divide(Decimal(value.numerator), Decimal(value.denominator))
        _domain(
            display.is_finite() and (value == 0 or display > 0),
            "Decimal probability range loss",
        )
        result.append(str(display))
    return result[0], result[1]


def _site_row(row: dict[str, Any], site: dict[str, Any]) -> None:
    core = site["core"]
    expected_axis = list(cohort.FULL_TAXA if core == "BOKE" else cohort.TAXA)
    _domain(
        core in cohort.CORES and site["original_axis"] == expected_axis,
        "Original measured axis differs",
    )
    original = site["original_counts"]
    common_mask = [True, True, True] if core == "BOKE" else [True, False, True]
    _domain(
        len(original) == len(expected_axis)
        and all(type(x) is int and x >= 0 for x in original)
        and site["original_taxon_measured"] == [True] * len(original)
        and all(type(x) is bool for x in site["original_taxon_measured"]),
        "Original measured count panel differs",
    )
    _domain(
        site["taxon_measured_on_common_axis"] == common_mask
        and all(type(x) is bool for x in site["taxon_measured_on_common_axis"]),
        "Original common-axis missingness differs",
    )
    projected = [original[expected_axis.index(taxon)] for taxon in cohort.TAXA]
    _domain(
        projected == site["projected_counts"]
        and sum(projected) == site["projected_panel_N"]
        and sum(original) == site["original_panel_N"],
        "Original count denominators differ",
    )
    prefix = core.lower()
    row.update(
        {
            f"{prefix}_{taxon}": value
            for taxon, value in zip(cohort.TAXA, projected, strict=True)
        }
    )
    row[f"{prefix}_original_panel_N"] = sum(original)
    row[f"{prefix}_sample_count"] = len(site["sample_ids"])
    if core == "BOKE":
        _domain(
            site["Fraxinus_original_panel_count"] == original[1],
            "Original Fraxinus count differs",
        )
        row["boke_Fraxinus"] = original[1]
    else:
        _domain(
            site["Fraxinus_original_panel_count"] is None, "BUS Fraxinus is unmeasured"
        )
        row["bus_Fraxinus_measured"] = False


def evaluate(loaded: dict[str, Any]) -> list[dict[str, Any]]:
    """Preserve fixed matched/unmatched windows and original full-panel selection."""
    response_rows = loaded["full_panel_responses"]
    _domain(
        [x["core"] for x in response_rows] == list(cohort.CORES)
        and [x["taxa"] for x in response_rows]
        == [list(cohort.FULL_TAXA), list(cohort.TAXA)],
        "Original full response axes differ",
    )
    responses = [
        [r["response_PPE_times_K"][r["taxa"].index(taxon)] for taxon in cohort.TAXA]
        for r in response_rows
    ]
    rows = []
    windows: set[tuple[int, int]] = set()
    for group in [*loaded["groups"], *loaded["unmatched"]]:
        window = group["window_cal_bp"]
        _domain(
            len(window) == 2
            and window[0] < window[1]
            and (window[0], window[1]) not in windows,
            "Unique ordered windows required",
        )
        windows.add((window[0], window[1]))
        row: dict[str, Any] = dict.fromkeys(CSV_FIELDS, "")
        row.update(window_younger_cal_bp=window[0], window_older_cal_bp=window[1])
        sites = group.get("sites", [group])
        for site in sites:
            _site_row(row, site)
        if "sites" not in group:
            _domain(
                len(sites) == 1 and sites[0]["core"] == "BUS",
                "Original unmatched BUS window required",
            )
            row.update(status="unmatched", reason="BOKE_window_unavailable")
        else:
            _domain(
                [s["core"] for s in sites] == list(cohort.CORES),
                "Exactly BOKE/BUS order required",
            )
            for core, response in zip(cohort.CORES, responses, strict=True):
                row.update(
                    {
                        f"{core.lower()}_response_{taxon}": value
                        for taxon, value in zip(cohort.TAXA, response, strict=True)
                    }
                )
            try:
                result = conditional_test(
                    [s["projected_counts"] for s in sites],
                    responses,
                    taxon_measured=[[True, True], [True, True]],
                )
                row.update(
                    status=result.status,
                    reason=result.reason,
                    conditional_Betula_total=result.total_betula,
                    boke_Betula_support_lower=result.support[0],
                    boke_Betula_support_upper=result.support[1],
                    fixed_response_odds_exact=str(result.odds),
                    p_le_0_05=result.p_value <= ALPHA,
                    p_le_0_05_div_13=result.p_value <= ALPHA / WINDOW_COUNT,
                )
                for name, probability in (
                    ("left_tail", result.left_tail),
                    ("right_tail", result.right_tail),
                    ("p_value", result.p_value),
                ):
                    row[f"{name}_lower"], row[f"{name}_upper"] = decimal_bounds(
                        probability
                    )
            except ValidationError as error:
                row.update(status="refused", reason=error.reason_code)
        rows.append(row)
    _domain(
        len(loaded["groups"]) == WINDOW_COUNT and len(loaded["unmatched"]) == 6,
        "Fixed thirteen matched/six unmatched windows required",
    )
    return rows


def _revision(repository: Path) -> str:
    """One Git source revision; no ordinary source-file hash inventory."""
    dev = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev"
    paths = []
    for module, suffix in (
        (
            sys.modules[__name__],
            "essd_reproduction/common_cover/conditional_adequacy.py",
        ),
        (cohort, "essd_reproduction/common_cover/cohort.py"),
        (count_admission, "essd_reproduction/common_cover/count_admission.py"),
        (inputs, "essd_reproduction/physical_forward/inputs.py"),
        (
            sources,
            "source_completion/pollen_reconstruction/swedish_static_basin/sources.py",
        ),
    ):
        relative = f"{dev}/{suffix}"
        path = Path(module.__file__ or "")
        _domain(
            path.resolve(strict=True) == path == repository / relative,
            "Canonical consumed source required",
        )
        paths.append(relative)
    relative = (
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/models/validation.py"
    )
    validation_path = Path(validation.__file__ or "")
    _domain(
        validation_path.resolve(strict=True)
        == validation_path
        == repository / relative,
        "Canonical validation source required",
    )
    paths.append(relative)
    relative = (
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
        "reconstruction/likelihood/multisite_likelihood.py"
    )
    owned_path = Path(count_admission.multisite_likelihood.__file__ or "")
    _domain(
        owned_path.resolve(strict=True) == owned_path == repository / relative,
        "Canonical common-cover admission source required",
    )
    paths.append(relative)

    def git(*args: str) -> bytes:
        return subprocess.check_output(
            ["git", "-C", str(repository), *args], timeout=30
        )

    revision = git("rev-parse", "HEAD").decode().strip()
    git("ls-files", "--error-unmatch", "--", *paths)
    git("diff", "--exit-code", revision, "--", *paths)
    return revision


def main() -> None:
    """Write the source-bound conditional adequacy table to an absent artifact path."""
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.absolute()
    _domain(
        repository.resolve(strict=True) == repository, "Physical repository required"
    )
    output = require_absent_artifact_output(repository, args.output)
    revision = _revision(repository)
    loaded = cohort.load_count_groups(repository)
    rows = evaluate(loaded)
    for pin in loaded["scientific_inputs"]:
        path = Path(pin["path"])
        relative = (
            str(path.relative_to(repository)) if path.is_absolute() else str(path)
        )
        sources.read_bound(repository, relative, pin)
    _domain(
        _revision(repository) == revision, "Consumed source changed during calculation"
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    raw = stream.getvalue().encode()
    _domain(len(raw) <= 128 * 1024, "Essential CSV exceeds 128 KiB")
    with output.open("xb") as handle:
        handle.write(raw)
    print(f"profile={PROFILE} source_commit={revision}")
    print(f"command={sys.orig_argv!r}")
    print(f"rows={len(rows)} new_fits=0 new_kernel_evaluations=0")
    raise SystemExit(1 if any(r["status"] == "refused" for r in rows) else 0)


if __name__ == "__main__":
    main()
