from __future__ import annotations

from typing import cast


def download_row(dataset_id: int = 201) -> dict[str, object]:
    chronologies = [
        {
            "chronology": {
                "chronologyid": 7001,
                "chronology": {
                    "chronologyname": "Selected model",
                    "modelagetype": "Calibrated radiocarbon years BP",
                    "isdefault": True,
                },
                "chroncontrols": [
                    {
                        "chroncontrolid": 8001,
                        "depth": 10,
                        "chroncontrolage": 1200,
                        "agelimityounger": 1150,
                        "agelimitolder": 1250,
                    }
                ],
            }
        },
        {
            "chronology": {
                "chronologyid": 7002,
                "chronology": {
                    "chronologyname": "Alternate model",
                    "modelagetype": "Radiocarbon years BP",
                    "isdefault": True,
                },
                "chroncontrols": [],
            }
        },
    ]
    return {
        "site": {
            "siteid": 20,
            "sitename": "Ageröds Mosse",
            "geography": '{"type":"Point","coordinates":[1.0,1.0]}',
            "geopolitical": [{"country": "Sweden"}],
            "dataset": {"datasetid": dataset_id, "datasettype": "pollen"},
            "collectionunit": {
                "collectionunitid": 301,
                "collectionunit": "Core A",
                "defaultchronology": 7001,
                "chronologies": chronologies,
                "dataset": {
                    "datasetid": dataset_id,
                    "datasettype": "pollen",
                    "database": "European Pollen Database",
                    "samples": [
                        {
                            "sampleid": 9001 + dataset_id,
                            "analysisunitid": 9101 + dataset_id,
                            "analysisunitname": "10 cm",
                            "depth": 10,
                            "thickness": 1,
                            "sampleanalyst": [{"contactid": 42}],
                            "ages": [
                                {
                                    "age": 1200,
                                    "ageyounger": 1150,
                                    "ageolder": 1250,
                                    "agetype": ("Calibrated radiocarbon years BP"),
                                    "chronologyid": 7001,
                                    "chronologyname": "Selected model",
                                },
                                {
                                    "age": 1100,
                                    "ageyounger": None,
                                    "ageolder": None,
                                    "agetype": "Radiocarbon years BP",
                                    "chronologyid": 7002,
                                    "chronologyname": "Alternate model",
                                },
                            ],
                            "datum": [
                                {
                                    "taxonid": 1947,
                                    "variablename": "Poaceae (Cerealia-type)",
                                    "taxongroup": "Vascular plants",
                                    "ecologicalgroup": "UPHE",
                                    "element": "pollen",
                                    "elementtype": "pollen",
                                    "units": "NISP",
                                    "value": 0,
                                    "context": None,
                                    "symmetry": None,
                                },
                                {
                                    "taxonid": 8000,
                                    "variablename": "Pollen concentration",
                                    "taxongroup": "Laboratory",
                                    "ecologicalgroup": "LABO",
                                    "element": "measurement",
                                    "elementtype": "concentration",
                                    "units": "grains/cm3",
                                    "value": 12.5,
                                    "context": "calculated",
                                    "symmetry": None,
                                },
                            ],
                        }
                    ],
                },
            },
        }
    }


def set_row_identity(row: dict[str, object], identifier: int) -> None:
    site = cast(dict[str, object], row["site"])
    site["siteid"] = identifier
    unit = cast(dict[str, object], site["collectionunit"])
    unit["collectionunitid"] = identifier + 1000
    dataset = cast(dict[str, object], unit["dataset"])
    dataset["datasetid"] = identifier + 2000
    site_dataset = cast(dict[str, object], site["dataset"])
    site_dataset["datasetid"] = identifier + 2000
    samples = cast(list[dict[str, object]], dataset["samples"])
    sample = samples[0]
    sample["sampleid"] = identifier + 3000
    sample["analysisunitid"] = identifier + 4000
