"""Check Swedish shifted-age and spatial-support results against frozen sources."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean

import pytest

from bijux_pollenomics_dev.source_completion.swedish_support_sensitivity import score

ROOT = Path(__file__).resolve().parents[4]
RESULT = ROOT / "docs/report/regions/nordic/swedish-support-sensitivity"
BASELINE = ROOT / "docs/report/regions/nordic/swedish-training-scope"
FREEZE_SHA = "db5bd39b7e9630b48def3ea5082ad1d93358e1e2de75c297b75933584c8a08ed"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_shifted_predictions_exclude_each_target_site() -> None:
    freeze = json.loads((RESULT / "frozen/freeze.json").read_text())
    assert _sha(RESULT / "frozen/freeze.json") == FREEZE_SHA
    assert {row["site_id"] for row in freeze["products"]} == {
        "13338",
        "28869",
        "28872",
    }
    for product in freeze["products"]:
        site_id = product["site_id"]
        path = RESULT / "frozen" / f"predictions-{site_id}.json.gz"
        assert _sha(path) == product["prediction_sha256"]
        with gzip.open(path) as stream:
            payload = json.load(stream)
        for row in payload["predictions"]:
            assert row["site_id"] == site_id
            assert site_id not in row["training_site_ids"]
            assert row["source_bin_id"] == row["target_bin_id"] + row["shift_bins"]
            assert row["target_pollen_counts_read"] is False
            if row["support_policy"] == "nearest_five":
                assert 2 <= row["training_site_count"] <= 5
            if row["support_policy"] == "beyond_100_km":
                assert row["nearest_training_distance_km"] >= 100


def test_zero_shift_full_support_reproduces_prior_scores() -> None:
    with (BASELINE / "scores.csv").open(newline="", encoding="utf-8") as stream:
        original = {
            (row["site_id"], row["bin_id"], row["method"]): row
            for row in csv.DictReader(stream)
            if row["scope"] == "four_country"
        }
    with (RESULT / "scores.csv").open(newline="", encoding="utf-8") as stream:
        current = {
            (row["site_id"], row["target_bin_id"], row["method"]): row
            for row in csv.DictReader(stream)
            if row["shift_bins"] == "0" and row["support_policy"] == "all"
        }
    assert len(original) == len(current) == 162
    assert set(original) == set(current)
    for key in original:
        assert float(current[key]["mae_fraction"]) == float(
            original[key]["mae_fraction"]
        )
        assert float(current[key]["hellinger_distance"]) == float(
            original[key]["hellinger_distance"]
        )
    report = json.loads((RESULT / "report.json").read_text())
    assert (
        report["attempted_site_policy_bins"],
        report["predicted_site_policy_bins"],
        report["refused_site_policy_bins"],
    ) == (486, 473, 13)
    with (RESULT / "paired-scores.csv").open(newline="", encoding="utf-8") as stream:
        pairs = [
            row
            for row in csv.DictReader(stream)
            if row["shift_bins"] == "1"
            and row["support_policy"] == "all"
            and row["method"] == "inverse_distance_squared"
        ]
    assert len(pairs) == 54
    per_site = {
        site_id: [row for row in pairs if row["site_id"] == site_id]
        for site_id in {row["site_id"] for row in pairs}
    }
    assert len(per_site) == 3
    paired_macro = report["paired_site_macro"]["1:all:inverse_distance_squared"]
    assert mean(
        mean(float(row["sensitivity_mae_fraction"]) for row in rows)
        for rows in per_site.values()
    ) == pytest.approx(paired_macro["sensitivity_equal_site_mae_fraction"])
    weighted = sum(
        float(row["sensitivity_mae_fraction"]) * int(row["target_sample_count"])
        for row in pairs
    ) / sum(int(row["target_sample_count"]) for row in pairs)
    assert weighted == pytest.approx(
        paired_macro["sensitivity_sample_weighted_mae_fraction"]
    )


def test_changed_freeze_is_rejected_before_target_scoring(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="prediction freeze digest changed"):
        score(
            ROOT,
            RESULT / "prepared",
            RESULT / "frozen",
            "0" * 64,
            tmp_path / "scores",
        )
    assert not (tmp_path / "scores").exists()
