"""Native and normalized chronology guards run before pollen age-bin assignment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.materialization import api
from bijux_pollenomics_dev.source_completion import (
    nordic_direct_pollen as nordic,
)
from bijux_pollenomics_dev.source_completion import (
    swedish_direct_pollen as direct,
)
from bijux_pollenomics_dev.source_completion import (
    swedish_lake_transfer as lake_transfer,
)
from bijux_pollenomics_dev.source_completion import (
    swedish_neotoma_holdout as holdout,
)
from bijux_pollenomics_dev.source_completion import (
    swedish_pollen_sequences as sequences,
)

from .test_pollen_element_consumers import native_sources as native_sources


@pytest.mark.parametrize("consumer", ["direct", "nordic_training", "sequences"])
@pytest.mark.parametrize("point", [True, float("inf"), float("nan")])
def test_raw_response_refuses_invalid_point_before_binning_or_export(
    native_sources: tuple[Path, Path], tmp_path: Path, consumer: str, point: object
) -> None:
    raw, config = native_sources
    part = raw / "part-008.json"
    document = json.loads(part.read_bytes())
    site = next(
        w["site"]
        for w in document["rows"]
        if w["site"]["dataset"]["datasetid"] == 54001
    )
    site["collectionunit"]["dataset"]["samples"][0]["ages"][0]["age"] = point
    part.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        if consumer == "direct":
            direct.prepare(raw, tmp_path / "result", config)
        elif consumer == "nordic_training":
            nordic._swedish_training(raw)
        else:
            sequences.build(raw, tmp_path / "result")


@pytest.mark.parametrize("consumer", ["direct", "nordic_training", "sequences"])
def test_raw_response_preserves_explicit_signed_calibrated_point_policy(
    native_sources: tuple[Path, Path], tmp_path: Path, consumer: str
) -> None:
    raw, config = native_sources
    for name in ("part-004.json", "part-008.json"):
        part = raw / name
        document = json.loads(part.read_bytes())
        for row in document["rows"]:
            row["site"]["collectionunit"]["dataset"]["samples"][0]["ages"][0][
                "age"
            ] = -10
        part.write_text(json.dumps(document))
    design = json.loads(config.read_bytes())
    design["common_age_bin_ids"] = [-1]
    config.write_text(json.dumps(design))
    if consumer == "direct":
        direct.prepare(raw, tmp_path / "result", config)
        result = json.loads(
            (tmp_path / "result/prepared/dataset-54001.json").read_bytes()
        )
        assert result["age_min_cal_bp"] == -10
        assert result["bins"]["-1"]["closed_nisp_count"] == 16
    elif consumer == "nordic_training":
        profiles, _ = nordic._swedish_training(raw)
        assert profiles["54001"]["bins"]["-1"]["closed_nisp"] == 16
    else:
        sequences.build(raw, tmp_path / "result")
        samples = json.loads((tmp_path / "result/samples.json").read_bytes())
        assert all(row["calibrated_age_bp"] == -10 for row in samples)


def normalized_claim(point: object = 150) -> dict[str, Any]:
    return {
        "subject_id": "sample:one",
        "subject_type": "sample",
        "country_code": "DK",
        "chronology_claim_id": "age:one",
        "chronology_id": "chronology:one",
        "source_age_type": "Calibrated radiocarbon years BP",
        "is_default_chronology": True,
        "comparability_status": "comparable",
        "calibration_status": "calibrated",
        "source_age_value": point,
        "source_age_younger": 100,
        "source_age_older": 200,
        "younger_bp": 100,
        "older_bp": 200,
    }


def normalized_sources(root: Path, claim: dict[str, Any]) -> dict[str, Any]:
    """Write one hand-counted source slice, keeping preparation and scoring real."""
    rows: dict[str, list[dict[str, Any]]] = {
        "samples": [
            {
                "sample_id": "sample:one",
                "country_code": "DK",
                "site_id": "site:one",
                "dataset_id": "dataset:one",
                "collection_unit_id": "core:one",
            }
        ],
        "datasets": [
            {
                "dataset_id": "dataset:one",
                "country_code": "DK",
                "source_payload": {
                    "database": "European Pollen Database",
                    "datasetpi": [],
                },
            }
        ],
        "sites": [
            {
                "site_id": "site:one",
                "country_code": "DK",
                "source_payload": {
                    "sitename": "synthetic",
                    "geography": json.dumps({"type": "Point", "coordinates": [14, 56]}),
                },
            }
        ],
        "age_claims": [claim],
        "chronologies": [
            {"chronology_id": "chronology:one", "source_is_default_assertion": True}
        ],
        "observations": [
            {
                "sample_id": "sample:one",
                "source_element": "pollen",
                "source_element_type": "pollen",
                "source_unit": "NISP",
                "unit_family": "count",
                "detection_status": "reported_value",
                "source_value": 1,
                "source_reported_name": "Alnus",
            }
        ],
    }
    manifest: dict[str, Any] = {
        "source_snapshot_id": nordic.SOURCE_SNAPSHOT,
        "build_id": nordic.RELATIONAL_BUILD,
        "surfaces": {},
    }
    for name, records in rows.items():
        relative = f"surfaces/{name}/part-00001.json"
        path = root / relative
        path.parent.mkdir(parents=True)
        body = json.dumps(
            {
                "source_snapshot_id": nordic.SOURCE_SNAPSHOT,
                "build_id": nordic.RELATIONAL_BUILD,
                "rows": records,
            }
        ).encode()
        path.write_bytes(body)
        manifest["surfaces"][name] = {
            "row_count": len(records),
            "parts": [{"path": relative, "sha256": hashlib.sha256(body).hexdigest()}],
        }
    (root / "manifest.json").write_text(json.dumps(manifest))
    return {
        "selected_age_claim_ids": {"sample:one": "age:one"},
        "sites": [{"candidate_sample_ids": ["sample:one"]}],
    }


@pytest.mark.parametrize(
    "consumer", ["nordic_prepare", "nordic_score", "holdout", "lake_transfer"]
)
@pytest.mark.parametrize("point", [True, -5, 5000])
def test_comparable_response_refuses_point_outside_admitted_interval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, consumer: str, point: object
) -> None:
    claim = normalized_claim(point)
    if consumer in {"holdout", "lake_transfer"}:
        claim["country_code"] = "SE"
        with pytest.raises(ValueError):
            if consumer == "holdout":
                holdout._claims_for_samples([claim], {"sample:one": {}})
            else:
                lake_transfer._selected_claims([claim])
        return
    metadata = normalized_sources(tmp_path, claim)
    screen = {
        "candidate_sample_ids": ["sample:one"],
        "country_denominators": {
            country: {"screen_candidate_samples": int(country == "DK")}
            for country in nordic.COUNTRIES
        },
    }
    monkeypatch.setattr(
        api,
        "inspect_neotoma_lra_pollen_screen",
        lambda **_: SimpleNamespace(as_dict=lambda: screen),
    )
    with pytest.raises(ValueError):
        if consumer == "nordic_prepare":
            nordic._neotoma_candidates(tmp_path, tmp_path / "raw")
        else:
            nordic._nordic_target_outcomes(tmp_path, "DK", metadata)


@pytest.mark.parametrize("consumer", ["nordic_prepare", "nordic_score"])
def test_comparable_point_produces_the_declared_source_count_bin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, consumer: str
) -> None:
    metadata = normalized_sources(tmp_path, normalized_claim())
    screen = {
        "candidate_sample_ids": ["sample:one"],
        "country_denominators": {
            country: {"screen_candidate_samples": int(country == "DK")}
            for country in nordic.COUNTRIES
        },
    }
    monkeypatch.setattr(
        api,
        "inspect_neotoma_lra_pollen_screen",
        lambda **_: SimpleNamespace(as_dict=lambda: screen),
    )
    if consumer == "nordic_prepare":
        profiles, *_ = nordic._neotoma_candidates(tmp_path, tmp_path / "raw")
        cell = profiles["DK:site:one"]["bins"]["0"]
    else:
        result = nordic._nordic_target_outcomes(tmp_path, "DK", metadata)
        cell = result["sites"]["site:one:0"]
    assert (
        cell["counts"]["Alnus"] == cell["closed_nisp"] == cell["all_pollen_nisp"] == 1
    )
