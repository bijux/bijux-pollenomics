"""The Swedish chronology block uses older source bins and matched targets."""

from __future__ import annotations

import csv
import gzip
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean

import pytest

from bijux_pollenomics_dev.source_completion.swedish_chronology_block import score

ROOT = Path(__file__).resolve().parents[4]
RESULT = ROOT / "docs/report/regions/nordic/swedish-chronology-block"


def test_frozen_predictions_exclude_target_site_and_adjacent_age_bins() -> None:
    preparation = json.loads((RESULT / "prepared/prepare.json").read_text())
    freeze = json.loads((RESULT / "frozen/freeze.json").read_text())
    assert preparation["older_source_bin_offset"] == 2
    assert preparation["excluded_source_bin_offsets"] == [-1, 0, 1]
    assert {product["site_id"] for product in freeze["products"]} == {
        "13338",
        "28869",
        "28872",
    }
    attempted = 0
    refused = 0
    for product in freeze["products"]:
        site_id = product["site_id"]
        prediction_path = RESULT / "frozen" / f"predictions-{site_id}.json.gz"
        assert (
            sha256(prediction_path.read_bytes()).hexdigest()
            == product["prediction_sha256"]
        )
        with gzip.open(prediction_path) as stream:
            payload = json.load(stream)
        manifest = json.loads(
            (
                ROOT
                / "docs/report/regions/nordic/swedish-training-scope/prepared/four_country"
                / site_id
                / "input-manifest.json"
            ).read_text()
        )
        predictions = payload["predictions"]
        refusals = payload["refusals"]
        bins = {row["target_bin_id"] for row in predictions}
        assert len(predictions) == 3 * len(bins)
        assert (
            len(bins) + len(refusals)
            == {"13338": 21, "28869": 20, "28872": 13}[site_id]
        )
        for row in predictions:
            target_bin = row["target_bin_id"]
            assert row["source_bin_id"] == target_bin + 2
            assert row["excluded_source_bin_ids"] == [
                target_bin - 1,
                target_bin,
                target_bin + 1,
            ]
            assert site_id not in row["training_site_ids"]
            assert manifest["target_group_id"] not in row["training_group_ids"]
            assert row["target_pollen_counts_read"] is False
            assert row["training_site_count"] >= 2
        attempted += len(bins) + len(refusals)
        refused += len(refusals)
    report = json.loads((RESULT / "report.json").read_text())
    assert (attempted, refused) == (report["attempted_bins"], report["refused_bins"])
    assert (
        report["attempted_sites"],
        report["eligible_sites"],
        report["predicted_sites"],
        report["scored_sites"],
        report["refused_sites"],
        report["failed_sites"],
    ) == (3, 3, 3, 3, 0, 0)


def test_matched_scores_keep_target_denominators_and_site_macro() -> None:
    with (RESULT / "paired-scores.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 162
    assert len({(row["site_id"], row["target_bin_id"]) for row in rows}) == 54
    assert all(
        int(row["target_assigned_nisp"]) > 0
        and int(row["target_native_nisp"]) >= int(row["target_assigned_nisp"])
        and int(row["target_sample_count"]) > 0
        for row in rows
    )
    report = json.loads((RESULT / "report.json").read_text())
    for method, aggregate in report["matched_site_macro"].items():
        selected = [row for row in rows if row["method"] == method]
        sites = sorted({row["site_id"] for row in selected})
        assert len(sites) == aggregate["scored_sites"] == 3
        assert mean(
            mean(
                float(row["chronology_block_mae_fraction"])
                for row in selected
                if row["site_id"] == site_id
            )
            for site_id in sites
        ) == pytest.approx(aggregate["block_equal_site_mae_fraction"])


def test_changed_prediction_freeze_is_refused_before_target_scoring(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="prediction freeze changed"):
        score(
            ROOT,
            RESULT / "prepared",
            RESULT / "frozen",
            "0" * 64,
            tmp_path / "scored",
        )
    assert not (tmp_path / "scored").exists()
