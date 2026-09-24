"""Check buffered block prediction without target count access."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial import (
    AuthorStudy,
    SiteGeometry,
    predict_block,
)
from bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.scoring import (
    _paired_comparison,
)
from bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.source import (
    _buffered_training,
    _edge_distance_km,
)


def site(name: str, grid: str, longitude: float, radius_m: float = 100) -> SiteGeometry:
    return SiteGeometry(name, grid, longitude, 0, radius_m, f"LRAready_{name}.csv")


def test_buffer_uses_both_basin_radii_and_all_target_sites() -> None:
    sites = (
        site("target_west", "512", 0),
        site("target_east", "512", 0.8),
        site("too_close", "562", 0.9),
        site("far", "562", 1.5),
    )
    assert _edge_distance_km(sites[1], sites[2]) < 20
    assert _buffered_training(sites, "512") == (sites[3],)


def test_prediction_is_unchanged_when_held_out_counts_change(tmp_path: Path) -> None:
    author = tmp_path / "author"
    working = author / "run.REVEALS.files"
    working.mkdir(parents=True)
    training = site("training", "562", 1.0)
    targets = (site("target_a", "512", 0), site("target_b", "512", 0.1))
    path = working / training.count_filename
    with path.open("w", newline="") as stream:
        csv.writer(stream).writerows(
            [
                ["TW", "50"],
                ["radius", "100"],
                ["model", "2"],
                ["Oak", "8"],
                ["Pine", "2"],
            ]
        )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    study = AuthorStudy(
        author,
        {f"author/run.REVEALS.files/{training.count_filename}": digest},
        "a" * 64,
        "b" * 64,
        "c" * 64,
        ["50"],
        ["oak", "pine"],
        ["Oak", "Pine"],
        (*targets, training),
    )
    first = predict_block(study, "512", tmp_path / "first")
    held_out = working / targets[0].count_filename
    held_out.write_text("withheld outcome 1\n")
    second = predict_block(study, "512", tmp_path / "second")
    held_out.write_text("withheld outcome 2\n")
    third = predict_block(study, "512", tmp_path / "third")
    assert first["target_count_files_opened"] == 0
    assert (
        first["predictions_sha256"]
        == second["predictions_sha256"]
        == third["predictions_sha256"]
    )
    assert (
        first["statuses_sha256"]
        == second["statuses_sha256"]
        == third["statuses_sha256"]
    )
    assert first["eligible_training_site_ids"] == ["training"]


def test_spatial_methods_use_only_buffered_training_and_distance(
    tmp_path: Path,
) -> None:
    author = tmp_path / "author"
    working = author / "run.REVEALS.files"
    working.mkdir(parents=True)
    target = site("target", "512", 0)
    training = (site("near", "562", 1), site("far", "562", 2))
    hashes = {}
    for item, oak in zip(training, (8, 2), strict=True):
        path = working / item.count_filename
        with path.open("w", newline="") as stream:
            csv.writer(stream).writerows(
                [
                    ["TW", "50"],
                    ["radius", "100"],
                    ["model", "2"],
                    ["Oak", str(oak)],
                    ["Pine", str(10 - oak)],
                ]
            )
        hashes[f"author/run.REVEALS.files/{item.count_filename}"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    study = AuthorStudy(
        author,
        hashes,
        "a" * 64,
        "b" * 64,
        "c" * 64,
        ["50"],
        ["oak", "pine"],
        ["Oak", "Pine"],
        (target, *training),
    )
    values = {}
    for method in ("training_mean", "nearest_site", "inverse_distance_squared"):
        output = tmp_path / method
        report = predict_block(study, "512", output, method)
        assert report["target_count_files_opened"] == 0
        assert report["eligible_training_site_ids"] == ["far", "near"]
        rows = list(csv.DictReader((output / "predictions.csv").open()))
        values[method] = float(
            next(row["predicted_fraction"] for row in rows if row["taxon"] == "oak")
        )
    assert abs(values["training_mean"] - 0.5) < 1e-12
    assert abs(values["nearest_site"] - 0.8) < 1e-12
    assert (
        values["training_mean"]
        < values["inverse_distance_squared"]
        < values["nearest_site"]
    )


def test_comparison_uses_only_common_scored_site_bins(tmp_path: Path) -> None:
    path = tmp_path / "within-grid.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=(
                "grid_id",
                "held_out_site_id",
                "bin_id_bp",
                "status",
                "mae_fraction",
                "total_variation",
            ),
        )
        writer.writeheader()
        for site_index in range(17):
            for bin_index in range(25):
                writer.writerow(
                    {
                        "grid_id": "512",
                        "held_out_site_id": f"S{site_index}",
                        "bin_id_bp": str(bin_index),
                        "status": "scored" if bin_index == 0 else "no_observed_count",
                        "mae_fraction": "0.1" if bin_index == 0 else "",
                        "total_variation": "0.2" if bin_index == 0 else "",
                    }
                )
    block = [
        {
            "block_grid_id": "512",
            "target_site_id": "S0",
            "bin_id_bp": "0",
            "status": "scored",
            "mae_fraction": 0.3,
            "total_variation": 0.4,
        },
        {
            "block_grid_id": "512",
            "target_site_id": "S0",
            "bin_id_bp": "1",
            "status": "no_training_site_same_bin",
            "mae_fraction": None,
            "total_variation": None,
        },
    ]
    result = _paired_comparison(block, path)
    assert result["common_scored_site_bins"] == 1
    assert result["common_sites"] == 1
    assert abs(result["spatial_minus_within_grid_mae_fraction"] - 0.2) < 1e-12
