"""Check the governed Swedish training-scope experiment's exclusion and scores."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

import pytest

from bijux_pollenomics_dev.source_completion.swedish_training_scope import score

ROOT = Path(__file__).resolve().parents[4]
RESULT = ROOT / "docs/report/regions/nordic/swedish-training-scope"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compressed(path: Path) -> dict:
    return json.loads(gzip.decompress(path.read_bytes()))


def test_governed_predictors_exclude_the_whole_target_site() -> None:
    receipt = json.loads((RESULT / "prepared/prepare.json").read_text())
    freeze_path = RESULT / "frozen/freeze.json"
    freeze = json.loads(freeze_path.read_text())
    assert len(receipt["folds"]) == len(freeze["folds"]) == 6
    assert (
        _sha(freeze_path)
        == "8ff7979c370465762b0903ed1551f1b78161dade7fda60e2ed5f2ceea3182f8b"
    )
    for fold, frozen in zip(receipt["folds"], freeze["folds"], strict=True):
        assert fold["input_manifest_sha256"] == frozen["input_manifest_sha256"]
        rel = Path(fold["scope"]) / fold["site_id"]
        prepared = RESULT / "prepared" / rel
        training = _compressed(prepared / "inputs/training-SE.json.gz")
        manifest = json.loads((prepared / "input-manifest.json").read_text())
        target_id = fold["site_id"]
        assert _sha(prepared / "input-manifest.json") == fold["input_manifest_sha256"]
        assert not any(profile["site_id"] == target_id for profile in training.values())
        assert not any(
            profile["group_id"] == manifest["target_group_id"]
            for profile in training.values()
        )
        countries = [profile["country"] for profile in training.values()]
        assert countries.count("SE") == 2
        assert len(countries) == (2 if fold["scope"] == "sweden_only" else 83)
        prediction = RESULT / "frozen" / rel / "predictions-SE.json.gz"
        assert _sha(prediction) == frozen["prediction_sha256"]
        assert all(
            target_id not in row["training_site_ids"]
            for row in _compressed(prediction)["predictions"]
        )


def test_common_support_scores_match_independent_site_macro_arithmetic() -> None:
    report = json.loads((RESULT / "report.json").read_text())
    with (RESULT / "paired-scores.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 117
    assert len({(row["site_id"], row["bin_id"]) for row in rows}) == 39
    for method, scopes in report["site_macro_mae_fraction_on_common_support"].items():
        for scope, expected in scopes.items():
            by_site: dict[str, list[float]] = defaultdict(list)
            for row in rows:
                if row["method"] == method:
                    by_site[row["site_id"]].append(float(row[f"{scope}_mae_fraction"]))
            assert len(by_site) == 3
            assert mean(mean(values) for values in by_site.values()) == pytest.approx(
                expected, abs=1e-15
            )


def test_wrong_freeze_is_refused_before_scoring(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="prediction freeze digest changed"):
        score(
            RESULT / "prepared", RESULT / "frozen", "0" * 64, ROOT, tmp_path / "scores"
        )
    assert not (tmp_path / "scores").exists()
