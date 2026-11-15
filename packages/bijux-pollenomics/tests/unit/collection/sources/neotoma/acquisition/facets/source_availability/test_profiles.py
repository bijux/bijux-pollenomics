"""Qualify two observed empty populations while preserving native payloads."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.facets.profiles import (
    qualify_neotoma_facet_body,
)

from ...resources.native_payloads import spec

NULL_TAXA = b'{"status":"success","data":[{"taxonid":null,"taxonname":null,"author":null,"ecolgroup":null,"status":null,"highertaxonid":null,"publicationid":null,"publication":null}],"message":"Retrieved all tables"}'
EMPTY_LITHOLOGY = b'{"status":"success","data":[],"message":"Retrieved all tables"}'


def qualify(facet: str, raw: bytes) -> dict[str, Any]:
    return qualify_neotoma_facet_body(
        spec(7861 if facet == "taxa" else 10508),
        facet,
        raw,
        expected_body_sha256=sha256(raw).hexdigest(),
    )


def test_exact_null_taxon_aggregate_is_not_an_identified_taxon() -> None:
    result = qualify("taxa", NULL_TAXA)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["source_payload"] == json.loads(NULL_TAXA)
    assert result["raw_row_count"] == 1
    assert result["identified_record_count"] == result["received_record_count"] == 0
    assert result["population_status"] == "source_null_aggregate_placeholder"
    assert result["absence_certified"] is False
    assert (
        result["owner_verification"]["dataset"] == "authenticated_request_endpoint_only"
    )
    assert result["owner_verification"]["site"] == "not_supplied"
    assert result["scientific_admission"] == "not_asserted"


def test_empty_lithology_array_is_endpoint_bound_not_a_native_dataset_claim() -> None:
    result = qualify("lithology", EMPTY_LITHOLOGY)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["source_payload"] == json.loads(EMPTY_LITHOLOGY)
    assert (
        result["raw_row_count"]
        == result["identified_record_count"]
        == result["received_record_count"]
        == 0
    )
    assert result["population_status"] == "source_api_empty_array"
    assert result["absence_certified"] is False
    assert (
        result["owner_verification"]["dataset"] == "authenticated_request_endpoint_only"
    )
    assert result["owner_verification"]["collection_unit"] == "not_supplied"


@pytest.mark.parametrize(
    "field",
    [
        "taxonid",
        "taxonname",
        "author",
        "ecolgroup",
        "status",
        "highertaxonid",
        "publicationid",
        "publication",
    ],
)
def test_partially_nonnull_unidentified_taxon_is_not_relabelled_empty(
    field: str,
) -> None:
    payload = json.loads(NULL_TAXA)
    payload["data"][0][field] = 1 if field.endswith("id") else "native text"
    raw = json.dumps(payload).encode()
    result = qualify("taxa", raw)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert result["source_payload"] == payload


@pytest.mark.parametrize(
    "mutation", ["missing", "extra", "duplicate_rows", "mixed_rows", "not_array"]
)
def test_only_the_observed_exact_null_aggregate_is_qualified(mutation: str) -> None:
    payload = json.loads(NULL_TAXA)
    if mutation == "missing":
        del payload["data"][0]["publication"]
    elif mutation == "extra":
        payload["data"][0]["database"] = None
    elif mutation == "duplicate_rows":
        payload["data"].append(deepcopy(payload["data"][0]))
    elif mutation == "mixed_rows":
        payload["data"].append(
            {
                "taxonid": 1,
                "taxonname": "Native",
                "author": None,
                "ecolgroup": "UPHE",
                "status": "extant",
                "highertaxonid": None,
                "publicationid": None,
                "publication": None,
            }
        )
    else:
        payload["data"] = payload["data"][0]
    result = qualify("taxa", json.dumps(payload).encode())
    assert result["qualification_status"] == "unqualified_source_schema"
    assert result["source_payload"] == payload


@pytest.mark.parametrize(
    "facet,body", [("taxa", NULL_TAXA), ("lithology", EMPTY_LITHOLOGY)]
)
@pytest.mark.parametrize(
    "mutation", ["api_failure", "contradictory_success", "wrong_data_kind"]
)
def test_empty_shapes_do_not_bypass_source_envelope_guards(
    facet: str, body: bytes, mutation: str
) -> None:
    payload = json.loads(body)
    if mutation == "api_failure":
        payload["status"] = "failure"
    elif mutation == "contradictory_success":
        payload["success"] = False
    else:
        payload["data"] = None
    result = qualify(facet, json.dumps(payload).encode())
    assert result["qualification_status"] == "unqualified_source_schema"


def test_existing_empty_layer_wrapper_keeps_its_original_qualification() -> None:
    raw = b'{"status":"success","data":[{"datasetid":10508,"lithology":[]}],"message":"Retrieved all tables"}'
    result = qualify("lithology", raw)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["population_status"] == "source_explicit_empty_array"
    assert result["owner_verification"]["dataset"] == "native_payload_matches_request"
    assert "raw_row_count" not in result and "absence_certified" not in result
