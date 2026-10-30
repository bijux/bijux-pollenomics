"""Fixed-family bounds allowing arbitrary grain dependence inside each sample.

Condition on the original efforts and windows. For each measured taxon, sample
fractions X_i lie in [0,1]; sample vectors are assumed independent WITHIN each
window, with arbitrary and possibly different expectations. For w_i=N_i/N and
S=sum(w_i**2), the bounded-variable MGF inequality gives
E exp(t*sum(w_i*(X_i-E X_i))) <= exp(t*t*S/8).
Chernoff optimization therefore gives two-sided failure <=2 exp(-2*e**2/S).
With e**2 >= (9/2)*S and 77 fixed coordinates, the union bound is
154 exp(-9) < 1/20: sum(9**k/k!, k=0..8) > 3080 proves the strict inequality.
Neither taxon independence nor independence BETWEEN windows is needed.

The target is the effort-weighted expectation of sample fractions, not the
observed pooled fraction, vegetation cover or an assumed common probability.
Within-sample grains may be dependent; within-window SAMPLE independence is
still an unvalidated assumption. These bounds do not repair earlier pooled
intervals, establish field calibration or justify postselection claims.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from fractions import Fraction
import io
from math import isqrt
from pathlib import Path
import subprocess
import sys
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources,
)
from bijux_pollenomics_lra.models import validation
from bijux_pollenomics_lra.models.errors import ValidationError

from ..physical_forward import inputs
from . import cohort, count_admission, within_site_homogeneity

PROFILE = "native-sample-unit-bounded-mean-v1"
FAMILY_COORDINATES = 77
SQUARED_RADIUS_FACTOR = Fraction(9, 2)
RADIUS_GRID = 10**12
CSV_FIELDS = (
    "core",
    "window_younger_cal_bp",
    "window_older_cal_bp",
    "matched_window",
    "taxa",
    "Fraxinus_measured",
    "sample_count",
    "positive_effort_samples",
    "selected_panel_N",
    "status",
    "reason",
    "sum_squared_weights_exact",
    "radius_upper_exact",
    "full_coordinate_domain",
    *(
        f"{name}_{field}"
        for name in cohort.FULL_TAXA
        for field in (
            "count",
            "observed_fraction",
            "expected_fraction_lower",
            "expected_fraction_upper",
        )
    ),
)


@dataclass(frozen=True)
class SampleUnitBounds:
    """Retain exact effort weights, outward bounds and explicit sample refusals."""

    sample_count: int
    positive_effort_samples: int
    panel_total: int
    pooled_counts: tuple[int, ...]
    observed_fractions: tuple[Fraction, ...] | None
    sum_squared_weights: Fraction | None
    radius_upper: Fraction | None
    lower: tuple[Fraction, ...] | None
    upper: tuple[Fraction, ...] | None
    full_coordinate_domain: bool | None
    refusal: str | None


def sample_unit_bounds(counts: Any) -> SampleUnitBounds:
    """Reuse native count guards and construct outward bounds using only integers."""
    table, efforts, pooled, _, _ = within_site_homogeneity.prepare(counts)
    total = sum(efforts)
    positive = sum(effort > 0 for effort in efforts)
    if not total:
        return SampleUnitBounds(
            len(table),
            positive,
            0,
            pooled,
            None,
            None,
            None,
            None,
            None,
            None,
            "zero_full_panel_effort",
        )
    # Zero-effort rows remain present with zero weight; no 0/0 sample fraction
    # is formed. Pooled counts/N equals the weighted observed fraction exactly.
    observed = tuple(Fraction(count, total) for count in pooled)
    squared_weights = sum((Fraction(n, total) ** 2 for n in efforts), Fraction())
    squared_radius = SQUARED_RADIUS_FACTOR * squared_weights
    scaled = squared_radius * RADIUS_GRID**2
    ceiling = (scaled.numerator + scaled.denominator - 1) // scaled.denominator
    root = isqrt(ceiling)
    if root**2 < ceiling:
        root += 1
    radius = Fraction(root, RADIUS_GRID)
    if radius**2 < squared_radius:
        raise ValidationError(
            "Outward sample-unit radius failed", reason_code="sample_unit_radius"
        )
    lower = tuple(max(Fraction(), value - radius) for value in observed)
    upper = tuple(min(Fraction(1), value + radius) for value in observed)
    full = all(a == 0 and b == 1 for a, b in zip(lower, upper, strict=True))
    return SampleUnitBounds(
        len(table),
        positive,
        total,
        pooled,
        observed,
        squared_weights,
        radius,
        lower,
        upper,
        full,
        None,
    )


def evaluate(loaded: dict[str, Any]) -> list[dict[str, Any]]:
    """Preserve all original windows and the fixed 77-coordinate family."""
    tables = within_site_homogeneity.sample_tables(loaded)
    if (
        len(tables) != 32
        or sum(len(site["original_axis"]) for site, _ in tables) != FAMILY_COORDINATES
    ):
        raise ValidationError(
            "Original 32 windows/77 coordinates required",
            reason_code="sample_unit_family",
        )
    matched = {tuple(group["window_cal_bp"]) for group in loaded["groups"]}
    output = []
    for site, counts in tables:
        result = sample_unit_bounds(counts)
        axis = site["original_axis"]
        row: dict[str, Any] = dict.fromkeys(CSV_FIELDS, "")
        row.update(
            core=site["core"],
            window_younger_cal_bp=site["window_cal_bp"][0],
            window_older_cal_bp=site["window_cal_bp"][1],
            matched_window=tuple(site["window_cal_bp"]) in matched,
            taxa="|".join(axis),
            Fraxinus_measured="Fraxinus" in axis,
            sample_count=result.sample_count,
            positive_effort_samples=result.positive_effort_samples,
            selected_panel_N=result.panel_total,
            status="refused" if result.refusal else "computed",
            reason=result.refusal or "",
        )
        if result.observed_fractions is not None:
            row.update(
                sum_squared_weights_exact=str(result.sum_squared_weights),
                radius_upper_exact=str(result.radius_upper),
                full_coordinate_domain=result.full_coordinate_domain,
            )
        for index, name in enumerate(axis):
            row[f"{name}_count"] = result.pooled_counts[index]
            if result.observed_fractions is not None:
                assert result.lower is not None and result.upper is not None
                row[f"{name}_observed_fraction"] = str(result.observed_fractions[index])
                row[f"{name}_expected_fraction_lower"] = str(result.lower[index])
                row[f"{name}_expected_fraction_upper"] = str(result.upper[index])
        output.append(row)
    return output


def _revision(repository: Path) -> str:
    """Record actual consumed Git source, without a source-file hash registry."""
    dev = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    names = (
        (
            sys.modules[__name__],
            dev + "essd_reproduction/common_cover/sample_dependence_bounds.py",
        ),
        (cohort, dev + "essd_reproduction/common_cover/cohort.py"),
        (count_admission, dev + "essd_reproduction/common_cover/count_admission.py"),
        (
            count_admission.multisite_likelihood,
            "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
            "reconstruction/likelihood/multisite_likelihood.py",
        ),
        (
            within_site_homogeneity,
            dev + "essd_reproduction/common_cover/within_site_homogeneity.py",
        ),
        (inputs, dev + "essd_reproduction/physical_forward/inputs.py"),
        (
            sources,
            dev
            + "source_completion/pollen_reconstruction/swedish_static_basin/sources.py",
        ),
        (
            validation,
            "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/models/validation.py",
        ),
    )
    paths = []
    for module, relative in names:
        path = Path(module.__file__ or "")
        if path.resolve(strict=True) != path or path != repository / relative:
            raise ValidationError(
                "Canonical consumed source required", reason_code="sample_unit_source"
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
    """Write source-bound sample-unit precision limits to an absent artifact path."""
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.absolute()
    if repository.resolve(strict=True) != repository:
        raise ValidationError(
            "Physical repository required", reason_code="sample_unit_source"
        )
    output = require_absent_artifact_output(repository, args.output)
    revision = _revision(repository)
    loaded = cohort.load_sample_count_groups(repository)
    rows = evaluate(loaded)
    for pin in loaded["scientific_inputs"]:
        relative = Path(pin["path"])
        sources.read_bound(
            repository,
            str(relative.relative_to(repository))
            if relative.is_absolute()
            else str(relative),
            pin,
        )
    if _revision(repository) != revision:
        raise ValidationError(
            "Consumed source changed", reason_code="sample_unit_source"
        )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    raw = stream.getvalue().encode()
    if len(raw) >= 65536:
        raise ValidationError(
            "Sample-unit CSV exceeds 64KiB", reason_code="sample_unit_output"
        )
    with output.open("xb") as handle:
        handle.write(raw)
    print(
        f"profile={PROFILE} source_commit={revision} coordinates={FAMILY_COORDINATES} new_fits=0 new_kernels=0 simulations=0"
    )
    print(f"command={sys.orig_argv!r}")
    raise SystemExit(1 if any(row["status"] == "refused" for row in rows) else 0)


if __name__ == "__main__":
    main()
