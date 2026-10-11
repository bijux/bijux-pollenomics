"""Refuse paired development comparisons with different target observations."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPOSITORY = Path(__file__).resolve().parents[5]
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
FACTORS = ("0.8", "1.0", "1.2")
CASES = (
    "all_equal",
    "radius_differs",
    "hellinger_differs",
    "mae_differs",
    "all_distinct",
)


def _producer() -> ModuleType:
    path = (
        REPOSITORY
        / "docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/paired_comparison.py"
    )
    spec = importlib.util.spec_from_file_location("paired_radius_comparison", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _case_rows(
    case: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, Any]]]:
    scores: list[dict[str, str]] = []
    mae: list[dict[str, str]] = []
    hellinger: list[dict[str, Any]] = []
    for site in range(1, 15):
        record_id = f"synthetic-site-{site:02d}"
        for method in METHODS:
            base = _token(f"synthetic-observation:{record_id}:{method}")
            a = (
                _token("different-radius-observation")
                if case in ("radius_differs", "all_distinct")
                and site == 1
                and method == METHODS[0]
                else base
            )
            b = (
                _token("different-mae-observation")
                if case in ("mae_differs", "all_distinct")
                and site == 1
                and method == METHODS[0]
                else base
            )
            c = (
                _token("different-hellinger-observation")
                if case in ("hellinger_differs", "all_distinct")
                and site == 1
                and method == METHODS[0]
                else base
            )
            mae.append(
                {
                    "target_record_id": record_id,
                    "method": method,
                    "target_raw_sha256": b,
                    "lra_prediction_identity": f"synthetic-prediction:{record_id}:{method}",
                    "direct_pollen_mae_fraction": "0.09",
                    "lra_forward_pollen_mae_fraction": "0.10",
                }
            )
            hellinger.append(
                {
                    "target_record_id": record_id,
                    "method": method,
                    "target_raw_sha256": c,
                    "observed_total_count": 100,
                    "lra_prediction_identity": f"synthetic-prediction:{record_id}:{method}",
                    "direct_pollen_hellinger": 0.20,
                    "lra_forward_pollen_hellinger": 0.21,
                }
            )
            for factor in FACTORS:
                scores.append(
                    {
                        "record_id": record_id,
                        "method": method,
                        "observation_sha256": a if factor == "1.0" else base,
                        "observed_count": "100",
                        "radius_factor": factor,
                        "mae_fraction": "0.10" if factor == "1.0" else "0.11",
                        "hellinger_distance": "0.21" if factor == "1.0" else "0.22",
                    }
                )
    return scores, mae, hellinger


def _study(root: Path, case: str) -> tuple[Path, dict[str, str]]:
    scores, mae, hellinger = _case_rows(case)
    study = root / "author-lra-constrained/radius-sensitivity"
    paths = {
        "radius_report": study / "scored/report.json",
        "radius_scores": study / "scored/scores.csv",
        "direct_mae": study.parent / "direct-pollen/matched-scores.csv",
        "direct_hellinger": study.parent / "direct-pollen/paired-hellinger.json",
    }
    prediction = _token("synthetic-frozen-prediction-manifest")
    _write_json(
        paths["radius_report"],
        {
            "scored_sites": 14,
            "scored_rows": 126,
            "source": {"prediction_manifest_sha256": prediction},
        },
    )
    _write_csv(paths["radius_scores"], scores)
    _write_csv(paths["direct_mae"], mae)
    _write_json(
        paths["direct_hellinger"],
        {
            "matched_sites": 14,
            "matched_method_rows": 42,
            "lra_prediction_manifest_sha256": prediction,
            "site_method_rows": hellinger,
        },
    )
    return study, {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in paths.items()
    }


@pytest.mark.parametrize("case", CASES)
def test_comparison_requires_three_equal_observation_hashes(
    tmp_path: Path, case: str
) -> None:
    producer = _producer()
    study, hashes = _study(tmp_path, case)
    producer.__dict__["EXPECTED"] = hashes
    output = tmp_path / "paired-output"
    if case == "all_equal":
        producer.produce(study, output)
        report = json.loads((output / "report.json").read_text())
        with (output / "paired-scores.csv").open(newline="") as stream:
            paired = list(csv.DictReader(stream))
        assert report["matched_sites"] == 14
        assert report["paired_rows"] == len(paired) == 126
    else:
        with pytest.raises(
            ValueError, match="paired target or LRA prediction identity"
        ):
            producer.produce(study, output)
        assert not output.exists()
