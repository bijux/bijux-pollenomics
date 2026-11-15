"""Native speleothem variants keep opaque unit references and explicit nulls."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from types import ModuleType
from typing import Any

import pytest


def owner() -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.unit_resources.profiles"
    )


def scope(role: str = "development_resource_discovery") -> dict[str, Any]:
    return {
        "unit_key": "speleothem-unit-100",
        "resource_kind": "speleothem",
        "site_id": 12,
        "collection_unit_id": 100,
        "native_dataset_ids": [201, 202],
        "exposure_role": role,
    }


def payload() -> dict[str, Any]:
    return {
        "status": "success",
        "data": [
            {
                "speleothem": {
                    "siteid": 12,
                    "collectionunitid": 100,
                    "entityid": 591,
                    "entityname": "Native entity",
                    "geology": "Native geology",
                    "rockage": None,
                    "monitoring": False,
                    "speleothemtype": "Native type",
                    "speleothemdriptype": "Native drip type",
                    "dripheight": None,
                    "dripheightunits": None,
                    "entitycovertype": "Native cover",
                    "entitycoverthickness": 3,
                    "entrancedistance": 12,
                    "entrancedistanceunits": 37,
                    "landusecovertype": "Literal land use",
                    "landusecoverpercent": None,
                    "vegetationcovertype": "Literal vegetation",
                    "vegetationcoverpercent": None,
                }
            }
        ],
        "message": "Retrieved all tables",
    }


def parse(source: dict[str, Any] | None = None) -> Any:
    content = json.dumps(payload() if source is None else source).encode()
    return owner().parse_neotoma_unit_source(
        scope(), content, expected_body_sha256=sha256(content).hexdigest()
    )


def test_unit_source_preserves_every_variant_and_separates_entity_from_record_count() -> (
    None
):
    source = payload()
    source["data"].append(deepcopy(source["data"][0]))
    source["data"][1]["speleothem"]["geology"] = "Native alternative geology"
    parsed = parse(source)
    assert parsed.payload == source and len(parsed.records) == 2
    summary = owner().summarize_unit_source(parsed)
    assert summary["received_record_rows"] == 2
    assert summary["distinct_native_entity_ids"] == [591]
    assert summary["entrance_distance_unit_references"] == [37]
    assert summary["unit_reference_label_resolution"] == "not_established"
    assert summary["native_owner_verification"]["dataset"] == "not_supplied"
    assert summary["scientific_admission"] == "not_asserted"
    assert summary["physical_depth_or_chronology_inferred"] is False


@pytest.mark.parametrize("field", ["siteid", "collectionunitid", "entityid"])
@pytest.mark.parametrize("value", [True, "100", 100.0, 0])
def test_native_owner_ids_are_strict_positive_integers(field: str, value: Any) -> None:
    source = payload()
    source["data"][0]["speleothem"][field] = value
    with pytest.raises(ValueError):
        parse(source)


@pytest.mark.parametrize("field", ["siteid", "collectionunitid"])
def test_foreign_native_parent_refuses_whole_body(field: str) -> None:
    source = payload()
    source["data"].append(deepcopy(source["data"][0]))
    source["data"][1]["speleothem"][field] = 999
    with pytest.raises(ValueError):
        parse(source)


@pytest.mark.parametrize(
    "field,value",
    [
        ("entrancedistanceunits", "m"),
        ("entrancedistanceunits", True),
        ("dripheightunits", 37),
        ("monitoring", 0),
        ("entrancedistance", True),
        ("vegetationcoverpercent", "0"),
    ],
)
def test_native_unit_labels_references_booleans_and_numbers_do_not_alias(
    field: str, value: Any
) -> None:
    source = payload()
    source["data"][0]["speleothem"][field] = value
    with pytest.raises(ValueError):
        parse(source)


def test_source_null_zero_and_literal_drip_unit_remain_distinct() -> None:
    source = payload()
    row = source["data"][0]["speleothem"]
    row.update(
        vegetationcoverpercent=0, dripheight=2.5, dripheightunits="Literal native unit"
    )
    parsed = parse(source)
    summary = owner().summarize_unit_source(parsed)
    assert parsed.records[0]["vegetationcoverpercent"] == 0
    assert parsed.records[0]["landusecoverpercent"] is None
    assert parsed.records[0]["dripheightunits"] == "Literal native unit"
    assert (
        summary["reference_field_availability"]["vegetationcoverpercent"][
            "non_null_rows"
        ]
        == 1
    )
    assert (
        summary["reference_field_availability"]["landusecoverpercent"][
            "explicit_null_rows"
        ]
        == 1
    )
    assert summary["independent_vegetation_reference"] == "not_established"
    assert summary["units_interpreted"] is False


def test_missing_native_field_is_not_a_null_wrapper_or_empty_response() -> None:
    source = payload()
    del source["data"][0]["speleothem"]["vegetationcoverpercent"]
    with pytest.raises(ValueError):
        parse(source)
    source = payload()
    source["data"] = [{"speleothem": None}]
    with pytest.raises(ValueError):
        parse(source)
    source = payload()
    source["data"] = []
    with pytest.raises(ValueError, match="empty"):
        parse(source)


@pytest.mark.parametrize(
    "role", ["reserved_candidate_confirmation", "heldout_no_numerical_access"]
)
def test_protected_given_buffer_is_not_touched(role: str) -> None:
    with pytest.raises(ValueError, match="role"):
        owner().parse_neotoma_unit_source(
            scope(role), object(), expected_body_sha256="0" * 64
        )
