"""Score the taxon percentages printed in Gaillard et al. (2010), Figure 6."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


SOURCE_SHA256 = "46bd92497d03169735b9a4665d71214c5dd8ff52ceddf39c577f0a4495fe73bd"
SOURCE_URL = "https://cp.copernicus.org/articles/6/483/2010/"

# Figure 6 labels are rounded whole percentages. Each row appears in all three
# panels for its region; unlabeled (<2%) taxa are deliberately outside the subset.
PUBLISHED_ROWS = (
    ("Skåne", "Picea", 3, 7, 13),
    ("Skåne", "Pinus", 13, 3, 3),
    ("Skåne", "Betula", 16, 2, 3),
    ("Skåne", "Poaceae", 15, 24, 19),
    ("Skåne", "Cerealia-t", 4, 32, 41),
    ("Småland", "Picea", 16, 54, 44),
    ("Småland", "Pinus", 42, 13, 19),
    ("Småland", "Betula", 24, 4, 6),
    ("Småland", "Poaceae", 5, 11, 18),
)


def produce(source_pdf: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    if hashlib.sha256(source_pdf.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("published figure source changed")
    rows: list[dict[str, object]] = []
    for region, taxon, pollen, reveals, observed in PUBLISHED_ROWS:
        rows.append(
            {
                "region": region,
                "taxon": taxon,
                "pollen_percent": pollen,
                "reveals_percent": reveals,
                "observed_vegetation_percent": observed,
                "pollen_absolute_error_pp": abs(pollen - observed),
                "reveals_absolute_error_pp": abs(reveals - observed),
            }
        )
    subsets = []
    for region in ("Skåne", "Småland"):
        selected = [row for row in rows if row["region"] == region]
        count = len(selected)
        subsets.append(
            {
                "region": region,
                "matched_named_taxa": count,
                "pollen_mean_absolute_error_pp": sum(
                    int(row["pollen_absolute_error_pp"]) for row in selected
                )
                / count,
                "reveals_mean_absolute_error_pp": sum(
                    int(row["reveals_absolute_error_pp"]) for row in selected
                )
                / count,
            }
        )
    report = {
        "schema_version": "southern-sweden-published-figure-comparison.v1",
        "source_url": SOURCE_URL,
        "source_pdf_sha256": SOURCE_SHA256,
        "source_figure": 6,
        "source_page": 490,
        "data_status": "manually_transcribed_rounded_published_figure_labels",
        "selection": "taxon_named_in_all_three_panels_within_region",
        "matched_named_taxa": len(rows),
        "regional_subsets": subsets,
        "pooled_named_subset_pollen_mae_pp": sum(
            int(row["pollen_absolute_error_pp"]) for row in rows
        )
        / len(rows),
        "pooled_named_subset_reveals_mae_pp": sum(
            int(row["reveals_absolute_error_pp"]) for row in rows
        )
        / len(rows),
        "repository_prediction_validated": False,
        "full_26_taxon_accuracy_estimated": False,
    }
    return rows, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows, report = produce(args.source_pdf)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "printed-labels.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )


if __name__ == "__main__":
    main()
