"""Conditional joint covariance diagnostics for native LandClim II outputs."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
from typing import Any
import zipfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .. import pft_crosswalk as source
from .. import pft_uncertainty_bounds as marginal
from . import lengths

TOTAL = "declared_constant_total"
GROUPS = {**marginal.GROUPS, TOTAL: ("ET", "ST", "OL")}
MEAN_THRESHOLD = Fraction("0.000000001")
FIELDS = (
    "window",
    "LCGRID_ID",
    "lonDD",
    "latDD",
    "disposition",
    "reason",
    "constraint",
    "margin_side",
    "violation_magnitude_exact",
    "parent_se_literal",
    "child_se_literals",
    "lct_total_exact",
    "residual_to_one_exact",
    "residual_to_hundred_exact",
)


def _number(value: str) -> Fraction:
    if type(value) is not str or value != value.strip() or not value:
        raise ValueError("Literal finite native decimal required")
    # Decimal preserves the literal exponent/decimal spelling without binary
    # rounding. Missing/nonfinite values never become numerical zeros.
    try:
        native = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Literal finite native decimal required") from exc
    if not native.is_finite():
        raise ValueError("Literal finite native decimal required")
    return Fraction(native)


def analyse_window(
    window: int,
    header: list[str],
    means: list[dict[str, str]],
    errors: list[dict[str, str]],
    *,
    expected_rows: int = 420,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Retain all original grid rows and separate source from covariance refusals."""
    if (
        len(header) != 50
        or len(set(header)) != 50
        or header[:3] != ["LCGRID_ID", "lonDD", "latDD"]
        or header[-3:] != ["ET", "ST", "OL"]
        or set(header[34:47])
        != set(
            source.SOURCE_GROUPS["ET"]
            + source.OBSERVED_MEAN_GROUPS["ST"]
            + source.SOURCE_GROUPS["OL"]
        )
        or len(means) != expected_rows
        or len(errors) != expected_rows
    ):
        raise ValueError("Original mean/SE axes and grid denominator required")
    if any(set(row) != set(header) for row in [*means, *errors]):
        raise ValueError("Exact original mean/SE row fields required")
    by_id = {row["LCGRID_ID"]: row for row in errors}
    ids = [row["LCGRID_ID"] for row in means]
    if (
        len(by_id) != expected_rows
        or len(set(ids)) != expected_rows
        or set(ids) != set(by_id)
        or any(not name for name in ids)
    ):
        raise ValueError("Unique matched native mean/SE grid identities required")
    values = header[3:]
    involved = set(GROUPS) - {TOTAL}
    involved.update(child for children in GROUPS.values() for child in children)
    involved.discard(TOTAL)
    if not involved.issubset(values):
        raise ValueError(
            "The declared partial hierarchy lacks native variable coverage"
        )
    ungrouped = [name for name in header[3:34] if name not in involved]
    if len(ungrouped) != 22:
        raise ValueError(
            "The original 22 ungrouped taxon variables must remain explicit"
        )
    populations: Counter[str] = Counter()
    diagnostics = []
    minimum_margins: dict[str, dict[str, Fraction]] = {}
    root_residuals: dict[str, list[Fraction]] = {"one": [], "hundred": []}
    maximum_mean_identity = Fraction()
    for mean in means:
        error = by_id[mean["LCGRID_ID"]]
        if (
            set(mean) != set(header)
            or set(error) != set(header)
            or any(
                _number(mean[coordinate]) != _number(error[coordinate])
                for coordinate in ("lonDD", "latDD")
            )
        ):
            raise ValueError("Native grid coordinates or row fields differ")
        base: dict[str, Any] = dict.fromkeys(FIELDS, "")
        base.update(
            window=window, **{key: mean[key] for key in ("LCGRID_ID", "lonDD", "latDD")}
        )

        def refuse(disposition: str, reason: str, row: dict[str, Any] = base) -> None:
            populations[disposition] += 1
            diagnostics.append({**row, "disposition": disposition, "reason": reason})

        try:
            mu = {name: _number(mean[name]) for name in values}
            se = {name: _number(error[name]) for name in values}
        except (ValueError, ZeroDivisionError):
            refuse(
                "invalid_native_numeric",
                "Missing, nonfinite or nonnumeric native mean/SE; no value substituted",
            )
            continue
        if any(value < 0 for value in (*mu.values(), *se.values())):
            refuse("negative_native_value", "Negative native mean or SE; no clipping")
            continue
        total = sum((mu[name] for name in GROUPS[TOTAL]), Fraction())
        base.update(
            lct_total_exact=str(total),
            residual_to_one_exact=str(total - 1),
            residual_to_hundred_exact=str(total - 100),
        )
        for label, target in (("one", 1), ("hundred", 100)):
            root_residuals[label].append(total - target)
        if not any((*mu.values(), *se.values())):
            refuse(
                "native_all_zero",
                "All 47 mean and SE entries are literally zero; no-data-like row, not a closed estimated composition",
            )
            continue
        discrepancies = {
            parent: abs(mu[parent] - sum((mu[child] for child in children), Fraction()))
            for parent, children in marginal.GROUPS.items()
        }
        maximum_mean_identity = max(maximum_mean_identity, *discrepancies.values())
        if max(discrepancies.values()) > MEAN_THRESHOLD:
            refuse(
                "mean_identity_refused",
                "At least one declared partial mean-sum identity exceeds the existing mean threshold",
            )
            continue
        admitted_one, admitted_hundred = (
            abs(total - 1) <= MEAN_THRESHOLD,
            abs(total - 100) <= MEAN_THRESHOLD,
        )
        if not admitted_one and not admitted_hundred:
            refuse(
                "mean_total_refused",
                "Literal ET+ST+OL total agrees with neither 1 nor 100 at the existing mean threshold",
            )
            continue
        populations[
            "mean_total_near_one" if admitted_one else "mean_total_near_hundred"
        ] += 1
        intervals = {
            name: lengths.LengthInterval(value, value) for name, value in se.items()
        }
        intervals[TOTAL] = lengths.LengthInterval(Fraction(), Fraction())
        result = lengths.assess_laminar_uncertainty(intervals, GROUPS)
        if set(result.ungrouped_variables) != set(ungrouped):
            raise ValueError("An unverified source variable acquired a sum constraint")
        disposition = (
            "conditional_point_covariance_feasible"
            if result.feasible
            else "conditional_point_covariance_infeasible"
        )
        populations[disposition] += 1
        for node in result.nodes:
            if node.lower_overlap_margin is None or node.upper_overlap_margin is None:
                continue
            margins = {
                "lower": node.lower_overlap_margin,
                "upper": node.upper_overlap_margin,
            }
            previous = minimum_margins.setdefault(node.variable, margins)
            minimum_margins[node.variable] = {
                side: min(previous[side], margin) for side, margin in margins.items()
            }
            for side, margin in margins.items():
                if margin < 0:
                    diagnostics.append(
                        {
                            **base,
                            "disposition": disposition,
                            "reason": "Exact recorded SEs violate a declared necessary sum constraint; no rounding repair",
                            "constraint": node.variable,
                            "margin_side": side,
                            "violation_magnitude_exact": str(-margin),
                            "parent_se_literal": "0"
                            if node.variable == TOTAL
                            else error[node.variable],
                            "child_se_literals": json.dumps(
                                {child: error[child] for child in node.children or ()},
                                separators=(",", ":"),
                            ),
                        }
                    )
    partition = sum(
        count
        for name, count in populations.items()
        if not name.startswith("mean_total_near_")
    )
    if partition != expected_rows:
        raise AssertionError("Every source row must retain one terminal disposition")
    return {
        "window": window,
        "source_grid_rows": expected_rows,
        "populations": dict(populations),
        "ungrouped_taxon_variables": ungrouped,
        "minimum_exact_SE_constraint_margins": {
            name: {side: str(v) for side, v in margins.items()}
            for name, margins in minimum_margins.items()
        },
        "maximum_absolute_native_mean_identity_residual_exact": str(
            maximum_mean_identity
        ),
        "native_lct_total_residuals": {
            name: {
                "rows": len(residuals),
                "minimum_signed_exact": str(min(residuals)) if residuals else None,
                "maximum_signed_exact": str(max(residuals)) if residuals else None,
                "within_existing_mean_threshold": sum(
                    abs(v) <= MEAN_THRESHOLD for v in residuals
                ),
            }
            for name, residuals in root_residuals.items()
        },
    }, diagnostics


def _revision(repository: Path) -> str:
    paths = [Path(module.__file__ or "") for module in (source, marginal, lengths)] + [
        Path(__file__)
    ]
    if any(
        path.resolve(strict=True) != path
        or not path.is_relative_to(repository / "packages")
        for path in paths
    ):
        raise ValueError(
            "Scientific modules must load from the selected canonical repository"
        )
    command = ["git", "-C", str(repository)]
    revision = subprocess.check_output(
        [*command, "rev-parse", "HEAD"], text=True, timeout=30
    ).strip()
    relative = [str(path.relative_to(repository)) for path in paths]
    subprocess.run(
        [*command, "ls-files", "--error-unmatch", "--", *relative],
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        [*command, "diff", "--exit-code", revision, "--", *relative],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return revision


def build(repository: Path, output: Path) -> dict[str, Any]:
    """Read the existing shared archive and retain one summary and refusal CSV."""
    repository = repository.absolute()
    if repository.resolve(strict=True) != repository:
        raise ValueError("A physical canonical repository required")
    output = require_absent_artifact_output(repository, output)
    revision = _revision(repository)
    mapping, inputs = source._verified_sources(repository)
    source._source_mapping(mapping)
    windows, diagnostics = [], []
    header = None
    with zipfile.ZipFile(repository / source.ARCHIVE) as archive:
        members = source._members(archive)
        for window in range(1, 26):
            header, means = source._records(archive, members["mean"][window], header)
            _, errors = source._records(archive, members["se"][window], header)
            summary, negative = analyse_window(window, header, means, errors)
            windows.append(summary)
            diagnostics.extend(negative)
    populations: Counter[str] = Counter()
    for window_summary in windows:
        populations.update(window_summary["populations"])
    report = {
        "schema_version": "landclim-partial-joint-covariance.v1",
        "question": "Do exact archived PFT/LCT SEs admit one PSD covariance for the five declared partial sum identities plus a conditional constant ET+ST+OL total?",
        "source_git_revision": revision,
        "command": sys.orig_argv,
        "inputs": inputs,
        "source": "PANGAEA 937075, June 2021 native results; https://doi.pangaea.de/10.1594/PANGAEA.937075",
        "source_grid_window_rows": sum(row["source_grid_rows"] for row in windows),
        "populations": dict(populations),
        "groups": GROUPS,
        "ungrouped_taxon_variables": windows[0]["ungrouped_taxon_variables"],
        "windows": windows,
        "diagnostic_csv": "refusals.csv",
        "diagnostic_rows": len(diagnostics),
        "native_mean_comparison_threshold_exact": str(MEAN_THRESHOLD),
        "SE_decisions": "Literal source decimal SEs are exact point intervals. PSD feasibility uses exact rational arithmetic and no tolerance, clipping, rescaling or inferred rounding envelope.",
        "source_admission": "The primary deposit declares proportional closed estimates; native recorded values show percentage-like totals. Both literal residuals to 1 and 100 are retained. Existing 1e-9 mean comparisons qualify only a conditional recorded mean identity, not source units or original covariance production. All-zero native rows remain separate.",
        "limits": [
            "The partial tree contains 20 leaves and 5 measured groups plus the declared zero-uncertainty ET+ST+OL total; 22 other taxon uncertainties remain ungrouped. No complete 31-taxon/13-PFT covariance consistency is established.",
            "The constant-total sum is a conditional interpretation of the published closed estimand. Mean agreement does not authenticate shared draws, missing PFT-producing source or its historical delta-method implementation.",
            "A feasible partial PSD covariance is not a recovered covariance, calibrated uncertainty or a bounded random composition with the reported means. An exact point failure records its magnitude; unknown source rounding remains unknown.",
            "Only one common positive unit scale preserves the covariance predicate. No mixed-unit repair, biological ISTS reclassification, historical model rerun, source rights decision, field accuracy or human scientific approval follows.",
        ],
    }
    body = (json.dumps(report, indent=2, allow_nan=False) + "\n").encode()
    if len(body) > 1024**2 or len(diagnostics) > 63_000:
        raise ValueError("Bounded scientific summary or diagnostic population exceeded")
    if _revision(repository) != revision:
        raise ValueError("Consumed scientific source changed during execution")
    _, terminal_inputs = source._verified_sources(repository)
    if terminal_inputs != inputs:
        raise ValueError("Raw scientific inputs changed during execution")
    output.mkdir()
    (output / "report.json").write_bytes(body)
    with (output / "refusals.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(diagnostics)
    return report


def main(argv: list[str] | None = None) -> int:
    """Diagnose the fixed shared archive without regenerating historical results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    build(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
