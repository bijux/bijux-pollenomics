"""Conflicting specimen elements cannot enter native pollen responses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion import (
    nordic_direct_pollen,
    swedish_direct_pollen,
    swedish_pollen_sequences,
)


@pytest.fixture
def native_sources(tmp_path: Path) -> tuple[Path, Path]:
    raw = tmp_path / "raw"
    raw.mkdir()
    parts: dict[str, list[dict[str, Any]]] = {}
    for dataset_id, spec in swedish_direct_pollen.DATASETS.items():
        datum = [
            {
                "taxonid": index,
                "variablename": label,
                "element": "pollen",
                "elementtype": "pollen",
                "units": "NISP",
                "value": 1,
            }
            for index, label in enumerate(nordic_direct_pollen.TAXA, start=1)
        ]
        datum.append(
            {**datum[0], "taxonid": 1000, "variablename": dataset_id, "value": 2}
        )
        if dataset_id == "54001":
            datum.append({**datum[0], "element": "stomate", "value": 7})
        sample = {
            "sampleid": int(dataset_id),
            "analysisunitid": int(dataset_id),
            "samplename": "source sample",
            "sampleanalyst": [],
            "depth": 1,
            "datum": datum,
            "ages": [
                {
                    "chronologyid": 1,
                    "chronologyname": "source chronology",
                    "agetype": "Calibrated radiocarbon years BP",
                    "age": 100,
                    "ageyounger": None,
                    "ageolder": None,
                }
            ],
        }
        dataset = {
            "datasetid": int(dataset_id),
            "datasettype": "pollen",
            "database": "European Pollen Database",
            "doi": [],
            "datasetpi": [],
        }
        site = {
            "siteid": int(spec["site_id"]),
            "sitename": spec["label"],
            "geography": json.dumps({"type": "Point", "coordinates": [14, 56]}),
            "dataset": dataset,
            "collectionunit": {
                "collectionunitid": {
                    "19913": 14910,
                    "53995": 39238,
                    "54001": 39241,
                }[dataset_id],
                "handle": dataset_id,
                "colldate": None,
                "defaultchronology": 1,
                "chronologies": [
                    {
                        "chronology": {
                            "chronologyid": 1,
                            "chronology": {
                                "chronologyname": "source chronology",
                                "modelagetype": "Calibrated radiocarbon years BP",
                                "agemodel": "source model",
                            },
                            "chroncontrols": [],
                        }
                    }
                ],
                "dataset": {**dataset, "samples": [sample]},
            },
        }
        parts.setdefault(spec["part"], []).append({"site": site})
    for name, rows in parts.items():
        (raw / name).write_text(json.dumps({"rows": rows}))
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {"closed_taxa": nordic_direct_pollen.TAXA, "common_age_bin_ids": [0]}
        )
    )
    return raw, config


@pytest.mark.parametrize("consumer", ["direct", "nordic_training", "sequences"])
def test_native_pollen_response_excludes_conflicting_same_taxon_element(
    native_sources: tuple[Path, Path], tmp_path: Path, consumer: str
) -> None:
    raw, config = native_sources
    output = tmp_path / "result"
    if consumer == "direct":
        swedish_direct_pollen.prepare(raw, output, config)
        profile = json.loads((output / "prepared/dataset-54001.json").read_bytes())
        assert profile["all_nisp_count"] == 18
        assert profile["closed_nisp_count"] == 16
        assert profile["bins"]["0"]["counts"]["Alnus"] == 1
    elif consumer == "nordic_training":
        profiles, _ = nordic_direct_pollen._swedish_training(raw)
        cell = profiles["54001"]["bins"]["0"]
        assert cell["all_pollen_nisp"] == 18
        assert cell["closed_nisp"] == 16
        assert cell["counts"]["Alnus"] == 1
    else:
        swedish_pollen_sequences.build(raw, output)
        samples = json.loads((output / "samples.json").read_bytes())
        observations = json.loads((output / "observations.json").read_bytes())
        sample = next(row for row in samples if row["dataset_id"] == "54001")
        assert sample["reported_nisp_denominator"] == 18
        alnus = [
            row
            for row in observations
            if row["dataset_id"] == "54001" and row["taxon_native"] == "Alnus"
        ]
        assert len(alnus) == 1 and alnus[0]["count"] == 1
