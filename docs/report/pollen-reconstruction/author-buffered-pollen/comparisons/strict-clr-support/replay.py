"""Inspect only buffered training vectors for strict-positive CLR fit support."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.source import (
    GRIDS,
    _buffered_training,
    _study,
)
from bijux_pollenomics_dev.essd_reproduction.observed_pollen_baseline import (
    _checked,
    _site_counts,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    study = _study(args.author, args.reference)
    rows = []
    summaries = []
    source_hashes = {}
    for grid in GRIDS:
        retained = _buffered_training(study.sites, grid)
        training = {}
        for site in retained:
            name = f"run.REVEALS.files/{site.count_filename}"
            path = _checked(study.author / name, study.source_hashes[f"author/{name}"])
            counts = _site_counts(
                path, site.site_id, study.bins, study.prepared_taxa, study.taxa
            )
            source_hashes[site.site_id] = counts.source_sha256
            training[site.site_id] = counts
        for bin_id in study.bins:
            available = [
                site for site in retained if bin_id in training[site.site_id].by_bin
            ]
            zeros = {
                site.site_id: sum(
                    value == 0
                    for value in training[site.site_id].by_bin[bin_id].values()
                )
                for site in available
            }
            if any(count < 0 or count > len(study.taxa) for count in zeros.values()):
                raise ValueError("Invalid training taxon zero count")
            rows.append(
                {
                    "target_grid_id": grid,
                    "bin_id_bp": bin_id,
                    "available_training_sites": len(available),
                    "strict_positive_training_sites": sum(
                        count == 0 for count in zeros.values()
                    ),
                    "training_sites_with_zero_taxa": sum(
                        count > 0 for count in zeros.values()
                    ),
                    "zero_taxa_by_training_site": zeros,
                    "strict_clr_fit_possible": len(available) >= 2
                    and all(count == 0 for count in zeros.values()),
                }
            )
        block = [row for row in rows if row["target_grid_id"] == grid]
        summaries.append(
            {
                "target_grid_id": grid,
                "buffered_training_sites": len(retained),
                "bins_with_any_training_site": sum(
                    row["available_training_sites"] > 0 for row in block
                ),
                "bins_with_at_least_two_training_sites": sum(
                    row["available_training_sites"] >= 2 for row in block
                ),
                "bins_with_strict_clr_fit": sum(
                    row["strict_clr_fit_possible"] for row in block
                ),
            }
        )
    if len(rows) != 2 * len(study.bins) or len(study.taxa) != 31:
        raise ValueError("Author training diagnostic axes differ")
    report = {
        "schema_version": "author-pollen-buffered-training-clr-support.v1",
        "source_manifest_sha256": study.source_manifest_sha256,
        "metadata_sha256": study.metadata_sha256,
        "crosswalk_sha256": study.crosswalk_sha256,
        "consumed_training_count_sha256": source_hashes,
        "taxa": study.taxa,
        "bins": study.bins,
        "zero_policy": "strictly_positive_no_replacement",
        "required_training_sites_per_fit": 2,
        "target_count_files_opened_within_each_fold": 0,
        "blocks": summaries,
        "bin_support": rows,
        "scientific_acceptance": "training-support-diagnostic-only",
    }
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# Strict-positive CLR training support",
        "",
        "Each adjacent author grid is withheld in turn and the frozen 20 km basin-edge buffer is applied. Only buffered opposite-grid count files are opened in each fold. The current host CLR ridge model needs at least two training sites in the bin and positive fractions for all 31 taxa at each site; this diagnostic applies that rule without selecting a zero replacement.",
        "",
        "| Target grid | Buffered training sites | Bins with any training | Bins with at least two | Bins with strict CLR fit |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for block in summaries:
        lines.append(
            f"| {block['target_grid_id']} | {block['buffered_training_sites']} | {block['bins_with_any_training_site']} | {block['bins_with_at_least_two_training_sites']} | {block['bins_with_strict_clr_fit']} |"
        )
    lines += [
        "",
        "The report gives each bin and training site zero-taxon count. This is a fit-support diagnostic, not a pollen prediction or measured vegetation accuracy. A zero policy would require an explicit predeclared scientific choice; no count is changed here.",
    ]
    (args.output / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summaries))


if __name__ == "__main__":
    main()
