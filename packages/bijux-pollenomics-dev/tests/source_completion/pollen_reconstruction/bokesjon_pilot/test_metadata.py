"""Cross-source identities and dated controls must not become field acceptance."""

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.metadata import (
    assess_metadata,
)


def packet() -> tuple[dict[str, Any], dict[str, Any]]:
    model = {
        "chronologyname": "LANDCLIM",
        "modelagetype": "Calibrated radiocarbon years BP",
    }
    controls = [
        {
            "chroncontrolid": 7,
            "depth": 300,
            "chroncontrolage": 2900,
            "chroncontroltype": "Radiocarbon",
            "geochron": {"agetype": "Radiocarbon years BP"},
        }
    ]
    chrono = [
        {
            "chronology": {
                "chronologyid": 38422,
                "chronology": model,
                "chroncontrols": controls,
            }
        }
    ]
    core = {
        "collectionunitid": 39241,
        "handle": "BOKE",
        "chronologies": chrono,
        "gpslocation": {"latitude": None, "longitude": None},
        "location": "centre of the lake",
        "dataset": {"datasetid": 54001, "datasettype": "pollen"},
    }
    retained = {
        "siteid": 28872,
        "dataset": {"datasetid": 54001, "datasettype": "pollen"},
        "collectionunit": core,
    }

    def dataset(n: int, kind: str) -> dict[str, Any]:
        return {
            "status": "success",
            "data": [
                {
                    "site": {
                        "siteid": 28872,
                        "collectionunitid": 39241,
                        "handle": "BOKE",
                        "datasets": [
                            {
                                "datasetid": n,
                                "datasettype": kind,
                                "doi": ["10.21233/test"] if kind == "pollen" else [],
                            }
                        ],
                    },
                }
            ],
        }

    sources = {
        "site": {
            "status": "success",
            "data": [
                {
                    "siteid": 28872,
                    "collectionunits": [
                        {
                            "collectionunitid": 39241,
                            "handle": "BOKE",
                            "datasets": [{"datasetid": 54001, "datasettype": "pollen"}],
                        },
                        {
                            "collectionunitid": 39241,
                            "handle": "BOKE",
                            "datasets": [
                                {"datasetid": 54000, "datasettype": "geochronologic"}
                            ],
                        },
                    ],
                }
            ],
        },
        "pollen": dataset(54001, "pollen"),
        "geochronologic": dataset(54000, "geochronologic"),
        "dating_download": {
            "status": "success",
            "data": [
                {
                    "site": {
                        "siteid": 28872,
                        "collectionunit": {
                            **deepcopy(core),
                            "dataset": {
                                "datasetid": 54000,
                                "datasettype": "geochronologic",
                            },
                        },
                    }
                }
            ],
        },
        "doi_records": [
            {
                "data": {
                    "id": "10.21233/test",
                    "attributes": {
                        "doi": "10.21233/test",
                        "url": "http://data.neotomadb.org/54001",
                        "rightsList": [
                            {
                                "rights": "CC-BY4",
                                "rightsUri": "http://creativecommons.org/licenses/by/4.0/deed.en_US",
                            }
                        ],
                    },
                }
            }
        ],
    }
    return retained, sources


def test_same_core_and_public_license_do_not_admit_historical_profile() -> None:
    retained, sources = packet()
    result = assess_metadata(retained, sources)
    assert result["identity"]["pollen_dataset_id"] == 54001
    assert result["identity"]["dating_dataset_id"] == 54000
    assert result["core_position"]["measured_gps_supplied"] is False
    assert result["chronology"]["controls_match_retained_pollen"] is True
    assert result["chronology"]["control_age_types"] == {"Radiocarbon years BP": 1}
    assert result["chronology"]["control_ages_are_sample_uncertainty_bounds"] is False
    assert result["rights"]["private_workbook_licensed"] is False
    assert result["scientific_admission"] == "not_established"


@pytest.mark.parametrize(
    "part", ["site", "pollen", "geochronologic", "dating_download"]
)
def test_wrong_native_entity_refuses(part: str) -> None:
    retained, sources = packet()
    doc = sources[part]["data"][0]
    if part == "site":
        doc["collectionunits"][0]["collectionunitid"] = 999
    elif part == "dating_download":
        doc["site"]["collectionunit"]["collectionunitid"] = 999
    else:
        doc["site"]["collectionunitid"] = 999
    with pytest.raises(ValueError, match="identity"):
        assess_metadata(retained, sources)


def test_changed_control_cannot_reuse_retained_chronology_qualification() -> None:
    retained, sources = packet()
    sources["dating_download"]["data"][0]["site"]["collectionunit"]["chronologies"][0][
        "chronology"
    ]["chroncontrols"][0]["chroncontrolage"] = 3200
    with pytest.raises(ValueError, match="chronology"):
        assess_metadata(retained, sources)


def test_duplicate_control_ids_refuse_even_when_both_sources_match() -> None:
    retained, sources = packet()
    for core in (
        retained["collectionunit"],
        sources["dating_download"]["data"][0]["site"]["collectionunit"],
    ):
        items = core["chronologies"][0]["chronology"]["chroncontrols"]
        items.append(deepcopy(items[0]))
    with pytest.raises(ValueError, match="control"):
        assess_metadata(retained, sources)


def test_doi_for_another_dataset_cannot_license_boke() -> None:
    retained, sources = packet()
    sources["doi_records"][0]["data"]["attributes"]["url"] = (
        "http://data.neotomadb.org/23013"
    )
    with pytest.raises(ValueError, match="license"):
        assess_metadata(retained, sources)


def test_unrecognized_rights_uri_does_not_acquire_cc_license_by_name() -> None:
    retained, sources = packet()
    sources["doi_records"][0]["data"]["attributes"]["rightsList"][0]["rightsUri"] = (
        "https://example.com/by/4.0"
    )
    with pytest.raises(ValueError, match="license"):
        assess_metadata(retained, sources)


def test_additional_rights_notice_is_retained_without_interpretation() -> None:
    retained, sources = packet()
    notice = {"rights": "Community notice", "rightsUri": "https://example.com/notice"}
    sources["doi_records"][0]["data"]["attributes"]["rightsList"].append(notice)
    assert (
        assess_metadata(retained, sources)["rights"]["doi_records"][0]["rights"][1]
        == notice
    )


def test_retained_pollen_dataset_identity_is_required() -> None:
    retained, sources = packet()
    retained["dataset"]["datasetid"] = 23013
    with pytest.raises(ValueError, match="identity"):
        assess_metadata(retained, sources)


def test_current_datasets_url_retains_additional_notice() -> None:
    retained, sources = packet()
    sources["doi_records"][0]["data"]["attributes"]["url"] = (
        "https://data.neotomadb.org/datasets/54001"
    )
    assert (
        assess_metadata(retained, sources)["rights"]["doi_records"][0]["dataset_id"]
        == 54001
    )


def test_retained_nested_dataset_cannot_be_geochronologic() -> None:
    retained, sources = packet()
    retained["collectionunit"]["dataset"]["datasettype"] = "geochronologic"
    with pytest.raises(ValueError, match="identity"):
        assess_metadata(retained, sources)


def test_current_doi_notice_cannot_be_omitted() -> None:
    retained, sources = packet()
    sources["pollen"]["data"][0]["site"]["datasets"][0]["doi"].append(
        "10.21233/current"
    )
    with pytest.raises(ValueError, match="license"):
        assess_metadata(retained, sources)


def test_unsupported_cc_path_cannot_supply_license() -> None:
    retained, sources = packet()
    sources["doi_records"][0]["data"]["attributes"]["rightsList"][0]["rightsUri"] = (
        "https://creativecommons.org/licenses/by/4.0/not-a-license"
    )
    with pytest.raises(ValueError, match="license"):
        assess_metadata(retained, sources)


def test_invalid_gps_fields_are_not_measured_coordinates() -> None:
    retained, sources = packet()
    retained["collectionunit"]["gpslocation"] = {"latitude": "NA", "longitude": ""}
    assert (
        assess_metadata(retained, sources)["core_position"]["measured_gps_supplied"]
        is False
    )
