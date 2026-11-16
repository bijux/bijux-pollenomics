"""Native detail owners remain distinct from source-root relationships."""

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
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.profiles"
    )


def identity(kind: str, role: str = "development_resource_discovery") -> dict[str, Any]:
    native_id = {"contact": 8710, "publication": 9435, "taxon": 29}[kind]
    return {
        "kind": kind,
        "native_id": native_id,
        "target_key": f"{kind}-{native_id}",
        "exposure_role": role,
    }


def payload(kind: str) -> dict[str, Any]:
    if kind == "contact":
        record = dict.fromkeys(("suffix", "phone", "fax", "url", "notes"))
        record.update(
            contactid=8710,
            stewardid=3,
            contactname="Native contributor",
            familyname="Native",
            leadinginitials="N.",
            givennames="Contributor",
            title="Dr",
            email="native@example.invalid",
            address="Literal source address",
            contactstatus="active",
        )
        data = [record]
    elif kind == "taxon":
        data = [
            {
                "taxonid": 29,
                "taxoncode": "Native-code",
                "taxonname": "Native taxon",
                "author": None,
                "ecolgroup": "source-group",
                "highertaxonid": 32627,
                "status": "extant",
                "taxagroupid": "VPL",
                "publicationid": 10034,
                "publication": "Literal taxonomic reference",
            }
        ]
    else:
        assert kind == "publication"
        record = dict.fromkeys(
            (
                "issue",
                "citationnumber",
                "doi",
                "booktitle",
                "numvolumes",
                "edition",
                "volumetitle",
                "seriestitle",
                "seriesvolume",
                "publisher",
                "url",
                "city",
                "state",
                "country",
                "originallanguage",
                "notes",
            )
        )
        record.update(
            publicationid=9435,
            pubtypeid=1,
            pubtype="source type",
            year="2004",
            citation="Literal citation",
            articletitle="Native article",
            journal="Source journal",
            volume="1",
            pages="1-2",
            author=[{"order": 1, "familyname": "Native", "givennames": "Author"}],
            datasets=[
                {"siteid": 13338, "primary": True, "datasetid": 19913},
                {"siteid": 999, "primary": False, "datasetid": 888},
            ],
        )
        data = [{"publication": record}]
    return {"status": "success", "data": data, "message": "Retrieved all tables"}


def parse(kind: str, value: dict[str, Any] | None = None) -> Any:
    content = json.dumps(payload(kind) if value is None else value).encode()
    return owner().parse_neotoma_linked_source(
        identity(kind), content, expected_body_sha256=sha256(content).hexdigest()
    )


@pytest.mark.parametrize("kind", ["contact", "publication", "taxon"])
def test_expected_native_detail_preserves_payload_variants_and_partial_scope(
    kind: str,
) -> None:
    source = payload(kind)
    source["data"].append(deepcopy(source["data"][0]))
    parsed = parse(kind, source)
    assert parsed.payload == source and len(parsed.records) == 2
    assert parsed.native_id == identity(kind)["native_id"]
    summary = owner().summarize_linked_source(parsed, source_proofs=[])
    assert summary["received_record_rows"] == 2
    assert summary["scientific_admission"] == "not_asserted"
    assert summary["units_interpreted"] is False
    if kind == "publication":
        assert len(parsed.records[0]["datasets"]) == 2
        assert parsed.records[0]["doi"] is None
    if kind == "contact":
        assert parsed.records[0]["stewardid"] == 3


@pytest.mark.parametrize("kind", ["contact", "publication", "taxon"])
@pytest.mark.parametrize("bad", [True, 1.5, "29", None, 999])
def test_native_detail_identity_is_exact_and_never_coerced(kind: str, bad: Any) -> None:
    source = payload(kind)
    record = (
        source["data"][0]["publication"] if kind == "publication" else source["data"][0]
    )
    record[
        {"contact": "contactid", "publication": "publicationid", "taxon": "taxonid"}[
            kind
        ]
    ] = bad
    with pytest.raises(ValueError):
        parse(kind, source)


@pytest.mark.parametrize("kind", ["contact", "publication", "taxon"])
def test_missing_native_fields_never_become_null_or_empty(kind: str) -> None:
    source = payload(kind)
    row = (
        source["data"][0]["publication"] if kind == "publication" else source["data"][0]
    )
    del row[
        {"contact": "notes", "publication": "datasets", "taxon": "publicationid"}[kind]
    ]
    with pytest.raises(ValueError):
        parse(kind, source)
    source = payload(kind)
    source["data"] = None
    with pytest.raises(ValueError):
        parse(kind, source)


def test_publication_relationships_are_not_global_detail_identity_or_author_ids() -> (
    None
):
    parsed = parse("publication")
    proof = {
        "relation": "dataset_publication",
        "root_dataset_id": 19913,
        "root_identity": {"site_id": 13338},
        "source_facet_key": "native",
        "json_pointer": "/data/0/publication/publicationid",
    }
    summary = owner().summarize_linked_source(parsed, source_proofs=[proof])
    assert (
        summary["dataset_relation_checks"][0]["status"]
        == "confirmed_by_current_detail_body"
    )
    assert "contact_ids" not in summary
    source = payload("publication")
    source["data"][0]["publication"]["datasets"][0]["siteid"] = 42
    parsed = parse("publication", source)
    summary = owner().summarize_linked_source(parsed, source_proofs=[proof])
    assert summary["dataset_relation_checks"][0]["status"] == "conflicting_native_site"
    taxonomy = {
        **proof,
        "relation": "taxonomic_reference_publication",
        "root_dataset_id": 111,
    }
    assert (
        owner().summarize_linked_source(parsed, source_proofs=[taxonomy])[
            "dataset_relation_checks"
        ][0]["status"]
        == "not_a_dataset_publication_edge"
    )


@pytest.mark.parametrize(
    "role", ["reserved_candidate_confirmation", "heldout_no_numerical_access"]
)
def test_protected_detail_refuses_before_touching_a_given_buffer(role: str) -> None:
    with pytest.raises(ValueError, match="role"):
        owner().parse_neotoma_linked_source(
            identity("taxon", role), object(), expected_body_sha256="0" * 64
        )


def test_wrong_digest_and_unavailable_population_are_distinct() -> None:
    with pytest.raises(ValueError, match="identity"):
        owner().parse_neotoma_linked_source(
            identity("taxon"),
            json.dumps(payload("taxon")).encode(),
            expected_body_sha256="0" * 64,
        )
    source = payload("taxon")
    source["data"] = []
    with pytest.raises(ValueError, match="empty"):
        parse("taxon", source)


@pytest.mark.parametrize("kind", ["contact", "publication", "taxon"])
def test_a_late_foreign_record_cannot_be_silently_dropped(kind: str) -> None:
    source = payload(kind)
    source["data"].append(deepcopy(source["data"][0]))
    record = (
        source["data"][-1]["publication"]
        if kind == "publication"
        else source["data"][-1]
    )
    record[
        {"contact": "contactid", "publication": "publicationid", "taxon": "taxonid"}[
            kind
        ]
    ] = 999
    with pytest.raises(ValueError):
        parse(kind, source)


def test_steward_identity_and_numeric_author_order_are_not_contact_aliases() -> None:
    content = json.dumps(payload("contact")).encode()
    target = {**identity("contact"), "native_id": 3, "target_key": "contact-3"}
    with pytest.raises(ValueError):
        owner().parse_neotoma_linked_source(
            target, content, expected_body_sha256=sha256(content).hexdigest()
        )
    source = payload("publication")
    source["data"][0]["publication"]["datasets"][0]["primary"] = 1
    with pytest.raises(ValueError):
        parse("publication", source)


def test_publication_null_aggregate_is_unavailable_relationship_metadata() -> None:
    source = payload("publication")
    placeholder = {"siteid": None, "datasetid": None, "primary": None}
    source["data"][0]["publication"]["datasets"] = [placeholder]
    parsed = parse("publication", source)
    assert parsed.payload == source
    assert parsed.records[0]["datasets"] == [placeholder]
    proof = {
        "relation": "dataset_publication",
        "root_dataset_id": 19913,
        "root_identity": {"site_id": 13338},
        "source_facet_key": "native",
        "json_pointer": "/data/0/publication/publicationid",
    }
    summary = owner().summarize_linked_source(parsed, source_proofs=[proof])
    assert summary["dataset_relation_checks"][0]["status"] == (
        "source_dataset_associations_unavailable"
    )
    assert (
        summary["dataset_association_population"] == "source_null_aggregate_placeholder"
    )
    assert summary["native_records"][0]["datasets"] == [placeholder]
    assert summary["scientific_admission"] == "not_asserted"


def test_publication_null_primary_remains_unknown_with_identified_association() -> None:
    source = payload("publication")
    source["data"][0]["publication"]["datasets"][0]["primary"] = None
    parsed = parse("publication", source)
    proof = {
        "relation": "dataset_publication",
        "root_dataset_id": 19913,
        "root_identity": {"site_id": 13338},
        "source_facet_key": "native",
        "json_pointer": "/data/0/publication/publicationid",
    }
    summary = owner().summarize_linked_source(parsed, source_proofs=[proof])
    assert parsed.records[0]["datasets"][0]["primary"] is None
    assert summary["dataset_relation_checks"][0]["status"] == (
        "confirmed_by_current_detail_body"
    )
    assert (
        summary["dataset_relation_checks"][0]["primary_assertion_status"] == "unknown"
    )


@pytest.mark.parametrize(
    "rows",
    [
        [{"datasetid": None, "siteid": 13338, "primary": None}],
        [{"datasetid": 19913, "siteid": None, "primary": None}],
        [{"datasetid": None, "siteid": None, "primary": False}],
        [{"datasetid": None, "siteid": None, "primary": None}] * 2,
        [
            {"datasetid": 19913, "siteid": 13338, "primary": True},
            {"datasetid": None, "siteid": None, "primary": None},
        ],
        [{"datasetid": 19913, "siteid": 13338, "primary": "unknown"}],
        [{"datasetid": True, "siteid": 13338, "primary": None}],
        [{"datasetid": 19913.0, "siteid": 13338, "primary": None}],
    ],
)
def test_publication_unknown_primary_does_not_relax_identity_or_population(
    rows: list[dict[str, Any]],
) -> None:
    source = payload("publication")
    source["data"][0]["publication"]["datasets"] = rows
    with pytest.raises(ValueError):
        parse("publication", source)
