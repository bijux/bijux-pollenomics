"""Frozen resource schemas are qualified from authenticated source bytes offline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourceCapture,
    NeotomaResourcePlan,
    NeotomaResourceSpec,
    capture_neotoma_resources,
)

_NO_FROZEN_RECORD = "There is no frozen record for this dataset.  Contact Neotoma Maintainers if you believe this record should have an associated frozen record."


def spec() -> NeotomaResourceSpec:
    return NeotomaResourceSpec(
        201,
        12,
        100,
        "pollen",
        None,
        "development_resource_discovery",
        "a" * 64,
        "/data/0/site/datasets/0",
        ("doi_frozen",),
    )


def payload(shape: str) -> dict[str, Any]:
    dataset = {
        "datasetid": 201,
        "datasettype": "pollen",
        "database": None,
        "doi": "10.0000/source",
        "publication": {"title": "Native record"},
        "snapshotdate": "2020-01-01",
    }
    site = {"siteid": 12, "unknown_native_field": "preserve"}
    metadata: dict[str, Any]
    if shape == "dataset_wrapper":
        metadata = {
            "dataset": {"site": {**site, "collectionunitid": 100}, "dataset": dataset}
        }
    else:
        metadata = {
            "site": {
                **site,
                "collectionunit": {"collectionunitid": 100},
                "dataset": dataset,
            }
        }
    samples = [
        {
            "sampleid": 41,
            "depth": 3.0,
            "datum": [
                {
                    "variablename": "Native name",
                    "units": "NISP",
                    "value": 7,
                    "custom_datum_field": None,
                }
            ],
            "ages": [{"chronologyid": 51, "age": 150}],
        }
    ]
    chronologies = [
        {
            "chronology": {
                "chronologyid": 51,
                "chronology": {"chronologyname": "Native model"},
                "chroncontrols": [
                    {"chroncontrolid": 61, "geochron": {"geochronid": 71}},
                    {"chroncontrolid": 61, "geochron": {"geochronid": 72}},
                ],
            }
        }
    ]
    return {
        "status": "success",
        "data": [
            {
                "download": {
                    "data": {**metadata, "samples": samples},
                    "chronologies": {"chronologies": chronologies},
                }
            }
        ],
        "message": "Retrieved all tables",
    }


def encode(document: dict[str, Any]) -> bytes:
    return json.dumps(document).encode()


def capture(path: Path, content: bytes) -> NeotomaResourceCapture:
    return capture_neotoma_resources(
        path,
        plan=NeotomaResourcePlan((spec(),), "b" * 64),
        fetch=lambda url, **_: NeotomaMetadataResponse(
            url, 200, (("Content-Length", str(len(content))),), content
        ),
    )
