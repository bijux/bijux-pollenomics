"""Join public core identities without inventing basin history or review."""

from __future__ import annotations

from collections import Counter
from math import isfinite
from typing import Any, cast
from urllib.parse import urlparse


def _one(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("status") != "success" or len(document.get("data", [])) != 1:
        raise ValueError("Source identity response is not uniquely successful")
    row = document["data"][0]
    if not isinstance(row, dict):
        raise ValueError("Source identity row must be an object")
    return row


def _core(core: dict[str, Any]) -> None:
    if core.get("collectionunitid") != 39241 or core.get("handle") != "BOKE":
        raise ValueError("BOKE core identity differs")


def _chronology(core: dict[str, Any]) -> dict[str, Any]:
    rows = [x["chronology"] for x in core["chronologies"]]
    selected = [x for x in rows if x["chronologyid"] == 38422]
    if len(selected) != 1:
        raise ValueError("Selected chronology identity is not unique")
    return cast(dict[str, Any], selected[0])


def _licenses(
    documents: list[dict[str, Any]], declared_dois: list[str]
) -> list[dict[str, Any]]:
    result = []
    seen = set()
    if not documents:
        raise ValueError("Dataset-specific license evidence required")
    for document in documents:
        data = document["data"]
        attributes = data["attributes"]
        doi = attributes["doi"].lower()
        route = urlparse(attributes["url"])
        if (
            data["id"].lower() != doi
            or doi in seen
            or route.hostname != "data.neotomadb.org"
            or route.path.strip("/") not in {"54001", "datasets/54001"}
        ):
            raise ValueError("DOI license does not uniquely identify pollen54001")
        seen.add(doi)
        rights = attributes["rightsList"]
        cc = [
            row
            for row in rights
            if urlparse(row.get("rightsUri", "")).hostname == "creativecommons.org"
            and urlparse(row.get("rightsUri", "")).path
            in {
                "/licenses/by/4.0/",
                "/licenses/by/4.0",
                "/licenses/by/4.0/deed.en_US",
                "/licenses/by/4.0/deed.en",
                "/licenses/by/4.0/legalcode",
                "/licenses/by/4.0/legalcode.en",
            }
        ]
        if len(cc) != 1:
            raise ValueError("Explicit CC BY4.0 license URI required")
        result.append({"doi": doi, "dataset_id": 54001, "rights": rights})
    if seen != {doi.lower() for doi in declared_dois}:
        raise ValueError("Incomplete dataset-declared DOI license evidence")
    return result


def assess_metadata(
    retained_site: dict[str, Any], sources: dict[str, Any]
) -> dict[str, Any]:
    """Authenticate same-core records and preserve control-age semantics."""
    if (
        retained_site.get("siteid") != 28872
        or retained_site.get("dataset", {}).get("datasetid") != 54001
    ):
        raise ValueError("Retained site identity differs")
    retained = retained_site["collectionunit"]
    _core(retained)
    for dataset in (retained_site["dataset"], retained.get("dataset", {})):
        if dataset.get("datasetid") != 54001 or dataset.get("datasettype") != "pollen":
            raise ValueError("Retained pollen dataset identity/type differs")
    fresh_site = _one(sources["site"])
    if fresh_site.get("siteid") != 28872:
        raise ValueError("Current site identity differs")
    expected = {54001: "pollen", 54000: "geochronologic"}
    found = []
    for row in fresh_site["collectionunits"]:
        for dataset in row["datasets"]:
            if dataset.get("datasetid") in expected:
                _core(row)
                found.append((dataset["datasetid"], dataset["datasettype"]))
    if sorted(found) != sorted(expected.items()):
        raise ValueError("Site dataset identity/type linkage differs")
    pollen_dois: list[str] = []
    for role, dataset_id in (("pollen", 54001), ("geochronologic", 54000)):
        row = _one(sources[role])["site"]
        _core(row)
        if (
            row.get("siteid") != 28872
            or len(row["datasets"]) != 1
            or row["datasets"][0]["datasetid"] != dataset_id
            or row["datasets"][0]["datasettype"] != expected[dataset_id]
        ):
            raise ValueError("Dataset metadata identity differs")
        if role == "pollen":
            pollen_dois = row["datasets"][0]["doi"]
            if not isinstance(pollen_dois, list) or not all(
                isinstance(v, str) for v in pollen_dois
            ):
                raise ValueError("Invalid dataset DOI license identity")
    current = _one(sources["dating_download"])["site"]
    if current.get("siteid") != 28872:
        raise ValueError("Dating site identity differs")
    _core(current["collectionunit"])
    if (
        current["collectionunit"]["dataset"]["datasetid"] != 54000
        or current["collectionunit"]["dataset"].get("datasettype") != "geochronologic"
    ):
        raise ValueError("Dating download dataset identity differs")
    old = _chronology(retained)
    new = _chronology(current["collectionunit"])
    if new != old:
        raise ValueError("Current chronology differs from retained pollen source")
    model = new["chronology"]
    if (
        model.get("chronologyname") != "LANDCLIM"
        or model.get("modelagetype") != "Calibrated radiocarbon years BP"
    ):
        raise ValueError("Selected chronology age identity differs")
    controls = new["chroncontrols"]
    ids = [c["chroncontrolid"] for c in controls]
    if not ids or any(type(i) is not int for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("Missing or duplicated chronological control identity")
    gps = retained.get("gpslocation") or {}
    return {
        "identity": {
            "site_id": 28872,
            "collection_unit_id": 39241,
            "handle": "BOKE",
            "pollen_dataset_id": 54001,
            "dating_dataset_id": 54000,
            "same_native_core_link": True,
        },
        "core_position": {
            "source_location": retained.get("location"),
            "native_gps": gps,
            "measured_gps_supplied": all(
                type(gps.get(k)) in (int, float)
                and isfinite(gps[k])
                and abs(gps[k]) <= limit
                for k, limit in (("latitude", 90), ("longitude", 180))
            ),
            "site_point_is_core_gps": False,
        },
        "chronology": {
            "selected_id": 38422,
            "source_model": model,
            "controls": controls,
            "control_count": len(controls),
            "control_types": dict(Counter(c["chroncontroltype"] for c in controls)),
            "control_age_types": dict(
                Counter(c["geochron"]["agetype"] for c in controls)
            ),
            "controls_match_retained_pollen": True,
            "control_ages_are_sample_uncertainty_bounds": False,
            "calibration_or_age_model_execution": False,
        },
        "rights": {
            "doi_records": _licenses(sources["doi_records"], pollen_dois),
            "public_pollen_license": "CC BY 4.0; all additional source notices retained",
            "geochronologic_license_transferred_from_pollen_doi": False,
            "private_workbook_licensed": False,
        },
        "historical_shoreline_established": False,
        "regional_representativeness_established": False,
        "qualified_review_supplied": False,
        "scientific_admission": "not_established",
        "independent_vegetation_pairs_admitted": 0,
    }
