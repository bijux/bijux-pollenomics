"""Native proxy qualification never substitutes counts, denominators or depths."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.resources.current import (
    parse_neotoma_current_source,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.profiles import (
    classify_body,
)

from .native_payloads import payload, resource

KINDS = (
    "pollen surface sample",
    "ostracode surface sample",
    "testate amoebae surface sample",
    "speleothem",
    "dinoflagellates",
)


def parse(source: dict[str, Any], kind: str = KINDS[2]) -> Any:
    body = json.dumps(source).encode()
    return parse_neotoma_current_source(
        resource(kind), body, expected_body_sha256=sha256(body).hexdigest()
    )


@pytest.mark.parametrize("kind", KINDS)
def test_current_native_measures_are_lossless_without_changing_capture_v1(
    kind: str,
) -> None:
    spec = resource(kind)
    source = payload(spec)
    body = json.dumps(source).encode()
    original = classify_body(spec, "current", body)
    assert original[0] == "unsupported_dataset_type"
    parsed = parse(source, kind)
    assert parsed.payload == source
    assert parsed.body_sha256 == sha256(body).hexdigest()
    assert parsed.parser_profile == "current_native_proxy_hierarchy.v1"
    assert parsed.samples[0]["depth"] is None
    datums = parsed.samples[0]["datum"]
    assert datums[0]["value"] == 3.5 and type(datums[0]["value"]) is float
    assert datums[1]["units"] == "cm" and datums[1]["element"] is None
    assert datums[2]["value"] == -24.2 and datums[2]["units"] == "per mille"
    assert classify_body(spec, "current", body) == original


@pytest.mark.parametrize(
    "damage",
    [
        "site",
        "core",
        "site_dataset",
        "unit_dataset",
        "site_type",
        "unit_type",
        "database",
        "boolean_site",
        "coerced_site_dataset",
        "coerced_unit_dataset",
        "samples_missing",
        "samples_null",
        "datum_missing",
        "datum_null",
        "datum_scalar",
        "boolean_value",
        "string_value",
        "unit_object",
        "element_object",
        "coerced_native_id",
    ],
)
def test_native_parent_shapes_and_scalar_kinds_refuse_after_accepted_baseline(
    damage: str,
) -> None:
    spec = resource()
    source = payload(spec)
    assert parse(source).payload == source
    site = source["data"][0]["site"]
    unit = site["collectionunit"]
    sample = unit["dataset"]["samples"][0]
    if damage == "site":
        site["siteid"] = 999
    elif damage == "core":
        unit["collectionunitid"] = 999
    elif damage == "site_dataset":
        site["dataset"]["datasetid"] = 999
    elif damage == "unit_dataset":
        unit["dataset"]["datasetid"] = 999
    elif damage == "site_type":
        site["dataset"]["datasettype"] = "pollen"
    elif damage == "unit_type":
        unit["dataset"]["datasettype"] = "pollen"
    elif damage == "database":
        unit["dataset"]["database"] = "Another database"
    elif damage == "boolean_site":
        site["siteid"] = True
    elif damage == "coerced_site_dataset":
        site["dataset"]["datasetid"] = "201"
    elif damage == "coerced_unit_dataset":
        unit["dataset"]["datasetid"] = "201"
    elif damage == "samples_missing":
        del unit["dataset"]["samples"]
    elif damage == "samples_null":
        unit["dataset"]["samples"] = None
    elif damage == "datum_missing":
        del sample["datum"]
    elif damage == "datum_null":
        sample["datum"] = None
    elif damage == "datum_scalar":
        sample["datum"] = [7]
    elif damage == "boolean_value":
        sample["datum"][0]["value"] = True
    elif damage == "string_value":
        sample["datum"][0]["value"] = "3.5"
    elif damage == "unit_object":
        sample["datum"][0]["units"] = {"unit": "NISP"}
    elif damage == "element_object":
        sample["datum"][0]["element"] = ["test"]
    else:
        sample["datum"][0]["taxonid"] = "11"
    with pytest.raises(ValueError):
        parse(source)


def test_explicit_empty_population_remains_distinct_from_missing_and_null() -> None:
    source = payload(resource())
    source["data"][0]["site"]["collectionunit"]["dataset"]["samples"] = []
    assert parse(source).samples == []


@pytest.mark.parametrize("state", ["null", "missing"])
def test_unidentified_sample_and_variable_fields_keep_native_availability(
    state: str,
) -> None:
    source = payload(resource())
    sample = source["data"][0]["site"]["collectionunit"]["dataset"]["samples"][0]
    datum = sample["datum"][0]
    for record, key in [(sample, "sampleid"), (datum, "taxonid")]:
        if state == "null":
            record[key] = None
        else:
            del record[key]
    assert parse(source).payload == source


@pytest.mark.parametrize(
    "role", ["reserved_candidate_confirmation", "heldout_no_numerical_access"]
)
def test_protected_current_profile_refuses_before_reading_given_buffer(
    role: str,
) -> None:
    invalid_buffer: Any = object()
    with pytest.raises(ValueError, match="exposure role"):
        parse_neotoma_current_source(
            resource(exposure_role=role), invalid_buffer, expected_body_sha256="0" * 64
        )


def test_bound_identity_and_known_type_are_mandatory() -> None:
    source = payload(resource())
    body = json.dumps(source).encode()
    with pytest.raises(ValueError, match="identity"):
        parse_neotoma_current_source(resource(), body, expected_body_sha256="0" * 64)
    with pytest.raises(ValueError, match="type"):
        parse_neotoma_current_source(
            resource("unobserved native proxy"),
            body,
            expected_body_sha256=sha256(body).hexdigest(),
        )


def test_literal_presence_absence_is_not_cast_to_boolean_or_count() -> None:
    source = payload(resource("ostracode surface sample"))
    sample = source["data"][0]["site"]["collectionunit"]["dataset"]["samples"][0]
    datum = deepcopy(sample["datum"][0])
    datum.update(units="present/absent", value=0)
    sample["datum"] = [datum, {**datum, "value": 1}]
    result = parse(source, "ostracode surface sample")
    assert [x["value"] for x in result.samples[0]["datum"]] == [0, 1]
    assert all(type(x["value"]) is int for x in result.samples[0]["datum"])
