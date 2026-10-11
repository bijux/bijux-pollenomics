"""Verify the retained pollen-study report and source-bound result tables."""

from __future__ import annotations

import argparse
from collections import Counter
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


def verify_swedish_landclim_support(
    swedish: Path, input_manifest: dict[str, Any]
) -> None:
    """Bind the reported six-name NISP support to source names and site counts."""
    parameters = (
        REPOSITORY_ROOT / "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"
    )
    with parameters.open(newline="", encoding="utf-8-sig") as stream:
        source_names = {
            row["Plant taxa/Pollen-morphological types"]
            for row in csv.DictReader(stream)
        }
    common = source_names & set(input_manifest["taxon_denominator"])
    if common != {
        "Betula",
        "Ulmus",
        "Salix",
        "Cyperaceae",
        "Filipendula",
        "Plantago lanceolata",
    }:
        raise ValueError("Swedish exact-name LandClim support changed")
    expected = {
        "19913": ("Abborrtjärnen", 50_208, 129_750, 38.7),
        "53995": ("Bussjösjön", 12_456, 68_668, 18.1),
        "54001": ("Bökesjön", 11_102, 42_548, 26.1),
    }
    for dataset_id, (site, count, denominator, percentage) in expected.items():
        profile = json.loads(
            (swedish / "prepared" / f"dataset-{dataset_id}.json").read_text()
        )
        bins = profile["bins"].values()
        source_count = sum(sum(row["counts"][name] for name in common) for row in bins)
        native_count = sum(row["all_nisp_count"] for row in profile["bins"].values())
        if (
            profile["site"] != site
            or source_count != count
            or native_count != denominator
            or profile["all_nisp_count"] != native_count
            or round(100 * source_count / native_count, 1) != percentage
        ):
            raise ValueError(f"Swedish LandClim support differs: {dataset_id}")


def verify_author_radius_sensitivity() -> None:
    """Keep frozen forward projections and paired scores bound to the old study."""
    root = REPORT_DIR / "author-lra-constrained"
    study = root / "radius-sensitivity"
    frozen_path = study / "frozen/predictions.json"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    report = json.loads((study / "scored/report.json").read_text(encoding="utf-8"))
    if (
        frozen["outcomes_opened"] is not False
        or frozen["source"]["experiment_sha256"]
        != "aba70474156edfd1e03ac777ddb1083b8f396f3e3a21a03d104a3b3713a544b4"
        or frozen["source"]["prediction_manifest_sha256"]
        != "56bc555a2373fb16c291e6fb9dc50cc43b5f99f7b03dc6e516c00c14d953329f"
        or frozen["factors"] != [0.8, 1.0, 1.2]
        or report["prediction_freeze_sha256"] != sha256(frozen_path)
        or report["eligible_sites"] != 15
        or report["scored_sites"] != 14
        or report["refused_site"] != "author:BECKHAM"
    ):
        raise ValueError("author radius sensitivity source or coverage changed")
    predictions = frozen["rows"]
    with (study / "scored/scores.csv").open(newline="", encoding="utf-8") as stream:
        scores = list(csv.DictReader(stream))

    def key(row: dict[str, Any]) -> tuple[str, str, float]:
        return row["record_id"], row["method"], float(row["radius_factor"])

    if (
        len(predictions) != 126
        or len(scores) != 126
        or len({key(row) for row in predictions}) != 126
        or {key(row) for row in predictions} != {key(row) for row in scores}
    ):
        raise ValueError("author radius sensitivity rows differ")
    with (root / "scores.csv").open(newline="", encoding="utf-8") as stream:
        original = {
            (row["target_record_id"], row["method"]): float(row["mae_fraction"])
            for row in csv.DictReader(stream)
            if row["status"] == "scored"
        }
    for row in scores:
        if float(row["radius_factor"]) == 1.0 and not math.isclose(
            float(row["mae_fraction"]),
            original[row["record_id"], row["method"]],
            abs_tol=1e-15,
            rel_tol=0,
        ):
            raise ValueError("author radius baseline score differs")
    for summary in report["site_macro"]:
        selected = [
            row
            for row in scores
            if row["method"] == summary["method"]
            and float(row["radius_factor"]) == summary["radius_factor"]
        ]
        if len(selected) != 14 or any(
            not math.isclose(
                sum(float(row[field]) for row in selected) / 14,
                summary[result_field],
                abs_tol=1e-15,
                rel_tol=0,
            )
            for field, result_field in (
                ("mae_fraction", "site_macro_mae_fraction"),
                ("hellinger_distance", "site_macro_hellinger_distance"),
            )
        ):
            raise ValueError("author radius site-macro summary differs")

    paired_dir = study / "paired"
    paired_report = json.loads((paired_dir / "report.json").read_text())
    expected_sources = {
        "radius_report": study / "scored/report.json",
        "radius_scores": study / "scored/scores.csv",
        "direct_mae": root / "direct-pollen/matched-scores.csv",
        "direct_hellinger": root / "direct-pollen/paired-hellinger.json",
    }
    if (
        paired_report["source_sha256"]
        != {name: sha256(path) for name, path in expected_sources.items()}
        or paired_report["producer_sha256"] != sha256(study / "paired_comparison.py")
        or paired_report["matched_sites"] != 14
        or paired_report["paired_rows"] != 126
        or len(paired_report["summary"]) != 9
    ):
        raise ValueError("author radius paired source identity changed")
    with (paired_dir / "paired-scores.csv").open(newline="") as stream:
        paired = list(csv.DictReader(stream))
    radius_by_key = {key(row): row for row in scores}
    if len(paired) != 126 or {key(row) for row in paired} != set(radius_by_key):
        raise ValueError("author radius paired support changed")
    for row in paired:
        source = radius_by_key[key(row)]
        if (
            row["observation_sha256"] != source["observation_sha256"]
            or not math.isclose(
                float(row["lra_mae_fraction"]),
                float(source["mae_fraction"]),
                abs_tol=1e-15,
                rel_tol=0,
            )
            or not math.isclose(
                float(row["direct_mae_fraction"]) - float(row["lra_mae_fraction"]),
                float(row["direct_minus_lra_mae_fraction"]),
                abs_tol=1e-15,
                rel_tol=0,
            )
        ):
            raise ValueError("author radius paired row differs")
    for summary in paired_report["summary"]:
        subset = [
            row
            for row in paired
            if row["method"] == summary["method"]
            and float(row["radius_factor"]) == summary["radius_factor"]
        ]
        if (
            len(subset) != 14
            or summary["direct_minus_lra_mae_fraction"] >= 0
            or summary["direct_minus_lra_hellinger_distance"] >= 0
            or sum(float(row["direct_minus_lra_mae_fraction"]) < 0 for row in subset)
            != summary["direct_lower_mae_sites"]
            or any(
                not math.isclose(
                    sum(float(row[field]) for row in subset) / 14,
                    summary[field],
                    abs_tol=1e-15,
                    rel_tol=0,
                )
                for field in (
                    "direct_mae_fraction",
                    "lra_mae_fraction",
                    "direct_minus_lra_mae_fraction",
                    "direct_hellinger_distance",
                    "lra_hellinger_distance",
                    "direct_minus_lra_hellinger_distance",
                )
            )
        ):
            raise ValueError("author radius paired summary differs")


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


def verify_publication_input_inventory(scope: dict[str, Any]) -> None:
    """Keep publication metadata distinct from authenticated primary inputs."""
    declared = scope["publication_input_inventory"]
    directory = REPOSITORY_ROOT / declared["directory"]
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    source = manifest["source"]
    for key in ("receipt", "workbook"):
        item = source[key]
        if sha256(REPOSITORY_ROOT / item["path"]) != item["sha256"]:
            raise ValueError(f"publication metadata source differs: {key}")
    for item in manifest["artifacts"]:
        path = directory / item["path"]
        if path.stat().st_size != item["byte_count"] or sha256(path) != item["sha256"]:
            raise ValueError(f"publication inventory artifact differs: {item['path']}")
    with (directory / "primary-source-crosswalk.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        crosswalk = list(csv.DictReader(stream))
    with (directory / "refusals.csv").open(newline="", encoding="utf-8") as stream:
        refusals = list(csv.DictReader(stream))
    rows = {row["worksheet_row"] for row in crosswalk}
    if (
        len(crosswalk) != declared["publication_metadata_records"]
        or len(rows) != len(crosswalk)
        or any(row["crosswalk_status"] != "unresolved" for row in crosswalk)
        or len(refusals) != declared["refusal_ledger_records"]
        or {row["worksheet_row"] for row in refusals} != rows
        or set(Counter(row["worksheet_row"] for row in refusals).values()) != {4}
        or any(
            row["state"] not in {"not_authenticated", "unresolved"} for row in refusals
        )
        or report["denominators"]["reproduction_ready_records"]
        != declared["reproduction_ready_records"]
        or report["claims"]["whole_paper_reproduction_certified"] is not False
    ):
        raise ValueError("publication input inventory differs from retained claims")


def verify_author_buffered_pollen(scope: dict[str, Any]) -> None:
    """Bind the buffered four-method diagnostic to frozen source and scores."""
    declared = scope["author_buffered_spatial_pollen"]
    directory = REPOSITORY_ROOT / declared["directory"]
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if (
        manifest["private_source_manifest_sha256"]
        != declared["private_source_manifest_sha256"]
        or len(manifest["files"]) != 54
    ):
        raise ValueError("buffered author source custody differs")
    for item in manifest["files"]:
        path = directory / item["path"]
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"buffered author output differs: {item['path']}")
    for relative, digest in manifest["producer_sha256"].items():
        if sha256(REPOSITORY_ROOT / relative) != digest:
            raise ValueError(f"buffered author producer differs: {relative}")

    comparison = json.loads(
        (directory / "comparisons/fitted-common-support/report.json").read_text(
            encoding="utf-8"
        )
    )
    baseline = json.loads(
        (directory / "comparisons/taxon/report.json").read_text(encoding="utf-8")
    )
    strict = json.loads(
        (directory / "comparisons/strict-clr-support/report.json").read_text(
            encoding="utf-8"
        )
    )
    if (
        comparison["observed_site_bins"] != declared["observed_site_bins"]
        or baseline["common_scored_site_bins"] != declared["fixed_baseline_scored_bins"]
        or comparison["common_scored_site_bins"]
        != declared["four_method_common_scored_bins"]
        or any(block["bins_with_strict_clr_fit"] != 0 for block in strict["blocks"])
    ):
        raise ValueError("buffered author support differs from retained claims")
    method_dirs = {
        "training_mean": "training-mean",
        "nearest_site": "nearest-site",
        "inverse_distance_squared": "inverse-distance-squared",
        "clr_rbf_ridge_half_count": "fitted-clr-rbf",
    }
    metrics = {item["method"]: item for item in comparison["methods"]}
    if (
        metrics["clr_rbf_ridge_half_count"]["common_site_macro_mae_fraction"]
        != declared["fitted_site_macro_mae_fraction"]
        or metrics["training_mean"]["common_site_macro_mae_fraction"]
        != declared["training_mean_common_site_macro_mae_fraction"]
    ):
        raise ValueError("buffered author method scores differ")
    for method, name in method_dirs.items():
        scores_dir = directory / name / "scores"
        report_path = scores_dir / "report.json"
        score_path = scores_dir / "scores.csv"
        receipt = comparison["score_receipts"][method]
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if (
            sha256(report_path) != receipt["report_sha256"]
            or sha256(score_path) != receipt["scores_sha256"]
            or report["scored_site_bins"]
            != comparison["method_specific_scored_bins"][method]
        ):
            raise ValueError(f"buffered author score receipt differs: {method}")
        for grid, digest in report["prediction_report_sha256"].items():
            if sha256(directory / name / f"grid-{grid}/report.json") != digest:
                raise ValueError(
                    f"buffered author prediction receipt differs: {method}"
                )


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
        / "reports/science/publication-correspondence/pft-crosswalk/uncertainty-bounds"
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


def _same_or_adjacent_float(observed: float, expected: float) -> bool:
    """Allow one binary rounding step across Python summation implementations."""
    return (
        math.isfinite(observed)
        and math.isfinite(expected)
        and observed
        in (
            expected,
            math.nextafter(expected, math.inf),
            math.nextafter(expected, -math.inf),
        )
    )


def verify_sambosjon_contained_age_support(
    scope: dict[str, Any], results: list[list[str]]
) -> None:
    """Reconcile pinned source support, count partitions and matched score means."""
    interval_scope = scope["sambosjon_contained_age_support"]
    interval_dir = REPOSITORY_ROOT / Path(interval_scope["report"]).parent
    interval = json.loads((interval_dir / "report.json").read_text())
    with (interval_dir / "coverage.csv").open(newline="") as stream:
        interval_coverage = list(csv.DictReader(stream))
    with (interval_dir / "scores.csv").open(newline="") as stream:
        interval_scores = list(csv.DictReader(stream))
    with (interval_dir / "samples.csv").open(newline="") as stream:
        interval_samples = list(csv.DictReader(stream))
    if (
        interval["producer_sha256"]
        != sha256(REPOSITORY_ROOT / interval_scope["producer"])
        or interval_scope["status"] != interval["status"]
        or interval_scope["confirmatory_result"] is not False
        or interval_scope["independent_vegetation_comparison"] is not False
        or len(interval_samples) != interval_scope["source_samples"]
        or len({r["sample_id"] for r in interval_samples}) != 111
        or interval_scope["contained_samples"]
        != interval["sample_statuses"]["contained"]
        or interval_scope["boundary_crossing_samples"]
        != interval["sample_statuses"]["crosses_boundary"]
        or len(interval_coverage) != interval_scope["candidate_bins"]
        or sum(r["status"] == "scored" for r in interval_coverage)
        != interval_scope["scored_common_bins"]
        or sum(r["status"] != "scored" for r in interval_coverage)
        != interval_scope["refused_bins"]
        or len(interval_scores) != 66
        or len({(r["bin_id"], r["method"]) for r in interval_scores}) != 66
        or sum(r["status"] == "scored" for r in interval_scores) != 63
        or any(
            r["mae_fraction"] or r["hellinger_distance"]
            for r in interval_scores
            if r["status"] != "scored"
        )
        or "sambosjon-contained-age-support" not in {row[0] for row in results[1:]}
    ):
        raise ValueError("Sämbosjön contained-age scope differs from retained result")
    for status, expected in interval["sample_mass"].items():
        selected = [r for r in interval_samples if r["status"] == status]
        if len(selected) != interval["sample_statuses"][status] or any(
            sum(int(r[key]) for r in selected) != value
            for key, value in expected.items()
        ):
            raise ValueError("Sämbosjön interval count/sample populations do not close")
    for method, summary in interval["methods"].items():
        selected = [
            r
            for r in interval_scores
            if r["method"] == method and r["status"] == "scored"
        ]
        if len(selected) != summary["paired_bins"] or any(
            not _same_or_adjacent_float(
                sum(float(r[key]) for r in selected) / len(selected),
                summary[key],
            )
            for key in (
                "mae_fraction",
                "hellinger_distance",
                "parent_same_bin_mae_fraction",
                "parent_same_bin_hellinger_distance",
            )
        ):
            raise ValueError(
                "Sämbosjön interval method summaries differ from score rows"
            )
    for relative, expected in interval["input_sha256"].items():
        if sha256(interval_dir.parent / relative) != expected:
            raise ValueError("Sämbosjön pinned interval input changed")


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
    verify_publication_input_inventory(scope)
    verify_author_buffered_pollen(scope)
    verify_author_radius_sensitivity()
    radius_scope = scope["author_lra_forward_radius_sensitivity"]
    radius_report = REPOSITORY_ROOT / radius_scope["report"]
    if (
        radius_scope["prediction_freeze_sha256"]
        != json.loads(radius_report.read_text())["prediction_freeze_sha256"]
        or radius_scope["modeled_radius_factors"] != [0.8, 1.0, 1.2]
        or radius_scope["prediction_rows"] != 126
        or radius_scope["eligible_sites"] != 15
        or radius_scope["scored_sites"] != 14
        or radius_scope["paired_report"]
        != "docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/paired/report.json"
        or radius_scope["paired_rows"] != 126
        or radius_scope["aggregate_direct_lower_all_nine"] is not True
    ):
        raise ValueError("author radius scope differs from retained study")
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
    verify_swedish_landclim_support(swedish, input_manifest)

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

    verify_sambosjon_contained_age_support(scope, results)

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
