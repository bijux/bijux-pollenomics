"""Preserve nullable publication annotations without inventing author identities."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from ..test_profiles import classify, payload


def publication() -> dict[str, Any]:
    return payload("publications")


def test_nullable_primary_annotation_preserves_native_owner_and_null() -> None:
    source = publication()
    source["data"][0]["publication"]["datasets"][0]["primary"] = None
    result = classify("publications", source)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["source_payload"] == source
    assert result["owner_verification"]["dataset"] == "native_payload_matches_request"
    assert "author_population" not in result


@pytest.mark.parametrize("value", [0, 1, 1.0, "true", "false", [], {}])
def test_nullable_primary_does_not_accept_coerced_booleans(value: Any) -> None:
    source = publication()
    source["data"][0]["publication"]["datasets"][0]["primary"] = value
    assert (
        classify("publications", source)["qualification_status"]
        == "unqualified_source_schema"
    )


def test_exact_null_author_aggregate_is_raw_row_not_identified_author() -> None:
    source = publication()
    source["data"][0]["publication"]["author"] = [
        {"familyname": None, "givennames": None, "order": None}
    ]
    original = deepcopy(source)
    result = classify("publications", source)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["source_payload"] == original and source == original
    assert result["received_record_count"] == 1
    assert result["author_population"] == {
        "raw_row_count": 1,
        "identified_record_count": 0,
        "null_aggregate_row_count": 1,
        "population_status": "source_null_aggregate_placeholder",
        "absence_certified": False,
        "person_identity_asserted": False,
    }
    assert result["scientific_admission"] == "not_asserted"


@pytest.mark.parametrize(
    "mutation", ["name", "extra", "missing", "duplicate", "mixed", "bad_order"]
)
def test_partial_or_unobserved_author_placeholder_is_refused(mutation: str) -> None:
    source = publication()
    author: dict[str, Any] = {"familyname": None, "givennames": None, "order": None}
    authors = [author]
    if mutation == "name":
        author["familyname"] = "Source"
    elif mutation == "extra":
        author["contactid"] = None
    elif mutation == "missing":
        del author["givennames"]
    elif mutation == "duplicate":
        authors.append(deepcopy(author))
    elif mutation == "mixed":
        authors.append({"familyname": "Source", "givennames": "Author", "order": 1})
    else:
        author["order"] = True
    source["data"][0]["publication"]["author"] = authors
    assert (
        classify("publications", source)["qualification_status"]
        == "unqualified_source_schema"
    )


@pytest.mark.parametrize("field", ["datasetid", "siteid"])
def test_null_annotations_do_not_bypass_native_publication_owner(field: str) -> None:
    source = publication()
    record = source["data"][0]["publication"]
    record["datasets"][0].update(primary=None)
    record["datasets"][0][field] = 999999
    record["author"] = [{"familyname": None, "givennames": None, "order": None}]
    assert (
        classify("publications", source)["qualification_status"]
        == "unqualified_source_schema"
    )
