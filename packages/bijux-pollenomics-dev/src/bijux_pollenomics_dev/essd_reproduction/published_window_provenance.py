"""Trace one published ESSD window through independent author R and installed LRA."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from statistics import median
from typing import cast

from .published_window_correspondence import BIN_ID, GRIDS, SOURCE_REVISION, WINDOW

SAME_RUN_TOLERANCE_PP = Decimal("1e-9")
METRICS = ("mean", "standard_error")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _author_r_values(
    path: Path, source_to_prepared: dict[str, str]
) -> dict[tuple[str, str, str], tuple[Decimal, Decimal]]:
    """Select only the regional author bin and convert fractions to percentage cover."""
    selected: dict[tuple[str, str, str], tuple[Decimal, Decimal]] = {}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["scope"] != "regional" or row["bin_id_bp"] != BIN_ID:
                continue
            if (
                row["source"] != "ESSD_LandClim_author_R_example"
                or row["grid_id"] not in GRIDS
                or row["site_id"]
                or row["taxon"] not in source_to_prepared
                or row["metric"] not in METRICS
                or row["unit"] != "fraction"
                or row["within_declared_tolerance"] != "True"
            ):
                raise ValueError("Selected author-R row has unsupported axes or parity")
            key = (
                row["grid_id"],
                source_to_prepared[row["taxon"]],
                row["metric"],
            )
            if key in selected:
                raise ValueError("Duplicate author-R regional key")
            selected[key] = (
                Decimal(row["author_reference"]) * 100,
                Decimal(row["installed_lra"]) * 100,
            )
    return selected


def _mean_vector_diagnostics(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Retain unnormalized mass and absolute gaps on the shared taxon axis."""
    diagnostics = []
    for grid in GRIDS:
        means = [
            row for row in rows if row["grid_id"] == grid and row["metric"] == "mean"
        ]
        if len(means) != 31 or len({row["taxon"] for row in means}) != 31:
            raise ValueError("Mean-vector taxon axis does not close")
        archive_sum = sum(Decimal(row["archive"]) for row in means)
        author_sum = sum(Decimal(row["author_r"]) for row in means)
        gaps = sorted(
            (
                (
                    row["taxon"],
                    abs(Decimal(row["author_r"]) - Decimal(row["archive"])),
                )
                for row in means
            ),
            key=lambda item: (-item[1], item[0]),
        )
        l1 = sum((gap for _, gap in gaps), Decimal(0))
        diagnostics.append(
            {
                "grid_id": grid,
                "taxa": str(len(means)),
                "archive_mean_sum_percentage_points": str(archive_sum),
                "author_r_mean_sum_percentage_points": str(author_sum),
                "author_r_minus_archive_sum_percentage_points": str(
                    author_sum - archive_sum
                ),
                "mean_l1_gap_percentage_points": str(l1),
                "largest_gap_taxon": gaps[0][0],
                "largest_gap_percentage_points": str(gaps[0][1]),
                "second_largest_gap_taxon": gaps[1][0],
                "second_largest_gap_percentage_points": str(gaps[1][1]),
                "two_largest_gap_share": str(
                    (gaps[0][1] + gaps[1][1]) / l1 if l1 else Decimal(0)
                ),
            }
        )
    return diagnostics


def compare_window(
    author_csv: Path,
    author_report: Path,
    published_csv: Path,
    published_report: Path,
    crosswalk_csv: Path,
) -> tuple[list[dict[str, str]], dict[str, object]]:
    """Pair the two computations and archive only on their exact shared axes."""
    author_meta = json.loads(author_report.read_text())
    published_meta = json.loads(published_report.read_text())
    if (
        author_meta["comparison"]
        != "installed_LRA_vs_independent_exact_author_R_replay"
        or not author_meta["passed"]
        or author_meta["unit"] != "fraction"
        or {row["grid_id"] for row in author_meta["grids"]} != set(GRIDS)
        or any(
            row["source_revision"] != SOURCE_REVISION for row in author_meta["grids"]
        )
        or published_meta["schema_version"]
        != "landclimii-published-window-correspondence.v1"
        or published_meta["source_revision"] != SOURCE_REVISION
        or published_meta["published_window"] != WINDOW
        or published_meta["author_bin_bounds_bp"] != [100, 350]
        or published_meta["historical_raw_input_closure"] != "not_established"
    ):
        raise ValueError("Prior correspondence reports do not share the declared scope")
    with crosswalk_csv.open(newline="") as stream:
        crosswalk = list(csv.DictReader(stream))
    source_to_prepared = {row["source"]: row["prepared"] for row in crosswalk}
    if (
        len(crosswalk) != 31
        or len(source_to_prepared) != 31
        or len(set(source_to_prepared.values())) != 31
    ):
        raise ValueError("Author taxon crosswalk does not close")
    author_values = _author_r_values(author_csv, source_to_prepared)
    rows: list[dict[str, str]] = []
    published_keys: set[tuple[str, str]] = set()
    with published_csv.open(newline="") as stream:
        for published in csv.DictReader(stream):
            grid, taxon = published["grid_id"], published["taxon"]
            key = (grid, taxon)
            if (
                grid not in GRIDS
                or taxon not in source_to_prepared.values()
                or published["window"] != WINDOW
                or published["author_bin_id_bp"] != BIN_ID
                or published["unit"] != "percentage_cover"
                or key in published_keys
            ):
                raise ValueError(
                    "Published-window row has unsupported or repeated axes"
                )
            published_keys.add(key)
            for metric, archive_column, installed_column in (
                ("mean", "published_mean", "recomputed_mean"),
                (
                    "standard_error",
                    "published_standard_error",
                    "recomputed_standard_error",
                ),
            ):
                if (grid, taxon, metric) not in author_values:
                    raise ValueError("Published taxon lacks author-R numerical support")
                author_r, installed_r_pair = author_values[(grid, taxon, metric)]
                archive = Decimal(published[archive_column])
                installed = Decimal(published[installed_column])
                if not all(
                    value.is_finite()
                    for value in (author_r, installed_r_pair, archive, installed)
                ):
                    raise ValueError("Published-window numerical value is non-finite")
                if abs(installed - installed_r_pair) > SAME_RUN_TOLERANCE_PP:
                    raise ValueError(
                        "Installed LRA values differ across prior receipts"
                    )
                rows.append(
                    {
                        "grid_id": grid,
                        "window": WINDOW,
                        "taxon": taxon,
                        "metric": metric,
                        "unit": "percentage_cover",
                        "archive": str(archive),
                        "author_r": str(author_r),
                        "installed_lra": str(installed),
                        "author_r_minus_archive": str(author_r - archive),
                        "installed_minus_archive": str(installed - archive),
                        "installed_minus_author_r": str(installed - author_r),
                    }
                )
    if len(published_keys) != 62 or len(rows) != 124 or len(author_values) != 124:
        raise ValueError("The two-grid mean/SE taxon axes do not close")
    mean_vectors = _mean_vector_diagnostics(rows)
    summaries = []
    for grid in GRIDS:
        for metric in METRICS:
            subset = [
                row
                for row in rows
                if row["grid_id"] == grid and row["metric"] == metric
            ]
            residuals = [abs(Decimal(row["author_r_minus_archive"])) for row in subset]
            parity = [abs(Decimal(row["installed_minus_author_r"])) for row in subset]
            if len(subset) != 31:
                raise ValueError("One grid/metric lacks its 31 taxon comparisons")
            largest = max(
                subset, key=lambda row: abs(Decimal(row["author_r_minus_archive"]))
            )
            summaries.append(
                {
                    "grid_id": grid,
                    "metric": metric,
                    "taxa": len(subset),
                    "max_absolute_author_r_minus_archive_pp": str(max(residuals)),
                    "median_absolute_author_r_minus_archive_pp": str(median(residuals)),
                    "max_absolute_installed_minus_author_r_pp": str(max(parity)),
                    "largest_archive_discrepancy_taxon": largest["taxon"],
                }
            )
    report: dict[str, object] = {
        "schema_version": "landclimii-published-window-provenance.v2",
        "source_revision": SOURCE_REVISION,
        "published_archive_sha256": published_meta["published_archive_sha256"],
        "author_bin_bounds_bp": [100, 350],
        "unit": "percentage_cover",
        "paired_taxon_keys": len(published_keys),
        "paired_mean_se_values": len(rows),
        "same_run_tolerance_percentage_points": str(SAME_RUN_TOLERANCE_PP),
        "input_sha256": {
            "author_csv": _digest(author_csv),
            "author_report": _digest(author_report),
            "published_csv": _digest(published_csv),
            "published_report": _digest(published_report),
            "crosswalk_csv": _digest(crosswalk_csv),
        },
        "summaries": summaries,
        "mean_vector_diagnostics": mean_vectors,
        "historical_raw_input_closure": "not_established",
        "measured_vegetation_accuracy": "not_evaluated",
    }
    return rows, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "author_csv",
        "author_report",
        "published_csv",
        "published_report",
        "crosswalk_csv",
        "output",
    ):
        parser.add_argument(f"--{name.replace('_', '-')}", type=Path, required=True)
    args = parser.parse_args()
    rows, report = compare_window(
        args.author_csv,
        args.author_report,
        args.published_csv,
        args.published_report,
        args.crosswalk_csv,
    )
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "paper-correspondence.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    summaries = cast(list[dict[str, str]], report["summaries"])
    mean_vectors = cast(list[dict[str, str]], report["mean_vector_diagnostics"])
    lines = [
        "# ESSD published-window numerical provenance",
        "",
        "The exact 100–350 BP author bin in grids 512 and 562 is paired across "
        "the independent author-R replay, installed LRA computation, and pinned "
        "PANGAEA 937075 published estimate. The 31 taxon mean and standard-error "
        "axes close in each grid (124 numerical values). Fractions from the "
        "author-R replay are multiplied by 100 before comparison with published "
        "percentage cover.",
        "",
        "| Grid | Metric | Maximum absolute R–archive gap (percentage points) | "
        "Median absolute gap | Maximum Python–R gap | Largest-gap taxon |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in summaries:
        lines.append(
            f"| {item['grid_id']} | {item['metric']} | "
            f"{Decimal(item['max_absolute_author_r_minus_archive_pp']):.6g} | "
            f"{Decimal(item['median_absolute_author_r_minus_archive_pp']):.6g} | "
            f"{Decimal(item['max_absolute_installed_minus_author_r_pp']):.6g} | "
            f"{item['largest_archive_discrepancy_taxon']} |"
        )
    lines.extend(
        [
            "",
            "The shared 31-taxon means are summed without renormalization. "
            "L1 is the sum of absolute percentage-point gaps across those taxa; "
            "it is a product correspondence diagnostic, not vegetation accuracy.",
            "",
            "| Grid | Archive mean sum (pp) | Author R mean sum (pp) | Mean L1 gap (pp) | Two largest-gap taxa | Share of L1 |",
            "| --- | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for item in mean_vectors:
        lines.append(
            f"| {item['grid_id']} | "
            f"{Decimal(item['archive_mean_sum_percentage_points']):.6f} | "
            f"{Decimal(item['author_r_mean_sum_percentage_points']):.6f} | "
            f"{Decimal(item['mean_l1_gap_percentage_points']):.6f} | "
            f"{item['largest_gap_taxon']}, {item['second_largest_gap_taxon']} | "
            f"{Decimal(item['two_largest_gap_share']):.3f} |"
        )
    lines.extend(
        [
            "",
            "On this author example, the archive difference also appears in the "
            "independent R replay; it is not a Python-only numerical discrepancy. "
            "The 2016 author-example and June 2021 archive historical raw-input "
            "cohorts are not closed as identical. This does not reproduce the "
            "1,128-row published study or evaluate measured vegetation accuracy.",
        ]
    )
    (args.output / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"values": len(rows), "summaries": summaries}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
