"""Score site-ID-withheld pollen means on authenticated author example counts."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from typing import cast

from bijux_pollenomics.analysis.lra_validation.baselines import (
    predict_spatial_baseline,
)
from bijux_pollenomics.analysis.lra_validation.contracts import (
    SiteRecord,
    site_group_id,
)
from bijux_pollenomics.analysis.lra_validation.metrics import score_pollen
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out


@dataclass(frozen=True)
class SiteCounts:
    """One author's prepared site table, with zero-count bins unavailable."""

    site_id: str
    source_sha256: str
    by_bin: dict[str, dict[str, int]]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checked(path: Path, sha256: str) -> Path:
    if _hash(path) != sha256:
        raise ValueError(f"Author input digest differs: {path}")
    return path


def _csv(path: Path) -> list[list[str]]:
    with path.open(newline="") as stream:
        return list(csv.reader(stream))


def _integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Count is not an exact nonnegative integer: {value}") from exc
    if str(parsed) != value or not 0 <= parsed <= 2**53:
        raise ValueError(f"Count is not an exact nonnegative integer: {value}")
    return parsed


def _site_counts(
    path: Path, site_id: str, bins: list[str], prepared_taxa: list[str], taxa: list[str]
) -> SiteCounts:
    rows = _csv(path)
    if rows[0] != ["TW", *bins] or [row[0] for row in rows[1:]] != [
        "radius",
        "model",
        *prepared_taxa,
    ]:
        raise ValueError(f"Author count axes differ: {path}")
    if any(len(row) != len(bins) + 1 for row in rows):
        raise ValueError(f"Author count row width differs: {path}")
    radii = [float(value) for value in rows[1][1:]]
    models = [_integer(value) for value in rows[2][1:]]
    by_bin: dict[str, dict[str, int]] = {}
    for position, bin_id in enumerate(bins):
        counts = {
            taxon: _integer(row[position + 1])
            for taxon, row in zip(taxa, rows[3:], strict=True)
        }
        if sum(counts.values()) > 0:
            if (
                not math.isfinite(radii[position])
                or radii[position] <= 0
                or models[position] not in {1, 2}
            ):
                raise ValueError(
                    f"Available author window lacks basin inputs: {path}/{bin_id}"
                )
            by_bin[bin_id] = counts
    return SiteCounts(site_id, _hash(path), by_bin)


def evaluate_grid(
    grid_id: str, bins: list[str], taxa: list[str], sites: list[SiteCounts]
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    """Predict each available target window from other site IDs in its own bin."""
    if len(sites) < 2 or len({site.site_id for site in sites}) != len(sites):
        raise ValueError("At least two distinct author site IDs are required")
    records = [
        SiteRecord(
            f"author:{grid_id}:{site.site_id}", f"author:{grid_id}:{site.site_id}"
        )
        for site in sites
    ]
    folds = grouped_leave_one_out(records)
    if len(folds) != len(sites):
        raise ValueError("Site-ID holdouts do not cover every author site")
    site_by_record = {
        record.record_id: site for record, site in zip(records, sites, strict=True)
    }
    group_by_site = {
        site.site_id: site_group_id((record.record_id,))
        for record, site in zip(records, sites, strict=True)
    }
    source_graph: dict[str, tuple[str, ...]] = {
        record.record_id: () for record in records
    }
    scores: list[dict[str, object]] = []
    predictions: list[dict[str, object]] = []
    site_summaries: list[dict[str, object]] = []
    for fold in folds:
        target = site_by_record[fold.test_record_ids[0]]
        if (
            len(fold.test_record_ids) != 1
            or group_by_site[target.site_id] not in fold.test_group_ids
        ):
            raise ValueError("Holdout does not isolate one complete site ID")
        training = [site_by_record[record_id] for record_id in fold.train_record_ids]
        site_mae: list[float] = []
        site_tv: list[float] = []
        attempted = 0
        for bin_id in bins:
            observed = target.by_bin.get(bin_id)
            if observed is None:
                scores.append(
                    {
                        "grid_id": grid_id,
                        "held_out_site_id": target.site_id,
                        "bin_id_bp": bin_id,
                        "status": "no_observed_count",
                        "training_sites": 0,
                        "observed_total_count": 0,
                        "mae_fraction": None,
                        "total_variation": None,
                        "training_manifest_sha256": None,
                    }
                )
                continue
            attempted += 1
            available = [site for site in training if bin_id in site.by_bin]
            if not available:
                scores.append(
                    {
                        "grid_id": grid_id,
                        "held_out_site_id": target.site_id,
                        "bin_id_bp": bin_id,
                        "status": "no_training_site_same_bin",
                        "training_sites": 0,
                        "observed_total_count": sum(observed.values()),
                        "mae_fraction": None,
                        "total_variation": None,
                        "training_manifest_sha256": None,
                    }
                )
                continue
            compositions = {
                group_by_site[site.site_id]: {
                    taxon: site.by_bin[bin_id][taxon]
                    / sum(site.by_bin[bin_id].values())
                    for taxon in taxa
                }
                for site in available
            }
            baseline = predict_spatial_baseline(
                fold,
                compositions,
                method="training_mean",
                input_ids=fold.train_record_ids,
                dependency_graph=source_graph,
                predictor_group_ids=tuple(compositions),
            )
            if target.site_id in {site.site_id for site in available}:
                raise ValueError("Target pollen entered its own training set")
            prediction = dict(baseline.fractions)
            result = score_pollen(prediction, observed)
            if (
                result.status != "scored"
                or result.mae_fraction is None
                or result.total_variation is None
            ):
                raise ValueError("Available observed count was not scored")
            site_mae.append(result.mae_fraction)
            site_tv.append(result.total_variation)
            scores.append(
                {
                    "grid_id": grid_id,
                    "held_out_site_id": target.site_id,
                    "bin_id_bp": bin_id,
                    "status": result.status,
                    "training_sites": len(available),
                    "observed_total_count": result.observed_total_count,
                    "mae_fraction": result.mae_fraction,
                    "total_variation": result.total_variation,
                    "training_manifest_sha256": baseline.training_manifest_sha256,
                }
            )
            for taxon in taxa:
                predictions.append(
                    {
                        "grid_id": grid_id,
                        "held_out_site_id": target.site_id,
                        "bin_id_bp": bin_id,
                        "taxon": taxon,
                        "observed_count": observed[taxon],
                        "predicted_fraction": prediction[taxon],
                        "training_sites": len(available),
                        "training_manifest_sha256": baseline.training_manifest_sha256,
                    }
                )
        site_summaries.append(
            {
                "site_id": target.site_id,
                "attempted_site_bins": attempted,
                "scored_site_bins": len(site_mae),
                "refused_no_training_site_bins": attempted - len(site_mae),
                "mean_mae_fraction": mean(site_mae) if site_mae else None,
                "mean_total_variation": mean(site_tv) if site_tv else None,
                "source_sha256": target.source_sha256,
            }
        )
    scored_sites = [
        row for row in site_summaries if row["mean_mae_fraction"] is not None
    ]
    if not scored_sites:
        raise ValueError("No site has a scoreable held-out author window")
    summary = {
        "grid_id": grid_id,
        "sites": len(sites),
        "bins": len(bins),
        "taxa": len(taxa),
        "attempted_site_bins": sum(
            cast(int, row["attempted_site_bins"]) for row in site_summaries
        ),
        "scored_site_bins": sum(
            cast(int, row["scored_site_bins"]) for row in site_summaries
        ),
        "refused_no_training_site_bins": sum(
            cast(int, row["refused_no_training_site_bins"]) for row in site_summaries
        ),
        "site_macro_mae_fraction": mean(
            cast(float, row["mean_mae_fraction"]) for row in scored_sites
        ),
        "site_macro_total_variation": mean(
            cast(float, row["mean_total_variation"]) for row in scored_sites
        ),
        "site_scores": site_summaries,
    }
    return scores, predictions, summary


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt_path = args.reference / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if (
        receipt.get("exit_code") != 0
        or receipt.get("input_files_unchanged") is not True
    ):
        raise ValueError(
            "Author input replay receipt is not successful and input-stable"
        )
    parity = json.loads((args.run / "report.json").read_text())
    _checked(receipt_path, parity["reference_receipt_sha256"])
    crosswalk_path = _checked(
        args.reference / "taxon-name-crosswalk.csv",
        parity["grids"][0]["crosswalk_sha256"],
    )
    with crosswalk_path.open(newline="") as stream:
        crosswalk = list(csv.DictReader(stream))
    taxa = [row["source"] for row in crosswalk]
    prepared = [row["prepared"] for row in crosswalk]
    if len(taxa) != 31 or len(set(taxa)) != 31 or len(set(prepared)) != 31:
        raise ValueError("Author taxon crosswalk is incomplete or ambiguous")
    working = args.author / "run.REVEALS.files"
    scores: list[dict[str, object]] = []
    predictions: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    seen_sites: set[str] = set()
    for grid in ("512", "562"):
        grid_report = next(item for item in parity["grids"] if item["grid_id"] == grid)
        manifest = json.loads((args.run / grid / "run-manifest.json").read_text())
        if (
            not grid_report["passed"]
            or manifest["parameters"]["source_revision"]
            != "57ead2e2fcc493d099be4e5a3092fc396e1c3d3a"
            or manifest["parameters"]["profile"] != parity["profile"]
        ):
            raise ValueError("Author profile, revision or retained parity differs")
        list_name = f"run.REVEALS.files/site.list.{grid}.csv"
        paths = (
            _checked(args.author / list_name, receipt["input_files"][list_name])
            .read_text()
            .splitlines()
        )
        if not paths or len(set(paths)) != len(paths):
            raise ValueError("Author site list is empty or repeated")
        bins: list[str] | None = None
        sites: list[SiteCounts] = []
        for name in paths:
            source_name = f"run.REVEALS.files/{name}"
            path = _checked(working / name, receipt["input_files"][source_name])
            header = _csv(path)[0]
            current_bins = header[1:]
            if bins is None:
                bins = current_bins
            if current_bins != bins or len(bins) != 25 or len(set(bins)) != 25:
                raise ValueError("Author bin axes differ")
            site_id = Path(name).stem.removeprefix("LRAready_")
            if site_id in seen_sites:
                raise ValueError("Author site ID occurs in multiple grids")
            seen_sites.add(site_id)
            sites.append(_site_counts(path, site_id, bins, prepared, taxa))
        assert bins is not None
        grid_scores, grid_predictions, summary = evaluate_grid(grid, bins, taxa, sites)
        if (
            summary["sites"] != grid_report["sites"]
            or summary["taxa"] != grid_report["taxa"]
            or summary["attempted_site_bins"] != grid_report["available_site_bins"]
        ):
            raise ValueError(
                "Observed-count support differs from retained source parity"
            )
        scores.extend(grid_scores)
        predictions.extend(grid_predictions)
        summaries.append(summary)
    args.output.mkdir(parents=True, exist_ok=False)
    _write_csv(args.output / "scores.csv", scores)
    _write_csv(args.output / "predictions.csv", predictions)
    result = {
        "schema_version": "author-example-observed-pollen-site-holdout.v1",
        "source": "rmfyfe/landclimII@57ead2e2fcc493d099be4e5a3092fc396e1c3d3a",
        "reference_receipt_sha256": _hash(receipt_path),
        "taxon_crosswalk_sha256": _hash(crosswalk_path),
        "method": "site_mean_of_training_observed_pollen_fractions_per_grid_bin",
        "split": "leave_one_author_site_id_out_within_each_grid",
        "count_denominator": "31_author_prepared_pollen_taxa",
        "score_units": "fraction",
        "measured_vegetation_accuracy": "not_evaluated",
        "swedish_cohort": "not_evaluated",
        "attempted_site_bins": sum(
            cast(int, grid["attempted_site_bins"]) for grid in summaries
        ),
        "scored_site_bins": sum(
            cast(int, grid["scored_site_bins"]) for grid in summaries
        ),
        "refused_no_training_site_bins": sum(
            cast(int, grid["refused_no_training_site_bins"]) for grid in summaries
        ),
        "site_macro_mae_fraction": mean(
            cast(float, site["mean_mae_fraction"])
            for grid in summaries
            for site in cast(list[dict[str, object]], grid["site_scores"])
            if site["mean_mae_fraction"] is not None
        ),
        "site_macro_total_variation": mean(
            cast(float, site["mean_total_variation"])
            for grid in summaries
            for site in cast(list[dict[str, object]], grid["site_scores"])
            if site["mean_total_variation"] is not None
        ),
        "grids": summaries,
    }
    (args.output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.output / "REPORT.md").write_text(
        "# Author-example observed pollen site holdouts\n\n"
        "The authenticated author-prepared 31-taxon count tables provide 17 site IDs "
        "in two grids. Each site ID was withheld in turn. For a target bin with counts, "
        "the predictor is the equal-site mean of observed pollen fractions from other "
        "site IDs in that grid and bin. The installed pollen scorer compares that "
        "prediction with withheld author-prepared integer counts. Target counts never enter "
        "their own fit. Zero-count bins are unavailable, not zero-valued observations.\n\n"
        f"Of {result['attempted_site_bins']} observed site-bin targets, "
        f"{result['scored_site_bins']} were scored and "
        f"{result['refused_no_training_site_bins']} had no other site in the bin. "
        f"The mean of the 17 site-level mean absolute errors is "
        f"{result['site_macro_mae_fraction']:.6f} in fraction units; "
        f"site-macro total variation is {result['site_macro_total_variation']:.6f}. "
        "The CSVs retain each bin score, refusal and taxon prediction.\n\n"
        "This is an exploratory observed-pollen baseline on author examples, not "
        "a Swedish cohort, spatial-block evaluation, LRA reconstruction score, "
        "or measured vegetation accuracy. Author site IDs have no reviewed "
        "cross-database alias closure; bins within a site are correlated and are "
        "summarized within site before the macro average. The 31 author-prepared "
        "taxa do not certify a full raw-core pollen denominator or source reuse rights "
        "for publication. No tuned parameters or uncertainty calibration are claimed.\n"
    )
    print(
        json.dumps(
            {
                "scored_site_bins": sum(grid["scored_site_bins"] for grid in summaries),
                "attempted_site_bins": sum(
                    grid["attempted_site_bins"] for grid in summaries
                ),
                "site_macro_mae_by_grid": {
                    grid["grid_id"]: grid["site_macro_mae_fraction"]
                    for grid in summaries
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
