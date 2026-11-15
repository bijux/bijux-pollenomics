"""Frozen resource schemas are qualified from authenticated source bytes offline."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.resources.frozen import (
    parse_neotoma_frozen_resource,
)

from .frozen_payloads import encode, payload, spec


@pytest.mark.parametrize("shape", ["dataset_wrapper", "site_wrapper"])
def test_frozen_shapes_preserve_native_fields_arrays_and_missing_taxon_ids(
    shape: str,
) -> None:
    document = payload(shape)
    content = encode(document)
    parsed = parse_neotoma_frozen_resource(
        spec(), content, expected_body_sha256=sha256(content).hexdigest()
    )
    assert parsed.parser_profile == f"doi_frozen_{shape}.v1"
    assert parsed.payload == document
    assert parsed.samples == document["data"][0]["download"]["data"]["samples"]
    assert "taxonid" not in parsed.samples[0]["datum"][0]
    assert (
        parsed.chronologies
        == document["data"][0]["download"]["chronologies"]["chronologies"]
    )
    assert parsed.dataset["publication"] == {"title": "Native record"}
    assert parsed.dataset["snapshotdate"] == "2020-01-01"
    assert parsed.dataset["database"] is None


@pytest.mark.parametrize(
    "mutation",
    [
        "dataset",
        "site",
        "unit",
        "type",
        "database",
        "bool_owner",
        "ambiguous_wrapper",
        "chronologies",
        "datum",
        "error",
        "duplicate",
    ],
)
def test_frozen_native_owners_and_structures_cannot_be_borrowed(mutation: str) -> None:
    document = payload("site_wrapper")
    data = document["data"][0]["download"]["data"]
    site = data["site"]
    if mutation == "dataset":
        site["dataset"]["datasetid"] = 202
    elif mutation == "site":
        site["siteid"] = 13
    elif mutation == "unit":
        site["collectionunit"]["collectionunitid"] = 101
    elif mutation == "type":
        site["dataset"]["datasettype"] = "charcoal"
    elif mutation == "database":
        site["dataset"]["database"] = "invented database"
    elif mutation == "bool_owner":
        site["dataset"]["datasetid"] = True
    elif mutation == "ambiguous_wrapper":
        data["dataset"] = {
            "site": {"siteid": 12, "collectionunitid": 100},
            "dataset": site["dataset"],
        }
    elif mutation == "chronologies":
        document["data"][0]["download"]["chronologies"]["chronologies"] = {}
    elif mutation == "datum":
        data["samples"][0]["datum"] = {}
    elif mutation == "error":
        document["status"] = "error"
    else:
        document["data"] *= 2
    content = encode(document)
    with pytest.raises(ValueError):
        parse_neotoma_frozen_resource(
            spec(), content, expected_body_sha256=sha256(content).hexdigest()
        )


def test_frozen_hash_and_exposure_are_checked_before_decoding() -> None:
    content = encode(payload("dataset_wrapper"))
    with pytest.raises(ValueError, match="identity"):
        parse_neotoma_frozen_resource(spec(), content, expected_body_sha256="0" * 64)
    with pytest.raises(ValueError, match="exposure"):
        parse_neotoma_frozen_resource(
            replace(spec(), exposure_role="heldout_no_numerical_access"),
            b"not JSON",
            expected_body_sha256=sha256(b"not JSON").hexdigest(),
        )
    with pytest.raises(ValueError):
        parse_neotoma_frozen_resource(
            spec(), b"not JSON", expected_body_sha256=sha256(b"not JSON").hexdigest()
        )


def test_frozen_expected_identity_cannot_use_boolean_equivalence() -> None:
    document = payload("site_wrapper")
    document["data"][0]["download"]["data"]["site"]["dataset"]["datasetid"] = 1
    content = encode(document)
    with pytest.raises(ValueError):
        parse_neotoma_frozen_resource(
            replace(spec(), dataset_id=True),
            content,
            expected_body_sha256=sha256(content).hexdigest(),
        )


@pytest.mark.parametrize("surface", ["chronology", "control", "units"])
def test_known_frozen_arrays_refuse_malformed_rows(surface: str) -> None:
    document = payload("site_wrapper")
    download = document["data"][0]["download"]
    if surface == "chronology":
        download["chronologies"]["chronologies"] = [{"chronology": "invalid"}]
    elif surface == "control":
        download["chronologies"]["chronologies"][0]["chronology"]["chroncontrols"] = [
            "invalid"
        ]
    else:
        download["data"]["samples"][0]["datum"][0]["units"] = {"invalid": "unit"}
    content = encode(document)
    with pytest.raises(ValueError):
        parse_neotoma_frozen_resource(
            spec(), content, expected_body_sha256=sha256(content).hexdigest()
        )


@pytest.mark.parametrize("declaration", ["nested_unit", "mirrored_dataset"])
def test_frozen_competing_native_declarations_must_agree(declaration: str) -> None:
    document = payload("dataset_wrapper")
    site = document["data"][0]["download"]["data"]["dataset"]["site"]
    if declaration == "nested_unit":
        site["collectionunit"] = {"collectionunitid": 101}
    else:
        site["dataset"] = {"datasetid": 202, "datasettype": "pollen", "database": None}
    content = encode(document)
    with pytest.raises(ValueError, match="owner|declarations"):
        parse_neotoma_frozen_resource(
            spec(), content, expected_body_sha256=sha256(content).hexdigest()
        )


@pytest.mark.parametrize(
    "state,current_database,strict_status",
    [
        ("missing", None, "refused_database_missing"),
        ("null", None, "matches_current_metadata"),
        ("value", "European Plant Macrofossil Database", "refused_database_difference"),
        ("value", "European Pollen Database", "matches_current_metadata"),
    ],
)
def test_snapshot_database_metadata_is_versioned_without_weakening_strict_parser(
    state: str, current_database: str | None, strict_status: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import frozen

    document = payload("dataset_wrapper")
    dataset = document["data"][0]["download"]["data"]["dataset"]["dataset"]
    if state == "missing":
        del dataset["database"]
    else:
        dataset["database"] = None if state == "null" else "European Pollen Database"
    resource = replace(spec(), database=current_database)
    content = encode(document)
    snapshot = frozen.parse_neotoma_frozen_snapshot(
        resource, content, expected_body_sha256=sha256(content).hexdigest()
    )
    assert snapshot.native.payload == document
    assert snapshot.database_metadata["snapshot"]["field_state"] == state
    assert snapshot.strict_current_binding_status == strict_status
    assert "taxonid" not in snapshot.native.samples[0]["datum"][0]
    if state == "missing":
        assert (
            "value" not in snapshot.database_metadata["snapshot"]
            and "database" not in snapshot.native.dataset
        )
    if strict_status.startswith("refused"):
        with pytest.raises(ValueError):
            parse_neotoma_frozen_resource(
                resource, content, expected_body_sha256=sha256(content).hexdigest()
            )
    else:
        assert (
            parse_neotoma_frozen_resource(
                resource, content, expected_body_sha256=sha256(content).hexdigest()
            ).payload
            == document
        )


@pytest.mark.parametrize("field", ["dataset", "site", "unit", "type"])
def test_snapshot_parser_still_requires_exact_native_owners(field: str) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import frozen

    document = payload("site_wrapper")
    site = document["data"][0]["download"]["data"]["site"]
    if field == "dataset":
        site["dataset"]["datasetid"] = 999
    elif field == "site":
        site["siteid"] = 999
    elif field == "unit":
        site["collectionunit"]["collectionunitid"] = 999
    else:
        site["dataset"]["datasettype"] = "charcoal"
    content = encode(document)
    with pytest.raises(ValueError):
        frozen.parse_neotoma_frozen_snapshot(
            spec(), content, expected_body_sha256=sha256(content).hexdigest()
        )


@pytest.mark.parametrize("invalid", [True, 7, [], {}])
def test_snapshot_database_value_must_be_native_text_null_or_missing(
    invalid: object,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import frozen

    document = payload("dataset_wrapper")
    document["data"][0]["download"]["data"]["dataset"]["dataset"]["database"] = invalid
    content = encode(document)
    with pytest.raises(ValueError, match="database"):
        frozen.parse_neotoma_frozen_snapshot(
            spec(), content, expected_body_sha256=sha256(content).hexdigest()
        )
