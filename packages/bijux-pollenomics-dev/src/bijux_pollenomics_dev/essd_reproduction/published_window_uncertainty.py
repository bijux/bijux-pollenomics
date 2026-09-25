"""Describe mean and reported-SE overlap for one authenticated ESSD window."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from .published_window_correspondence import ARCHIVE_SHA256, GRIDS, SOURCE_REVISION


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_envelopes(
    correspondence_csv: Path, provenance_report: Path
) -> tuple[list[dict[str, str]], dict[str, object]]:
    """Compare one-SE envelopes without treating them as confidence intervals."""
    source = json.loads(provenance_report.read_text())
    if (
        source.get("schema_version") != "landclimii-published-window-provenance.v2"
        or source.get("source_revision") != SOURCE_REVISION
        or source.get("published_archive_sha256") != ARCHIVE_SHA256
        or source.get("author_bin_bounds_bp") != [100, 350]
        or source.get("paired_mean_se_values") != 124
        or source.get("historical_raw_input_closure") != "not_established"
    ):
        raise ValueError("Provenance report is outside the exact published window")
    paired: dict[tuple[str, str], dict[str, dict[str, str]]] = {}
    with correspondence_csv.open(newline="") as stream:
        for row in csv.DictReader(stream):
            if (
                row["grid_id"] not in GRIDS
                or row["window"] != "100-350 BP"
                or row["unit"] != "percentage_cover"
                or row["metric"] not in {"mean", "standard_error"}
            ):
                raise ValueError("Correspondence row has an unsupported axis")
            metrics = paired.setdefault((row["grid_id"], row["taxon"]), {})
            if row["metric"] in metrics:
                raise ValueError("Duplicate grid/taxon/metric key")
            metrics[row["metric"]] = row
    if (
        len(paired) != 62
        or any(sum(grid == selected for grid, _ in paired) != 31 for selected in GRIDS)
        or any(
            set(metrics) != {"mean", "standard_error"} for metrics in paired.values()
        )
    ):
        raise ValueError("The two-grid, 31-taxon mean/SE axis does not close")

    rows: list[dict[str, str]] = []
    for (grid, taxon), metrics in sorted(paired.items()):
        mean, error = metrics["mean"], metrics["standard_error"]
        archive_mean, author_mean = Decimal(mean["archive"]), Decimal(mean["author_r"])
        archive_se, author_se = Decimal(error["archive"]), Decimal(error["author_r"])
        if (
            not all(
                value.is_finite()
                for value in (archive_mean, author_mean, archive_se, author_se)
            )
            or min(archive_se, author_se) < 0
        ):
            raise ValueError("Nonfinite value or negative reported standard error")
        gap = abs(author_mean - archive_mean)
        se_sum = archive_se + author_se
        separation = max(gap - se_sum, Decimal(0))
        rows.append(
            {
                "grid_id": grid,
                "taxon": taxon,
                "unit": "percentage_cover",
                "archive_mean": str(archive_mean),
                "archive_standard_error": str(archive_se),
                "author_r_mean": str(author_mean),
                "author_r_standard_error": str(author_se),
                "absolute_mean_gap_percentage_points": str(gap),
                "sum_standard_errors_percentage_points": str(se_sum),
                "one_se_envelopes_disjoint": str(gap > se_sum),
                "one_se_envelope_separation_percentage_points": str(separation),
            }
        )
    summaries = []
    for grid in GRIDS:
        subset = [row for row in rows if row["grid_id"] == grid]
        disjoint = [row for row in subset if row["one_se_envelopes_disjoint"] == "True"]
        largest = (
            max(
                disjoint,
                key=lambda row: Decimal(
                    row["one_se_envelope_separation_percentage_points"]
                ),
            )
            if disjoint
            else None
        )
        summaries.append(
            {
                "grid_id": grid,
                "taxa": len(subset),
                "disjoint_one_se_envelopes": len(disjoint),
                "overlapping_one_se_envelopes": len(subset) - len(disjoint),
                "largest_separation_taxon": largest["taxon"] if largest else "none",
                "largest_separation_percentage_points": (
                    largest["one_se_envelope_separation_percentage_points"]
                    if largest
                    else "0"
                ),
            }
        )
    return rows, {
        "schema_version": "landclimii-published-window-uncertainty-envelope.v1",
        "source_revision": SOURCE_REVISION,
        "published_archive_sha256": ARCHIVE_SHA256,
        "provenance_report_sha256": _digest(provenance_report),
        "correspondence_csv_sha256": _digest(correspondence_csv),
        "window": "100-350 BP",
        "envelope_definition": "mean plus or minus one reported standard error",
        "summaries": summaries,
        "historical_raw_input_closure": "not_established",
        "inferential_comparison": "not_evaluated",
        "measured_vegetation_accuracy": "not_evaluated",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--correspondence-csv", type=Path, required=True)
    parser.add_argument("--provenance-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows, report = compare_envelopes(args.correspondence_csv, args.provenance_report)
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "taxon-envelopes.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    summary = report["summaries"]
    assert isinstance(summary, list)
    lines = [
        "# ESSD published-window uncertainty envelopes",
        "",
        "The pinned 2016 author-R replay and PANGAEA 937075 June 2021 product "
        "are paired for 31 taxa in each of grids 512 and 562 at 100–350 BP. "
        "Each envelope is the reported mean ± one reported standard error, in "
        "percentage cover. Two envelopes are disjoint when the absolute mean "
        "gap exceeds the sum of their standard errors.",
        "",
        "| Grid | Disjoint / 31 taxa | Largest separation (percentage points) | Taxon |",
        "| --- | ---: | ---: | --- |",
    ]
    for item in summary:
        lines.append(
            f"| {item['grid_id']} | {item['disjoint_one_se_envelopes']} | "
            f"{Decimal(str(item['largest_separation_percentage_points'])):.6f} | "
            f"{item['largest_separation_taxon']} |"
        )
    lines.extend(
        [
            "",
            "This is a descriptive comparison of two reported uncertainty scales. "
            "Their cross-version dependence and historical raw-input identity are "
            "unknown, so envelope overlap is not a significance test. The result "
            "does not measure vegetation accuracy or reproduce the full study.",
        ]
    )
    (args.output / "REPORT.md").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
