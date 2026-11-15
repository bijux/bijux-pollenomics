"""Native contributor, DOI and physical-site associations keep explicit owners."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
    NeotomaFacetPlan,
)
from bijux_pollenomics.collection.sources.neotoma.capture.facets.profiles import (
    qualify_neotoma_facet_body,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourceSpec,
)

from .parent_scope.native_sources import capture_fixture, discover_fixture


def native_payload(facet: str) -> dict[str, Any]:
    contact = dict.fromkeys(
        ("url", "email", "address", "fullname", "lastname", "firstname"), None
    )
    contact.update(contactid=17, fullname="Native investigator")
    dataset = {"datasetid": 201, "datasettype": "pollen"}
    unit = {
        "handle": "NATIVE",
        "datasets": [dataset],
        "collectionunit": None,
        "collectionunitid": 301,
        "collectionunittype": "Sediment core",
    }
    site = {
        "siteid": 101,
        "sitename": "Native site",
        "sitedescription": "Source description",
        "geography": "POINT(15 60)",
        "altitude": 30,
        "recdatecreated": "2020-01-01T00:00:00",
        "collectionunits": [unit],
    }
    return {
        "status": "success",
        "data": {
            "contacts": [{"contacts": {"contacts": [contact], "datasetid": 201}}],
            "doi": [{"datasetid": 201, "dois": "10.0000/Native-DOI"}],
            "sites": [site],
        }[facet],
        "message": "Retrieved all tables",
    }


def resource() -> NeotomaResourceSpec:
    return NeotomaResourceSpec(
        201,
        101,
        301,
        "pollen",
        "Native database",
        "development_resource_discovery",
        "b" * 64,
        "/data/0/site/datasets/0",
    )


def qualify(facet: str, source: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(source).encode()
    return qualify_neotoma_facet_body(
        resource(), facet, body, expected_body_sha256=sha256(body).hexdigest()
    )


@pytest.mark.parametrize("facet", ["contacts", "doi", "sites"])
def test_native_association_shape_retains_every_source_field(facet: str) -> None:
    source = native_payload(facet)
    result = qualify(facet, source)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["received_record_count"] == 1
    assert result["source_payload"] == source
    assert result["owner_verification"]["dataset"] == "native_payload_matches_request"
    assert result["scientific_admission"] == "not_asserted"
    assert result["units_interpreted"] is False
    assert result["chronology_selected"] is False
    expected = "native_payload_matches_request" if facet == "sites" else "not_supplied"
    assert result["owner_verification"]["site"] == expected
    assert result["owner_verification"]["collection_unit"] == expected
    assert result["owner_verification"]["database"] == "not_supplied"
    if facet == "doi":
        assert result["source_payload"]["data"][0]["dois"] == "10.0000/Native-DOI"


@pytest.mark.parametrize(
    ("facet", "damage"),
    [
        ("contacts", "foreign_dataset"),
        ("contacts", "boolean_contact"),
        ("contacts", "missing_contacts"),
        ("contacts", "nontext_email"),
        ("doi", "foreign_dataset"),
        ("doi", "coerced_dataset"),
        ("doi", "nontext_doi"),
        ("sites", "foreign_site"),
        ("sites", "foreign_unit"),
        ("sites", "foreign_dataset"),
        ("sites", "foreign_type"),
        ("sites", "duplicate_unit"),
        ("sites", "missing_geography"),
        ("sites", "coerced_altitude"),
    ],
)
def test_association_shape_and_parent_mismatches_never_establish_owners(
    facet: str, damage: str
) -> None:
    source = native_payload(facet)
    assert qualify(facet, source)["qualification_status"] == "qualified_source_schema"
    row = source["data"][0]
    if facet == "contacts":
        association = row["contacts"]
        if damage == "foreign_dataset":
            association["datasetid"] = 999
        elif damage == "boolean_contact":
            association["contacts"][0]["contactid"] = True
        elif damage == "missing_contacts":
            del association["contacts"]
        else:
            association["contacts"][0]["email"] = ["native@example.invalid"]
    elif facet == "doi":
        if damage == "foreign_dataset":
            row["datasetid"] = 999
        elif damage == "coerced_dataset":
            row["datasetid"] = "201"
        else:
            row["dois"] = ["10.0000/Native-DOI"]
    elif damage == "foreign_site":
        row["siteid"] = 999
    elif damage == "foreign_unit":
        row["collectionunits"][0]["collectionunitid"] = 999
    elif damage == "foreign_dataset":
        row["collectionunits"][0]["datasets"][0]["datasetid"] = 999
    elif damage == "foreign_type":
        row["collectionunits"][0]["datasets"][0]["datasettype"] = "charcoal"
    elif damage == "duplicate_unit":
        row["collectionunits"].append(deepcopy(row["collectionunits"][0]))
    elif damage == "missing_geography":
        del row["geography"]
    else:
        row["altitude"] = "30"
    result = qualify(facet, source)
    assert result["qualification_status"] == "unqualified_source_schema"
    assert result["source_payload"] == source
    assert set(result["owner_verification"].values()) == {
        "not_verified_unqualified_source_schema"
    }


@pytest.mark.parametrize("facet", ["contacts", "doi", "sites"])
def test_empty_association_arrays_are_explicit_and_cannot_prove_native_owners(
    facet: str,
) -> None:
    source = native_payload(facet)
    source["data"] = []
    result = qualify(facet, source)
    assert result["qualification_status"] == "qualified_source_schema"
    assert result["received_record_count"] == 0
    assert result["population_status"] == "source_explicit_empty_array"
    assert set(result["owner_verification"].values()) == {"not_supplied"}


def test_contributor_link_uses_exact_authenticated_nested_contact_pointer(
    tmp_path: Path,
) -> None:
    content = json.dumps(native_payload("contacts")).encode()

    def fetch(url: str, **_kwargs: Any) -> NeotomaMetadataResponse:
        return NeotomaMetadataResponse(
            url, 200, (("Content-Length", str(len(content))),), content
        )

    directory = tmp_path / "contacts"
    capture = capture_fixture(
        directory,
        plan=NeotomaFacetPlan((resource(),), "c" * 64, ("contacts",)),
        fetch=fetch,
    )
    links = discover_fixture(
        directory, expected_manifest_sha256=capture.manifest_sha256
    )
    assert len(links["links"]) == 1
    link = links["links"][0]
    assert link["target_kind"] == "contact" and link["native_id"] == 17
    assert link["json_pointer"] == "/data/0/contacts/contacts/0/contactid"
    assert link["root_identity"]["dataset_id"] == 201
    assert link["root_identity"]["collection_unit_id"] == 301
    assert link["inherited_exposure_role"] == "development_resource_discovery"
    assert link["source_capture_manifest_sha256"] == capture.manifest_sha256
    assert link["source_body_sha256"] == sha256(content).hexdigest()
    entry = capture.facets[0]["attempts"][0]
    assert link["source_receipt_sha256"] == entry["receipt_sha256"]
