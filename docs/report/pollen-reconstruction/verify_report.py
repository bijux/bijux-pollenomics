"""Verify the retained pollen-study report and source-bound result tables."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any


REPORT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = REPORT_DIR.parents[2]
MANIFEST_PATH = REPORT_DIR / "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_publication_correspondence(scope: dict[str, Any]) -> None:
    """Keep publication ledgers bound to their distinct scientific claims."""
    correspondence = scope["publication_correspondence"]
    author_dir = REPOSITORY_ROOT / correspondence["author_example"]["directory"]
    author = json.loads((author_dir / "report.json").read_text(encoding="utf-8"))
    with (author_dir / "paper-correspondence.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        author_rows = list(csv.DictReader(stream))
    if (
        author["comparison"] != "installed_LRA_vs_independent_exact_author_R_replay"
        or author["unit"] != "fraction"
        or author["passed"] is not True
        or author["compared_values"] != 14074
        or len(author_rows) != author["compared_values"]
        or {row["unit"] for row in author_rows} != {"fraction"}
        or {row["within_declared_tolerance"] for row in author_rows} != {"True"}
        or max(
            abs(float(row["signed_residual"]))
            for row in author_rows
            if row["metric"] == "mean"
        )
        != author["max_absolute_mean_residual"]
        or max(
            abs(float(row["signed_residual"]))
            for row in author_rows
            if row["metric"] == "standard_error"
        )
        != author["max_absolute_standard_error_residual"]
    ):
        raise ValueError("author-example correspondence differs from retained claims")

    window_dir = REPOSITORY_ROOT / correspondence["published_window"]["directory"]
    window = json.loads((window_dir / "report.json").read_text(encoding="utf-8"))
    with (window_dir / "paper-correspondence.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        window_rows = list(csv.DictReader(stream))
    if (
        window["comparison"]
        != "retained_author_example_python_recomputation_minus_pangaea_937075_archive"
        or window["unit"] != "percentage_cover"
        or window["author_bin_bounds_bp"] != [100, 350]
        or window["tolerance"] != "none_descriptive_cross_revision_comparison"
        or len(window_rows) != 62
        or {row["unit"] for row in window_rows} != {"percentage_cover"}
        or {row["window"] for row in window_rows} != {"100-350 BP"}
        or {row["grid_id"] for row in window_rows} != {"512", "562"}
        or any(
            max(
                abs(float(row["mean_residual"]))
                for row in window_rows
                if row["grid_id"] == grid["grid_id"]
            )
            != float(grid["max_absolute_mean_residual_percentage_points"])
            for grid in window["grids"]
        )
    ):
        raise ValueError("published-window correspondence differs from retained claims")

    provenance_dir = (
        REPOSITORY_ROOT / correspondence["three_way_provenance"]["directory"]
    )
    provenance = json.loads(
        (provenance_dir / "report.json").read_text(encoding="utf-8")
    )
    with (provenance_dir / "paper-correspondence.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        provenance_rows = list(csv.DictReader(stream))
    if (
        provenance["paired_mean_se_values"] != 124
        or len(provenance_rows) != 124
        or {row["metric"] for row in provenance_rows} != {"mean", "standard_error"}
        or {row["grid_id"] for row in provenance_rows} != {"512", "562"}
        or provenance["historical_raw_input_closure"] != "not_established"
        or correspondence["three_way_provenance"]["paired_mean_se_values"] != 124
    ):
        raise ValueError(
            "three-way publication provenance differs from retained claims"
        )

    envelopes_dir = (
        REPOSITORY_ROOT / correspondence["uncertainty_envelopes"]["directory"]
    )
    envelopes = json.loads((envelopes_dir / "report.json").read_text(encoding="utf-8"))
    with (envelopes_dir / "taxon-envelopes.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        envelope_rows = list(csv.DictReader(stream))
    if (
        len(envelope_rows) != 62
        or any(row["one_se_envelopes_disjoint"] != "False" for row in envelope_rows)
        or any(
            grid["disjoint_one_se_envelopes"] != 0 for grid in envelopes["summaries"]
        )
        or envelopes["inferential_comparison"] != "not_evaluated"
        or correspondence["uncertainty_envelopes"]["taxon_envelopes"] != 62
        or correspondence["uncertainty_envelopes"]["disjoint_one_se_envelopes"] != 0
    ):
        raise ValueError("uncertainty envelopes differ from retained claims")

    alignment_dir = REPOSITORY_ROOT / correspondence["window_alignment"]["directory"]
    alignment = json.loads((alignment_dir / "report.json").read_text(encoding="utf-8"))
    with (alignment_dir / "window-correspondence.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        alignment_rows = list(csv.DictReader(stream))
    exact = [row["tw_index"] for row in alignment_rows if row["exact_bounds"] == "True"]
    if (
        len(alignment_rows) != 25
        or exact != ["2"]
        or alignment["compared_windows"] != 25
        or alignment["exact_tw_indices"] != exact
        or correspondence["window_alignment"]["compared_windows"] != 25
        or correspondence["window_alignment"]["exact_tw_indices"] != exact
    ):
        raise ValueError("publication window alignment differs from retained claims")


def verify_author_source(source_root: Path) -> None:
    """Authenticate private inputs with the same reader used by the study."""
    from bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.source import (
        _study,
    )

    custody = json.loads((REPORT_DIR / "author-source-custody.json").read_text())
    manifest_path = source_root / custody["original_manifest_filename"]
    if sha256(manifest_path) != custody["original_manifest_sha256"]:
        raise ValueError("private author source manifest digest mismatch")
    original = json.loads(manifest_path.read_text())
    if len(original["files"]) != custody["retained_manifest_file_count"]:
        raise ValueError("private author source manifest file count mismatch")
    total_bytes = 0
    authenticated = {}
    for relative, expected_digest in original["files"].items():
        path = (source_root / relative).resolve()
        if not path.is_relative_to(source_root.resolve()):
            raise ValueError("author source path escapes the supplied source root")
        size = path.stat().st_size
        digest = sha256(path)
        if digest != expected_digest:
            raise ValueError(f"private author source digest mismatch: {relative}")
        total_bytes += size
        authenticated[relative] = (size, digest)
    if total_bytes != custody["retained_manifest_file_bytes"]:
        raise ValueError("private author source byte count mismatch")
    for item in custody["required_development_files"]:
        if authenticated.get(item["path"]) != (item["bytes"], item["sha256"]):
            raise ValueError(f"private author source digest mismatch: {item['path']}")
    study = _study(source_root / "author", source_root / "reference")
    observed = {
        "sites": len(study.sites),
        "taxa": len(study.taxa),
        "bins": len(study.bins),
    }
    if observed != custody["expected_cohort"]:
        raise ValueError("private author source cohort differs from the retained study")
    print(
        f"authenticated private author inputs: {observed['sites']} sites, "
        f"{observed['taxa']} taxa and {observed['bins']} bins"
    )


def verify_author_target_pollen() -> None:
    """Check the retained 31-target split, frozen predictions and score support."""
    directory = REPOSITORY_ROOT / "docs/report/regions/nordic/author-target-pollen"
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    manifest_path = directory / "input-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(manifest_path) != report["input_manifest_sha256"]:
        raise ValueError("author-target input manifest digest mismatch")
    if manifest["target_outcomes_in_prediction_inputs"] is not False:
        raise ValueError("author-target predictor input includes target outcomes")
    axis = set(report["axis"])
    if len(axis) != 31 or axis != set(manifest["axis"]):
        raise ValueError("author-target response axis changed")
    for relative, digest in manifest["produced_file_sha256"].items():
        if sha256(directory / relative) != digest:
            raise ValueError(f"author-target prepared file digest mismatch: {relative}")
    for country in ("DK", "FI", "NO"):
        with gzip.open(
            directory / "inputs" / f"training-{country}.json.gz", "rt"
        ) as stream:
            training = json.load(stream)
        if any(profile["country"] == country for profile in training.values()):
            raise ValueError("held-out country occurs in author-target training")
        path = directory / "predictions" / f"predictions-{country}.json.gz"
        if sha256(path) != report["prediction_sha256"][country]:
            raise ValueError("author-target frozen prediction digest mismatch")
        with gzip.open(path, "rt") as stream:
            prediction = json.load(stream)
        if prediction["country"] != country or set(prediction["axis"]) != axis:
            raise ValueError("author-target prediction identity changed")
        for row in prediction["predictions"]:
            fractions = row["fractions"]
            if (
                row["target_pollen_counts_read"] is not False
                or set(fractions) != axis
                or any(
                    not math.isfinite(value) or value < 0
                    for value in fractions.values()
                )
                or abs(sum(fractions.values()) - 1) > 1e-10
            ):
                raise ValueError("invalid author-target prediction composition")
    for filename, digest_field in {
        "scores.csv": "scores_sha256",
        "coverage.csv": "coverage_sha256",
        "site-scores.csv": "site_scores_sha256",
        "taxon-diagnostics.csv": "taxon_diagnostics_sha256",
    }.items():
        if sha256(directory / filename) != report[digest_field]:
            raise ValueError(f"author-target scored output digest mismatch: {filename}")
    with (directory / "scores.csv").open(newline="", encoding="utf-8") as stream:
        scores = list(csv.DictReader(stream))
    with (directory / "coverage.csv").open(newline="", encoding="utf-8") as stream:
        coverage = list(csv.DictReader(stream))
    scored_keys = {
        (row["country"], row["site_id"], row["bin_id"], row["method"]) for row in scores
    }
    if (
        len(scores) != report["score_rows"]
        or len(scored_keys) != len(scores)
        or any(row["status"] != "scored" for row in scores)
        or len(scores)
        != len(report["methods"])
        * sum(int(row["positive_target_and_predicted_site_bins"]) for row in coverage)
    ):
        raise ValueError("author-target score support does not close")
    author_mass = json.loads(
        (
            REPOSITORY_ROOT
            / "docs/report/regions/nordic/author-taxonomy-mass/report.json"
        ).read_text(encoding="utf-8")
    )
    for row in author_mass["countries"]:
        country = row["country"]
        expected = report["country_source_denominators"][country]
        for field in (
            "selected_samples",
            "all_native_nisp",
            "author_assigned_nisp",
            "author_excluded_nisp",
            "unmapped_nisp",
        ):
            reported_field = {
                "all_native_nisp": "native_nisp",
                "author_assigned_nisp": "assigned_nisp",
            }.get(field, field)
            if row[field] != expected[reported_field]:
                raise ValueError(
                    f"author-target source denominator changed: {country} {field}"
                )


def verify_swedish_author_target_pollen() -> None:
    """Check Swedish exclusion, source mass, frozen predictions and scores."""
    directory = (
        REPOSITORY_ROOT / "docs/report/regions/nordic/swedish-author-target-pollen"
    )
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    manifest_path = directory / "input-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    parent = REPOSITORY_ROOT / "docs/report/regions/nordic/author-target-pollen"
    if (
        sha256(manifest_path) != report["input_manifest_sha256"]
        or sha256(parent / "input-manifest.json")
        != manifest["parent_input_manifest_sha256"]
        or manifest["target_outcomes_in_prediction_inputs"] is not False
        or len(manifest["axis"]) != 31
        or manifest["axis"] != report["axis"]
    ):
        raise ValueError("Swedish author-target input identity changed")
    for relative, digest in manifest["parent_training_sha256"].items():
        if sha256(parent / relative) != digest:
            raise ValueError("Swedish author-target parent training changed")
    for relative, digest in manifest["produced_file_sha256"].items():
        if sha256(directory / relative) != digest:
            raise ValueError("Swedish author-target prepared input changed")
    with gzip.open(directory / "inputs/training-SE.json.gz", "rt") as stream:
        training = json.load(stream)
    if len(training) != 81 or {row["country"] for row in training.values()} != {
        "DK",
        "FI",
        "NO",
    }:
        raise ValueError("Swedish pollen occurs in cross-border training")
    prediction_path = directory / "predictions/predictions-SE.json.gz"
    if sha256(prediction_path) != report["prediction_sha256"]["SE"]:
        raise ValueError("Swedish author-target predictions changed")
    with gzip.open(prediction_path, "rt") as stream:
        predictions = json.load(stream)
    if predictions["country"] != "SE" or predictions["axis"] != report["axis"]:
        raise ValueError("Swedish author-target prediction axis changed")
    for row in predictions["predictions"]:
        fractions = row["fractions"]
        if (
            row["target_pollen_counts_read"] is not False
            or set(fractions) != set(report["axis"])
            or any(
                not math.isfinite(value) or value < 0 for value in fractions.values()
            )
            or abs(sum(fractions.values()) - 1) > 1e-10
        ):
            raise ValueError("invalid Swedish author-target prediction")
    for filename, field in {
        "scores.csv": "scores_sha256",
        "coverage.csv": "coverage_sha256",
        "site-scores.csv": "site_scores_sha256",
        "taxon-diagnostics.csv": "taxon_diagnostics_sha256",
    }.items():
        if sha256(directory / filename) != report[field]:
            raise ValueError("Swedish author-target score digest changed")
    with (directory / "scores.csv").open(newline="", encoding="utf-8") as stream:
        scores = list(csv.DictReader(stream))
    with (directory / "coverage.csv").open(newline="", encoding="utf-8") as stream:
        coverage = list(csv.DictReader(stream))
    if (
        len(scores) != report["score_rows"]
        or len(scores) != len(report["methods"]) * 51
        or len(predictions["refusals"]) != 3
        or len(predictions["predictions"]) != len(scores)
        or len(coverage) != 1
        or int(coverage[0]["candidate_site_bins"]) != 54
        or int(coverage[0]["positive_target_and_predicted_site_bins"]) != 51
    ):
        raise ValueError("Swedish author-target score support changed")
    with gzip.open(directory / "sealed-outcomes/outcomes-SE.json.gz", "rt") as stream:
        outcomes = json.load(stream)
    bins = [cell for site in outcomes.values() for cell in site.values()]
    denominator = report["country_source_denominators"]["SE"]
    if (
        len(outcomes) != denominator["sites"]
        or sum(cell["all_pollen_nisp"] for cell in bins) != denominator["native_nisp"]
        or sum(cell["closed_nisp"] for cell in bins) != denominator["assigned_nisp"]
        or denominator["assigned_nisp"]
        + denominator["author_excluded_nisp"]
        + denominator["unmapped_nisp"]
        != denominator["native_nisp"]
    ):
        raise ValueError("Swedish author-target source mass changed")
    mass_path = (
        REPOSITORY_ROOT
        / "docs/report/source-relations/neotoma/author-taxonomy-mass/report.json"
    )
    config_path = (
        REPOSITORY_ROOT
        / "docs/report/pollen-reconstruction/swedish-direct-pollen/config.json"
    )
    if (
        sha256(mass_path) != manifest["swedish_common_bin_mass_sha256"]
        or sha256(config_path) != manifest["swedish_common_bin_config_sha256"]
    ):
        raise ValueError("Swedish common-bin source identity changed")
    mass = json.loads(mass_path.read_text(encoding="utf-8"))
    common = set(
        json.loads(config_path.read_text(encoding="utf-8"))["common_age_bin_ids"]
    )
    common_cells = [
        cell
        for site in outcomes.values()
        for bin_id, cell in site.items()
        if int(bin_id) in common
    ]
    if (
        len(common_cells) != mass["common_bin_count"]
        or sum(cell["all_pollen_nisp"] for cell in common_cells)
        != sum(site["all_native_nisp"] for site in mass["sites"])
        or sum(cell["closed_nisp"] for cell in common_cells)
        != sum(site["author_assigned_nisp"] for site in mass["sites"])
    ):
        raise ValueError("Swedish common-bin author target mass differs")


def verify_pft_uncertainty_bounds() -> dict[str, Any]:
    """Check source identity and complete published uncertainty-bound coverage."""
    directory = (
        REPOSITORY_ROOT
        / "docs/report/publication-replay/landclim-pft-crosswalk/uncertainty-bounds"
    )
    report: dict[str, Any] = json.loads(
        (directory / "report.json").read_text(encoding="utf-8")
    )
    if sha256(directory / "windows.csv") != report["window_csv_sha256"]:
        raise ValueError("PFT uncertainty window ledger changed")
    for source in report["inputs"]:
        if sha256(REPOSITORY_ROOT / source["path"]) != source["sha256"]:
            raise ValueError("PFT uncertainty source changed")
    with (directory / "windows.csv").open(newline="", encoding="utf-8") as stream:
        windows = list(csv.DictReader(stream))
    if (
        len(windows) != 125
        or report["same_draw_covariance_aggregation_verified"] is not False
        or set(report["summary"]) != {"ET", "ST", "OL", "ISTS", "TBS"}
    ):
        raise ValueError("PFT uncertainty support changed")
    for group, summary in report["summary"].items():
        selected = [row for row in windows if row["group"] == group]
        if (
            len(selected) != 25
            or {int(row["window"]) for row in selected} != set(range(1, 26))
            or any(int(row["grid_rows"]) != 420 for row in selected)
            or sum(int(row["grid_rows"]) for row in selected)
            != summary["grid_window_rows"]
            or any(
                sum(int(row[field]) for row in selected) != summary[field]
                for field in (
                    "below_lower_bound_rows",
                    "above_upper_bound_rows",
                    "nondegenerate_bound_rows",
                    "strictly_inside_bound_rows",
                )
            )
            or summary["below_lower_bound_rows"]
            or summary["above_upper_bound_rows"]
        ):
            raise ValueError(f"PFT uncertainty support differs: {group}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--author-source-root",
        type=Path,
        help="private source capsule containing author/, reference/ and the original manifest",
    )
    args = parser.parse_args()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "pollen-reconstruction-report-manifest.v1":
        raise ValueError("unexpected pollen reconstruction manifest schema")
    for item in manifest["files"]:
        relative = item["path"]
        if relative.startswith("artifacts/"):
            raise ValueError(f"durable report depends on disposable output: {relative}")
        path = (REPOSITORY_ROOT / relative).resolve()
        if not path.is_relative_to(REPOSITORY_ROOT) or not path.is_file():
            raise ValueError(f"invalid report evidence path: {relative}")
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"report evidence digest mismatch: {relative}")

    results_path = REPORT_DIR / "results.csv"
    with results_path.open(newline="", encoding="utf-8") as stream:
        results = list(csv.reader(stream))
    if not results or any(len(row) != 8 for row in results):
        raise ValueError("scientific result table must have eight columns")
    scope = json.loads((REPORT_DIR / "scope.json").read_text(encoding="utf-8"))
    if scope.get("confirmatory_result") is not False:
        raise ValueError("scoped report must not declare a confirmatory result")
    verify_publication_correspondence(scope)
    with (REPORT_DIR / "swedish-source-questions.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        source_questions = list(csv.reader(stream))
    if (
        len(source_questions) != 11
        or source_questions[0]
        != [
            "site",
            "neotoma_dataset_id",
            "neotoma_site_id",
            "rootsi_archive_member",
            "observed_gap",
            "question",
            "dependent_use",
        ]
        or any(
            len(row) != 7 or any(not cell.strip() for cell in row)
            for row in source_questions[1:]
        )
    ):
        raise ValueError("Swedish source questions have missing or shifted columns")
    baseline_scope = scope["author_example_site_mean_holdout"]
    baseline_path = (
        "docs/report/pollen-reconstruction/author-example-site-mean-holdout/report.json"
    )
    if baseline_scope["report"] != baseline_path:
        raise ValueError("Author site-mean report path changed")
    baseline = json.loads((REPOSITORY_ROOT / baseline_path).read_text())
    for field in (
        "attempted_site_bins",
        "scored_site_bins",
        "refused_no_training_site_bins",
        "site_macro_mae_fraction",
        "site_macro_total_variation",
    ):
        if baseline_scope[field] != baseline[field]:
            raise ValueError(f"Author site-mean scope differs: {field}")
    baseline_dir = REPOSITORY_ROOT / Path(baseline_path).parent
    with (baseline_dir / "scores.csv").open(newline="", encoding="utf-8") as stream:
        baseline_scores = list(csv.DictReader(stream))
    with (baseline_dir / "predictions.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        baseline_predictions = list(csv.DictReader(stream))
    scored_keys = {
        (row["grid_id"], row["held_out_site_id"], row["bin_id_bp"])
        for row in baseline_scores
        if row["status"] == "scored"
    }
    prediction_keys = {
        (row["grid_id"], row["held_out_site_id"], row["bin_id_bp"])
        for row in baseline_predictions
    }
    if (
        len(baseline_scores) != 425
        or len(scored_keys) != baseline["scored_site_bins"]
        or sum(row["status"] == "no_training_site_same_bin" for row in baseline_scores)
        != baseline["refused_no_training_site_bins"]
        or prediction_keys != scored_keys
        or len(baseline_predictions) != baseline["scored_site_bins"] * 31
    ):
        raise ValueError("Author site-mean score and prediction support differs")
    custody = json.loads((REPORT_DIR / "author-source-custody.json").read_text())
    for field in ("producer", "source_reader"):
        identity = custody[field]
        if sha256(REPOSITORY_ROOT / identity["path"]) != identity["sha256"]:
            raise ValueError(f"author source custody code digest mismatch: {field}")
    if (
        custody["original_manifest_sha256"]
        != scope["producer_and_source_identities"][
            "author_development_source_manifest_sha256"
        ]
    ):
        raise ValueError("author study and custody source identities differ")

    swedish = REPORT_DIR / "swedish-direct-pollen"
    input_manifest = json.loads((swedish / "input-manifest.json").read_text())
    if input_manifest["config_sha256"] != sha256(swedish / "config.json"):
        raise ValueError("Swedish direct-pollen configuration digest mismatch")
    producer = (
        REPOSITORY_ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/swedish_direct_pollen.py"
    )
    if input_manifest["runner_sha256"] != sha256(producer):
        raise ValueError("Swedish direct-pollen producer digest mismatch")

    native = REPORT_DIR / "swedish-native-sequences"
    native_manifest = json.loads((native / "manifest.json").read_text())
    for filename, expected in native_manifest["files_sha256"].items():
        if sha256(native / filename) != expected:
            raise ValueError(f"Swedish native sequence digest mismatch: {filename}")

    nordic_dir = REPOSITORY_ROOT / "docs/report/regions/nordic/direct-pollen"
    nordic = json.loads((nordic_dir / "manifest.json").read_text(encoding="utf-8"))
    declared = scope["producer_and_source_identities"]
    if (
        declared["nordic_direct_pollen_scored_rows"] != nordic["scored_rows"]
        or declared["nordic_direct_pollen_prediction_rows"]
        != nordic["prediction_counts"]
    ):
        raise ValueError("Nordic report scope differs from retained prediction counts")
    countries = set(scope["nordic_direct_pollen_country_holdout"]["target_countries"])
    if countries != set(nordic["prediction_sha256"]):
        raise ValueError("Nordic target countries differ from retained predictions")
    for field, filename in {
        "results_sha256": "RESULTS.md",
        "cohort_sha256": "cohort.csv",
        "coverage_sha256": "coverage.csv",
        "prediction_table_sha256": "predictions.csv",
        "scores_sha256": "scores.csv",
        "site_scores_sha256": "site-scores.csv",
        "training_sources_sha256": "training-sources.csv",
    }.items():
        if nordic[field] != sha256(nordic_dir / filename):
            raise ValueError(f"Nordic direct-pollen digest mismatch: {filename}")
    for country in sorted(countries):
        prediction_path = nordic_dir / f"predictions-{country}.json"
        if nordic["prediction_sha256"][country] != sha256(prediction_path):
            raise ValueError(
                f"Nordic direct-pollen digest mismatch: {prediction_path.name}"
            )
    with gzip.open(
        REPORT_DIR / "author-development-predictions.csv.gz", "rb"
    ) as stream:
        if not stream.read(1):
            raise ValueError("compressed development predictions are empty")

    verify_author_target_pollen()
    author_target_scope = scope["nordic_author_target_pollen"]
    author_target = json.loads(
        (REPOSITORY_ROOT / author_target_scope["report"]).read_text(encoding="utf-8")
    )
    if (
        author_target_scope["input_manifest_sha256"]
        != author_target["input_manifest_sha256"]
        or author_target_scope["author_target_taxa"] != len(author_target["axis"])
        or author_target_scope["fixed_method_score_rows"] != author_target["score_rows"]
    ):
        raise ValueError("author-target scope differs from the retained study")

    verify_swedish_author_target_pollen()
    swedish_author_scope = scope["swedish_author_target_pollen"]
    swedish_author = json.loads(
        (REPOSITORY_ROOT / swedish_author_scope["report"]).read_text(encoding="utf-8")
    )
    if (
        swedish_author_scope["input_manifest_sha256"]
        != swedish_author["input_manifest_sha256"]
        or swedish_author_scope["fixed_method_score_rows"]
        != swedish_author["score_rows"]
        or swedish_author_scope["author_target_taxa"] != len(swedish_author["axis"])
    ):
        raise ValueError("Swedish author-target scope differs from the retained study")

    lake_scope = scope["swedish_lake_transfer"]
    lake_dir = REPOSITORY_ROOT / Path(lake_scope["report"]).parent
    lake_report = json.loads((lake_dir / "report.json").read_text())
    lake_inputs = json.loads((lake_dir / "input-manifest.json").read_text())
    lake_freeze = json.loads((lake_dir / "prediction-freeze.json").read_text())
    with (lake_dir / "coverage.csv").open(newline="", encoding="utf-8") as stream:
        lake_coverage = list(csv.DictReader(stream))
    lake_denominator = lake_report["country_source_denominators"]["SE"]
    if (
        lake_scope["protocol"]
        != str(Path(lake_scope["report"]).parent / "protocol.json")
        or lake_scope["prediction_freeze"]
        != str(Path(lake_scope["report"]).parent / "prediction-freeze.json")
        or lake_scope["prediction_freeze_sha256"]
        != sha256(lake_dir / "prediction-freeze.json")
        or lake_freeze["prediction_sha256"] != lake_report["prediction_sha256"]["SE"]
        or lake_scope["physical_lake_sites"] != lake_denominator["sites"]
        or lake_scope["selected_samples"] != lake_denominator["selected_samples"]
        or lake_scope["excluded_source_samples"]
        != lake_inputs["excluded_source_samples"]
        or lake_scope["native_pollen_nisp"] != lake_denominator["native_nisp"]
        or lake_scope["author_assigned_nisp"] != lake_denominator["assigned_nisp"]
        or lake_scope["fixed_method_score_rows"] != lake_report["score_rows"]
        or len(lake_coverage) != 1
        or lake_scope["candidate_and_scored_site_bins"]
        != int(lake_coverage[0]["positive_target_and_predicted_site_bins"])
        or "swedish-lake-transfer" not in {row[0] for row in results[1:]}
    ):
        raise ValueError("Swedish lake transfer scope differs from retained result")

    pft_bounds = verify_pft_uncertainty_bounds()
    pft_scope = scope["pft_uncertainty_bounds"]
    if (
        pft_scope["groups"] != len(pft_bounds["summary"])
        or pft_scope["grid_window_rows_per_group"] != 10500
        or pft_scope["necessary_bound_violations"] != 0
        or pft_scope["same_draw_covariance_aggregation_verified"]
        != pft_bounds["same_draw_covariance_aggregation_verified"]
    ):
        raise ValueError("PFT uncertainty scope differs from retained result")

    print(
        f"verified {len(manifest['files'])} retained files, "
        f"{len(results) - 1} scientific result rows and Swedish/Nordic source manifests"
    )
    if args.author_source_root is not None:
        verify_author_source(args.author_source_root)


if __name__ == "__main__":
    main()
