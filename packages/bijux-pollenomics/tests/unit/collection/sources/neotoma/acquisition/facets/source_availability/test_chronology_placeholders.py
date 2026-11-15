"""An exact null control aggregate remains a source placeholder, never a dated control."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from ..test_profiles import classify, payload


def control_placeholder() -> dict[str, Any]:
    return {
        "age": None,
        "agetype": None,
        "analysisunitid": None,
        "analysisunitname": None,
        "chroncontrolid": None,
        "controllimits": {"ageolder": None, "ageyounger": None},
        "controltype": None,
        "depth": None,
        "geochron": {
            "delta13c": None,
            "geochronage": {"age": None, "errorolder": None, "erroryounger": None},
            "geochronagetype": None,
            "geochronid": None,
            "geochronlabnumber": None,
            "geochrontype": None,
            "infinite": None,
            "materialdated": None,
            "notes": None,
        },
        "notes": None,
        "relativeage": {
            "c14ages": {"c14ageolder": None, "c14ageyounger": None},
            "calages": {"calageolder": None, "calageyounger": None},
            "relativeage": None,
        },
        "thickness": None,
    }


def test_exact_null_control_retains_chronology_without_identified_controls() -> None:
    source = payload("chronologies")
    source["data"][0]["chronology"]["controls"] = [control_placeholder()]
    original = deepcopy(source)
    result = classify("chronologies", source)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["source_payload"] == original and source == original
    assert result["received_record_count"] == 1
    assert result["control_population"] == {
        "raw_row_count": 1,
        "identified_record_count": 0,
        "null_aggregate_row_count": 1,
        "population_status": "source_null_aggregate_placeholder",
        "absence_certified": False,
        "dated_measurement_count": None,
    }
    assert result["chronology_selected"] is False
    assert result["owner_verification"]["dataset"] == "native_payload_matches_request"


@pytest.mark.parametrize(
    "mutation",
    ["age", "nested_age", "relative_age", "extra", "missing", "duplicate", "mixed"],
)
def test_partial_or_unobserved_null_control_is_refused(mutation: str) -> None:
    source = payload("chronologies")
    control = control_placeholder()
    controls = [control]
    if mutation == "age":
        control["age"] = 0
    elif mutation == "nested_age":
        control["geochron"]["geochronage"]["age"] = 0
    elif mutation == "relative_age":
        control["relativeage"]["relativeage"] = "native label"
    elif mutation == "extra":
        control["id"] = None
    elif mutation == "missing":
        del control["notes"]
    elif mutation == "duplicate":
        controls.append(deepcopy(control))
    else:
        controls.append(source["data"][0]["chronology"]["controls"][0])
    source["data"][0]["chronology"]["controls"] = controls
    assert (
        classify("chronologies", source)["qualification_status"]
        == "unqualified_source_schema"
    )


@pytest.mark.parametrize(
    "field,value", [("datasetid", 999999), ("datasettype", "pollen trap")]
)
def test_null_control_does_not_bypass_native_chronology_owner(
    field: str, value: Any
) -> None:
    source = payload("chronologies")
    source["data"][0]["chronology"]["controls"] = [control_placeholder()]
    source["data"][0]["chronology"]["datasets"][0][field] = value
    assert (
        classify("chronologies", source)["qualification_status"]
        == "unqualified_source_schema"
    )


def test_existing_known_empty_control_array_keeps_literal_assessment() -> None:
    source = payload("chronologies")
    source["data"][0]["chronology"]["controls"] = []
    result = classify("chronologies", source)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["received_record_count"] == 1 and "control_population" not in result
