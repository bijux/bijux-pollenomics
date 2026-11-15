"""Numerical source capture has explicit roles, versions and failure populations."""

from __future__ import annotations

import json

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourcePlan,
    NeotomaResourceSpec,
)


def spec(
    identity: int = 201,
    kind: str = "pollen",
    role: str = "development_resource_discovery",
    database: str | None = "source database",
    versions: tuple[str, ...] = ("current",),
) -> NeotomaResourceSpec:
    return NeotomaResourceSpec(
        identity,
        12,
        100,
        kind,
        database,
        role,
        "a" * 64,
        "/data/0/site/datasets/0",
        versions,
    )


def plan(*resources: NeotomaResourceSpec) -> NeotomaResourcePlan:
    return NeotomaResourcePlan(resources, "b" * 64)


def body(resource: NeotomaResourceSpec) -> bytes:
    dataset = {
        "datasetid": resource.dataset_id,
        "datasettype": resource.dataset_type,
        "database": resource.database,
    }
    samples = [
        {
            "sampleid": None if resource.dataset_type == "geochronologic" else 2001,
            "datum": [
                {
                    "taxonid": None if resource.dataset_type == "geochronologic" else 1,
                    "value": None if resource.dataset_type == "geochronologic" else 3.5,
                    "units": "%"
                    if resource.dataset_type == "loss-on-ignition"
                    else "NISP",
                }
            ],
        }
    ]
    return json.dumps(
        {
            "status": "success",
            "data": [
                {
                    "site": {
                        "siteid": 12,
                        "dataset": dict(dataset),
                        "collectionunit": {
                            "collectionunitid": 100,
                            "dataset": {**dataset, "samples": samples},
                            "chronologies": [],
                        },
                    }
                }
            ],
        }
    ).encode()


def response(url: str, content: bytes, status: int = 200) -> NeotomaMetadataResponse:
    return NeotomaMetadataResponse(
        url, status, (("Content-Length", str(len(content))),), content
    )
