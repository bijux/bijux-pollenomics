"""Mixed native measures retain their literal identities, values and units."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourceSpec,
)


def resource(
    kind: str = "testate amoebae surface sample", **changes: Any
) -> NeotomaResourceSpec:
    return replace(
        NeotomaResourceSpec(
            201,
            12,
            100,
            kind,
            "Native database",
            "development_resource_discovery",
            "a" * 64,
            "/data/0/site/datasets/0",
            ("current",),
        ),
        **changes,
    )


def payload(spec: NeotomaResourceSpec) -> dict[str, Any]:
    metadata = {
        "datasetid": spec.dataset_id,
        "datasettype": spec.dataset_type,
        "database": spec.database,
    }
    datum = {
        "taxonid": 11,
        "variablename": "Native specimen",
        "element": "test",
        "elementtype": "test",
        "units": "NISP",
        "value": 3.5,
        "ecologicalgroup": "Native source group",
        "taxongroup": "Native source group",
        "context": None,
        "symmetry": None,
    }
    parameter = {
        **datum,
        "taxonid": 12,
        "variablename": "water table depth",
        "element": None,
        "elementtype": None,
        "units": "cm",
        "value": 7.25,
    }
    isotope = {
        **parameter,
        "taxonid": 13,
        "variablename": "delta13C",
        "units": "per mille",
        "value": -24.2,
    }
    sample = {"sampleid": 2001, "depth": None, "datum": [datum, parameter, isotope]}
    return {
        "status": "success",
        "data": [
            {
                "site": {
                    "siteid": spec.site_id,
                    "dataset": deepcopy(metadata),
                    "collectionunit": {
                        "collectionunitid": spec.collection_unit_id,
                        "dataset": {**metadata, "samples": [sample]},
                    },
                }
            }
        ],
        "message": "Retrieved all tables",
    }
