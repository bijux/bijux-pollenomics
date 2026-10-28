"""Artificial native core metadata and rows with no retained count-file access."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


def fixture(index: int = 0) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    repository = Path(__file__).resolve().parents[6]
    protocol = json.loads(
        (
            repository
            / "reports/science/pollen-reconstruction/nordic-literal-window-support/protocol.json"
        ).read_bytes()
    )
    protocol["suppression_semantics"] = (
        "Synthetic unavailable aggregate; not an observed source zero"
    )
    core = deepcopy(protocol["cores"][index])
    identity, chronology = core["identity"], core["chronology"]
    samples = []
    for row in range(identity["source_sample_count"]):
        point = [2700, 3200, 3700, 4200, 4700, 5200, 5700, -1][row % 8]
        samples.append(
            {
                "sampleid": 10000 + row,
                "analysisunitid": 20000 + row,
                "depth": row,
                "thickness": None,
                "ages": [
                    {
                        "chronologyid": chronology[
                            "native_collection_default_reference"
                        ],
                        "chronologyname": "synthetic alternate",
                        "agetype": "Radiocarbon years BP",
                        "age": 9999,
                    },
                    {
                        "chronologyid": chronology["selected_id"],
                        "chronologyname": chronology["selected_name"],
                        "agetype": chronology["selected_native_type"],
                        "age": point,
                    },
                ],
                "datum": [
                    cell("Betula", 29, 4),
                    cell("Ulmus", 310, 2),
                    cell("Pinus", 385, 3),
                    {
                        **cell("Volume", 999, 0.5),
                        "element": "volume",
                        "elementtype": "volume",
                        "units": "cm3",
                    },
                ],
            }
        )
    unit = {
        "collectionunitid": identity["collection_unit_id"],
        "handle": identity["handle"],
        "defaultchronology": chronology["native_collection_default_reference"],
        "collection_note": "synthetic preserved core description",
        "chronologies": [
            {
                "chronology": {
                    "chronologyid": code,
                    "chronology": {
                        "isdefault": flag,
                        "chronologyname": chronology["selected_name"]
                        if code == chronology["selected_id"]
                        else "synthetic alternate",
                        "modelagetype": chronology["selected_native_type"]
                        if code == chronology["selected_id"]
                        else "Radiocarbon years BP",
                    },
                    "chroncontrols": [{"control": "synthetic preserved declaration"}],
                }
            }
            for raw_code, flag in chronology["source_default_flags"].items()
            for code in [int(raw_code)]
        ],
        "dataset": {
            "datasetid": identity["dataset_id"],
            "datasettype": "pollen",
            "contacts": [{"name": "synthetic native attribution"}],
            "samples": samples,
        },
    }
    source = {
        "rows": [
            {
                "site": {
                    "siteid": identity["site_id"],
                    "sitename": "synthetic source-owned name",
                    "dataset": {
                        "datasetid": identity["dataset_id"],
                        "doi": "synthetic citation",
                    },
                    "collectionunit": unit,
                }
            }
        ]
    }
    return source, core, protocol


def cell(label: str, code: int, value: object) -> dict[str, Any]:
    return {
        "variablename": label,
        "taxonid": code,
        "value": value,
        "element": "pollen",
        "elementtype": "pollen",
        "units": "NISP",
        "context": None,
    }


def native_samples(source: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = source["rows"][0]["site"]["collectionunit"][
        "dataset"
    ]["samples"]
    return result
