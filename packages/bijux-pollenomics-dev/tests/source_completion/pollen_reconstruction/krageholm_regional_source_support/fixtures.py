"""Artificial native owners, with no retained measurement or source-file read."""

from __future__ import annotations

from typing import Any

from .native_rows import AGE_NAME, AGE_TYPE, TAXA, WINDOWS
from .population import IDENTITY


def fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    samples = []
    for index in range(96):
        point = -50 if index == 0 else 5700 if index == 1 else WINDOWS[index % 6][0]
        datum = [
            {
                "taxonid": identifier,
                "variablename": label,
                "value": value,
                "element": role,
                "elementtype": role,
                "units": unit,
                "context": None,
            }
            for identifier, label, value, role, unit in (
                (29, "Betula", 4, "pollen", "NISP"),
                (310, "Ulmus", 2, "pollen", "NISP"),
                (385, "Pinus", 3, "pollen", "NISP"),
                (276, "Sample volume", 2.5, "volume", "cm3"),
                (35429, "Indeterminate", 7, "pollen/spore", "NISP"),
            )
        ]
        samples.append(
            {
                "sampleid": 10000 + index,
                "analysisunitid": 20000 + index,
                "depth": index,
                "thickness": None,
                "ages": [
                    {
                        "chronologyid": 13365,
                        "chronologyname": "Fossilva",
                        "agetype": "Radiocarbon years BP",
                        "age": 1,
                        "ageyounger": None,
                        "ageolder": None,
                    },
                    {
                        "chronologyid": 13366,
                        "chronologyname": AGE_NAME,
                        "agetype": AGE_TYPE,
                        "age": point,
                        "ageyounger": None,
                        "ageolder": None,
                    },
                ],
                "datum": datum,
            }
        )
    selected = {
        "isdefault": True,
        "modelagetype": AGE_TYPE,
        "chronologyname": AGE_NAME,
        "agemodel": "synthetic selected model",
    }
    fossilva = {
        "isdefault": True,
        "modelagetype": "Radiocarbon years BP",
        "chronologyname": "Fossilva",
    }
    source = {
        "rows": [
            {
                "site": {
                    "siteid": 3204,
                    "dataset": {"datasetid": 23013},
                    "collectionunit": {
                        "collectionunitid": 16622,
                        "handle": "KRAGMJNY",
                        "defaultchronology": 13365,
                        "chronologies": [
                            {
                                "chronology": {
                                    "chronologyid": identity,
                                    "chronology": metadata,
                                    "chroncontrols": [],
                                }
                            }
                            for identity, metadata in (
                                (13365, fossilva),
                                (13366, selected),
                            )
                        ],
                        "dataset": {
                            "datasetid": 23013,
                            "datasettype": "pollen",
                            "samples": samples,
                        },
                    },
                }
            }
        ]
    }
    protocol = {
        "schema_version": "krageholm-regional-literal-panel-protocol.v1",
        "source": {
            "path": "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-005.json",
            "bytes": 1,
            "sha256": "0" * 64,
        },
        "identity": dict(IDENTITY),
        "chronology": {
            "selected_id": 13366,
            "selected_name": AGE_NAME,
            "selected_native_type": AGE_TYPE,
            "reference_epoch_ad": 1950,
            "native_collection_default_reference": 13365,
            "source_default_flags": {"13365": True, "13366": True},
        },
        "taxa": [{"label": label, "taxon_id": identity} for label, identity in TAXA],
        "windows": [list(window) for window in WINDOWS],
        "scope": "Synthetic source-support control, no observations opened",
        "suppression_semantics": "Unavailable derived aggregate, not a provider-suppression assertion",
        "rights_and_attribution": "Synthetic control, no source rights decision",
    }
    return source, protocol


def samples(source: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = source["rows"][0]["site"]["collectionunit"][
        "dataset"
    ]["samples"]
    return result
