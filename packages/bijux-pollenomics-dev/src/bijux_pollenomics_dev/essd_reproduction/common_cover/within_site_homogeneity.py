"""Conditional within-site sample homogeneity on the original measured panels.

Under independent multinomial sample rows with ONE common pollen probability
vector, conditioning on row and column totals removes that vector. A table x
has mass proportional to 1/prod(x_ij!), not uniform mass among feasible tables.
Successive multivariate-hypergeometric rows have this law by telescoping the
remaining-count factorials. The final row is fixed by the remaining margins.

For N grains, row efforts r_i and taxon totals c_j, let D be the LCM of positive
r_i*c_j. Pearson's statistic is N*T/D-N, where T=sum x_ij**2*D/(r_i*c_j).
T is an exact integer: inclusive >= tail ordering has NO floating tolerance.
Zero margins remain in the source table but contribute no arithmetic term.
The plus-one Monte Carlo rank p=(1+b)/(1+B) includes ties and is conservative
under exchangeable null draws; it is NOT an enumerated conditional tail.
The separate Clopper-Pearson interval concerns simulation-tail uncertainty,
not field counts or joint confidence over the 32 prespecified windows.

The original admission/exclusions and exposed chronology windows stay fixed.
Independent grains/samples and a common within-window pollen probability are
model assumptions, not source facts. Nonrejection cannot establish them,
vegetation accuracy, chronology, geometry, rights or valid pooled uncertainty.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from fractions import Fraction
import io
from math import isfinite, lcm
from pathlib import Path
import subprocess
import sys
from time import monotonic
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
from bijux_pollenomics_lra.reconstruction.uncertainty import two_taxon_counting

from ..physical_forward import inputs
from . import cohort, count_admission

PROFILE = "native-sample-fixed-margin-pearson-monte-carlo-v1"
DRAWS = 9999
BASE_SEED = 846291731
FAMILY_SIZE = 32
MAX_ROWS = 128
MAX_CELL_COUNT = 10_000
MAX_TOTAL = 1_000_000
MAX_DENOMINATOR_BITS = 4096
MAX_DRAW_CELLS = 4_000_000
RUNTIME_SECONDS = 50
MC_CONFIDENCE = 0.99
CSV_FIELDS = (
    "core",
    "window_younger_cal_bp",
    "window_older_cal_bp",
    "matched_window",
    "taxa",
    "Fraxinus_measured",
    "sample_count",
    "positive_effort_samples",
    "positive_taxa",
    "selected_panel_N",
    "Betula",
    "Fraxinus",
    "Ulmus",
    "status",
    "reason",
    "pearson_exact",
    "draws_requested",
    "draws_completed",
    "extreme_count",
    "p_mc_exact",
    "p_le_0_05",
    "p_le_0_05_div_32",
    "mc_tail_confidence",
    "mc_tail_lower",
    "mc_tail_upper",
    "seed",
    "numpy_version",
)


def _require(
    condition: object, message: str, reason: str = "homogeneity_input"
) -> None:
    if not condition:
        raise ValidationError(message, reason_code=reason)


@dataclass(frozen=True)
class HomogeneityResult:
    """Retain the conditional statistic, simulation completion and tail uncertainty."""

    status: str
    reason: str
    statistic: Fraction
    draws_completed: int
    extreme_count: int | None
    p_value: Fraction | None
    mc_tail_interval: tuple[float, float] | None


def prepare(
    counts: Any,
) -> tuple[
    tuple[tuple[int, ...], ...],
    tuple[int, ...],
    tuple[int, ...],
    int,
    tuple[tuple[int, ...], ...],
]:
    """Admit exact measured counts and bound integer work before any sampling."""
    count_admission.require_unmasked(counts, "Counts")
    try:
        raw = np.asarray(counts, dtype=object)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValidationError("One rectangular count table required") from error
    _require(
        raw.ndim == 2 and 1 <= raw.shape[0] <= MAX_ROWS and raw.shape[1] in (2, 3),
        "A bounded two/three-taxon sample table is required",
    )
    for value in raw.flat:
        _require(
            not isinstance(value, (bool, np.bool_))
            and isinstance(value, (int, float, np.integer, np.floating)),
            "Counts must be numeric without flags or missing values",
        )
        _require(
            0 <= value <= MAX_CELL_COUNT and isfinite(value) and value == int(value),
            "Counts must be finite bounded nonnegative integers",
        )
    table = tuple(tuple(int(v) for v in row) for row in raw)
    rows = tuple(map(sum, table))
    columns = tuple(sum(row[j] for row in table) for j in range(raw.shape[1]))
    _require(
        sum(rows) <= MAX_TOTAL,
        "Conditional grain total exceeds resource limit",
        "homogeneity_resources",
    )
    denominator = lcm(*(r * c for r in rows for c in columns if r and c))
    _require(
        denominator.bit_length() <= MAX_DENOMINATOR_BITS,
        "Pearson denominator exceeds integer-work limit",
        "homogeneity_resources",
    )
    weights = tuple(
        tuple(denominator // (r * c) if r and c else 0 for c in columns) for r in rows
    )
    return table, rows, columns, denominator, weights


def integer_score(table: Any, weights: tuple[tuple[int, ...], ...]) -> int:
    """Return the fixed-margin integer score used to order Pearson statistics."""
    return sum(
        int(value) ** 2 * weight
        for row, coefficients in zip(table, weights, strict=True)
        for value, weight in zip(row, coefficients, strict=True)
    )


def draw_table(
    rows: tuple[int, ...], columns: tuple[int, ...], rng: np.random.Generator
) -> tuple[tuple[int, ...], ...]:
    """Sample the nonuniform fixed-margin law, retaining zero margins literally."""
    remaining = list(columns)
    sampled = []
    for effort in rows[:-1]:
        row = tuple(
            int(v)
            for v in rng.multivariate_hypergeometric(
                remaining, effort, method="marginals"
            )
        )
        sampled.append(row)
        remaining = [a - b for a, b in zip(remaining, row, strict=True)]
    sampled.append(tuple(remaining))
    return tuple(sampled)


def conditional_homogeneity(
    counts: Any, *, seed: int, draws: int = DRAWS, deadline: float | None = None
) -> HomogeneityResult:
    """One prespecified conditional Monte Carlo test with exact integer tie order."""
    _require(type(seed) is int and 0 <= seed < 2**64, "One uint64 seed required")
    _require(
        type(draws) is int and 1 <= draws <= DRAWS,
        "Draw count exceeds declared simulation budget",
        "homogeneity_resources",
    )
    table, rows, columns, denominator, weights = prepare(counts)
    observed = integer_score(table, weights)
    statistic = Fraction(sum(rows) * observed, denominator) - sum(rows)
    _require(
        draws * len(rows) * len(columns) <= MAX_DRAW_CELLS,
        "Draw-cell work exceeds resource limit",
        "homogeneity_resources",
    )
    reason = (
        "zero_total_effort"
        if not sum(rows)
        else "one_positive_sample"
        if sum(r > 0 for r in rows) < 2
        else "one_positive_taxon"
        if sum(c > 0 for c in columns) < 2
        else ""
    )
    if reason:
        return HomogeneityResult(
            "uninformative", reason, statistic, 0, None, Fraction(1), None
        )
    rng = np.random.Generator(np.random.PCG64(seed))
    extreme = 0
    for index in range(draws):
        if index % 128 == 0 and deadline is not None and monotonic() >= deadline:
            return HomogeneityResult(
                "refused",
                "homogeneity_runtime_budget",
                statistic,
                index,
                None,
                None,
                None,
            )
        extreme += integer_score(draw_table(rows, columns, rng), weights) >= observed
    try:
        interval = two_taxon_counting.fixed_two_taxon_counting_interval(
            [extreme, draws - extreme],
            [1.0, 1.0],
            [1.0, 1.0],
            taxon_measured=[True, True],
            confidence_level=MC_CONFIDENCE,
        ).pollen_probability_interval
    except ValidationError as error:
        return HomogeneityResult(
            "refused", error.reason_code, statistic, draws, extreme, None, None
        )
    if deadline is not None and monotonic() >= deadline:
        return HomogeneityResult(
            "refused",
            "homogeneity_runtime_budget",
            statistic,
            draws,
            extreme,
            None,
            None,
        )
    return HomogeneityResult(
        "computed",
        "",
        statistic,
        draws,
        extreme,
        Fraction(extreme + 1, draws + 1),
        interval,
    )


def sample_tables(
    loaded: dict[str, Any],
) -> list[tuple[dict[str, Any], list[list[int]]]]:
    """Reconcile all original windows/samples before computing any outcome."""
    sites = [site for group in loaded["groups"] for site in group["sites"]] + loaded[
        "unmatched"
    ]
    _require(
        len(loaded["groups"]) == 13
        and len(loaded["unmatched"]) == 6
        and len(sites) == FAMILY_SIZE,
        "Original 13 matched/six unmatched windows required",
    )
    _require(
        Counter(site["core"] for site in sites) == {"BOKE": 13, "BUS": 19},
        "Original site/window population differs",
    )
    samples = loaded["sample_panels"]
    _require(
        len(samples) == 110 and len({s["sample_id"] for s in samples}) == 110,
        "Original 110 unique sample identities required",
    )
    by_window: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for sample in samples:
        _require(
            type(sample["sample_id"]) is int and sample["source_unit"] == "NISP",
            "Native sample identity/unit differs",
        )
        by_window.setdefault((sample["core"], *sample["window_cal_bp"]), []).append(
            sample
        )
    output = []
    seen = set()
    for site in sorted(sites, key=lambda s: (s["core"], *s["window_cal_bp"])):
        key = (site["core"], *site["window_cal_bp"])
        _require(key not in seen, "Repeated native site/window")
        seen.add(key)
        axis = list(cohort.FULL_TAXA if site["core"] == "BOKE" else cohort.TAXA)
        members = by_window.get(key, [])
        _require(
            site["original_axis"] == axis
            and members
            and all(s["taxa"] == axis for s in members),
            "Original measured panel/sample group differs",
        )
        _require(
            [s["sample_id"] for s in members] == site["sample_ids"],
            "Native sample order/support differs",
        )
        counts = [s["counts"] for s in members]
        _, efforts, totals, _, _ = prepare(counts)
        _require(
            list(totals) == site["original_counts"]
            and sum(efforts) == site["original_panel_N"],
            "Sample-to-pooled count conservation failed",
        )
        output.append((site, counts))
    _require(set(by_window) == seen, "Unconsumed native samples remain")
    return output


def evaluate(
    loaded: dict[str, Any], *, draws: int = DRAWS, deadline: float | None = None
) -> list[dict[str, Any]]:
    """Retain every admitted sample table with its bounded conditional test outcome."""
    tables = sample_tables(loaded)
    _require(
        draws * sum(len(c) * len(c[0]) for _, c in tables) <= MAX_DRAW_CELLS,
        "Cohort draw-cell work exceeds resource limit",
        "homogeneity_resources",
    )
    matched = {tuple(g["window_cal_bp"]) for g in loaded["groups"]}
    output = []
    for index, (site, counts) in enumerate(tables):
        _, efforts, totals, _, _ = prepare(counts)
        axis = site["original_axis"]
        row: dict[str, Any] = dict.fromkeys(CSV_FIELDS, "")
        row.update(
            core=site["core"],
            window_younger_cal_bp=site["window_cal_bp"][0],
            window_older_cal_bp=site["window_cal_bp"][1],
            matched_window=tuple(site["window_cal_bp"]) in matched,
            taxa="|".join(axis),
            Fraxinus_measured="Fraxinus" in axis,
            sample_count=len(counts),
            positive_effort_samples=sum(n > 0 for n in efforts),
            positive_taxa=sum(n > 0 for n in totals),
            selected_panel_N=sum(efforts),
            seed=BASE_SEED + index,
            numpy_version=np.__version__,
            draws_requested=draws,
        )
        row.update(
            {
                name: totals[axis.index(name)] if name in axis else ""
                for name in cohort.FULL_TAXA
            }
        )
        try:
            result = conditional_homogeneity(
                counts, seed=BASE_SEED + index, draws=draws, deadline=deadline
            )
            row.update(
                status=result.status,
                reason=result.reason,
                pearson_exact=str(result.statistic),
                draws_completed=result.draws_completed,
                extreme_count=result.extreme_count
                if result.extreme_count is not None
                else "",
            )
            if result.p_value is not None:
                row.update(
                    p_mc_exact=str(result.p_value),
                    p_le_0_05=result.p_value <= Fraction(1, 20),
                    p_le_0_05_div_32=result.p_value <= Fraction(1, 20 * FAMILY_SIZE),
                )
            if result.mc_tail_interval is not None:
                row.update(
                    mc_tail_confidence=MC_CONFIDENCE,
                    mc_tail_lower=result.mc_tail_interval[0],
                    mc_tail_upper=result.mc_tail_interval[1],
                )
        except ValidationError as error:
            row.update(status="refused", reason=error.reason_code, draws_completed=0)
        output.append(row)
    return output


def _revision(repository: Path) -> str:
    """Bind consumed maintained source to one Git revision, not a hash inventory."""
    dev = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    lra = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
    paths = []
    for module, relative in (
        (
            sys.modules[__name__],
            dev + "essd_reproduction/common_cover/within_site_homogeneity.py",
        ),
        (cohort, dev + "essd_reproduction/common_cover/cohort.py"),
        (count_admission, dev + "essd_reproduction/common_cover/count_admission.py"),
        (
            count_admission.multisite_likelihood,
            "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
            "reconstruction/likelihood/multisite_likelihood.py",
        ),
        (inputs, dev + "essd_reproduction/physical_forward/inputs.py"),
        (
            sources,
            dev
            + "source_completion/pollen_reconstruction/swedish_static_basin/sources.py",
        ),
        (validation, lra + "models/validation.py"),
        (two_taxon_counting, lra + "reconstruction/uncertainty/two_taxon_counting.py"),
    ):
        path = Path(module.__file__ or "")
        _require(
            path.resolve(strict=True) == path == repository / relative,
            "Canonical consumed source required",
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
    """Write bounded within-site homogeneity outcomes with original source custody."""
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.absolute()
    _require(
        repository.resolve(strict=True) == repository, "Physical repository required"
    )
    output = require_absent_artifact_output(repository, args.output)
    revision = _revision(repository)
    deadline = monotonic() + RUNTIME_SECONDS
    loaded = cohort.load_sample_count_groups(repository)
    rows = evaluate(loaded, deadline=deadline)
    for pin in loaded["scientific_inputs"]:
        relative = Path(pin["path"])
        sources.read_bound(
            repository,
            str(relative.relative_to(repository))
            if relative.is_absolute()
            else str(relative),
            pin,
        )
    _require(
        _revision(repository) == revision, "Consumed source changed during calculation"
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    raw = stream.getvalue().encode()
    _require(len(raw) < 1024 * 1024, "Essential CSV exceeds one MiB")
    with output.open("xb") as handle:
        handle.write(raw)
    print(
        f"profile={PROFILE} source_commit={revision} numpy={np.__version__} RNG=PCG64 method=marginals"
    )
    print(f"command={sys.orig_argv!r}")
    print(
        f"rows={len(rows)} draws_per_informative_window={DRAWS} new_fits=0 new_kernels=0"
    )
    raise SystemExit(1 if any(r["status"] == "refused" for r in rows) else 0)


if __name__ == "__main__":
    main()
