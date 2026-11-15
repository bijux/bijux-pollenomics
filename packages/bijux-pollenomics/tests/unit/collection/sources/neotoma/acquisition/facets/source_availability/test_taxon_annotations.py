"""Preserve native nullable ecological annotations on identified taxa."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.facets.profiles import (
    qualify_neotoma_facet_body,
)

from ...resources.native_payloads import spec


def taxon() -> dict[str, Any]:
    return {
        "taxonid": 53018,
        "taxonname": "232Th",
        "author": None,
        "ecolgroup": None,
        "status": "extant",
        "highertaxonid": 41884,
        "publicationid": None,
        "publication": None,
    }


def qualify(row: dict[str, Any]) -> dict[str, Any]:
    raw = json.dumps(
        {"status": "success", "data": [row], "message": "Retrieved all tables"}
    ).encode()
    return qualify_neotoma_facet_body(
        spec(68269), "taxa", raw, expected_body_sha256=sha256(raw).hexdigest()
    )


def test_identified_isotope_retains_explicit_null_ecological_annotation() -> None:
    source = taxon()
    result = qualify(source)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["source_payload"]["data"] == [source]
    assert result["source_payload"]["data"][0]["ecolgroup"] is None
    assert result["received_record_count"] == 1
    assert result["population_status"] == "source_records_received"
    assert "null_aggregate_row_count" not in result
    assert (
        result["owner_verification"]["dataset"] == "authenticated_request_endpoint_only"
    )
    assert result["scientific_admission"] == "not_asserted"


@pytest.mark.parametrize("value", [False, True, 0, 1, 1.0, [], {}, ["ITOP"]])
def test_ecological_annotation_never_coerces_other_native_kinds(value: Any) -> None:
    source = taxon()
    source["ecolgroup"] = value
    result = qualify(source)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert result["source_payload"]["data"] == [source]
    assert "taxa.ecolgroup" in result["reason"]


def test_missing_ecological_annotation_remains_unqualified() -> None:
    source = taxon()
    del source["ecolgroup"]
    result = qualify(source)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert result["source_payload"]["data"] == [source]


@pytest.mark.parametrize("value", [None, True, False, 0, -1, 53018.0, "53018"])
def test_null_annotation_does_not_relax_native_taxon_identity(value: Any) -> None:
    source = taxon()
    source["taxonid"] = value
    result = qualify(source)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert result["source_payload"]["data"] == [source]


@pytest.mark.parametrize("field", ["taxonname", "status"])
@pytest.mark.parametrize("value", [None, True, 1, [], {}])
def test_other_required_taxon_text_remains_required(field: str, value: Any) -> None:
    source = taxon()
    source[field] = value
    assert qualify(source)["qualification_status"] == "unqualified_source_schema"


def test_existing_ecological_text_is_preserved() -> None:
    source = taxon()
    source.update(
        taxonid=27851, taxonname="δ13C", ecolgroup="ITOP", highertaxonid=23802
    )
    result = qualify(source)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["source_payload"]["data"] == [source]
