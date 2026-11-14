"""Frozen resource schemas are qualified from authenticated source bytes offline."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourceCapture,
    NeotomaResourcePlan,
    NeotomaResourceSpec,
    capture_neotoma_resources,
    replay_neotoma_resource_capture,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.frozen import (
    parse_neotoma_frozen_resource,
    qualify_neotoma_frozen_capture,
)


def spec() -> NeotomaResourceSpec:
    return NeotomaResourceSpec(
        201,
        12,
        100,
        "pollen",
        None,
        "development_resource_discovery",
        "a" * 64,
        "/data/0/site/datasets/0",
        ("doi_frozen",),
    )


def payload(shape: str) -> dict[str, Any]:
    dataset = {
        "datasetid": 201,
        "datasettype": "pollen",
        "database": None,
        "doi": "10.0000/source",
        "publication": {"title": "Native record"},
        "snapshotdate": "2020-01-01",
    }
    site = {"siteid": 12, "unknown_native_field": "preserve"}
    metadata: dict[str, Any]
    if shape == "dataset_wrapper":
        metadata = {
            "dataset": {"site": {**site, "collectionunitid": 100}, "dataset": dataset}
        }
    else:
        metadata = {
            "site": {
                **site,
                "collectionunit": {"collectionunitid": 100},
                "dataset": dataset,
            }
        }
    samples = [
        {
            "sampleid": 41,
            "depth": 3.0,
            "datum": [
                {
                    "variablename": "Native name",
                    "units": "NISP",
                    "value": 7,
                    "custom_datum_field": None,
                }
            ],
            "ages": [{"chronologyid": 51, "age": 150}],
        }
    ]
    chronologies = [
        {
            "chronology": {
                "chronologyid": 51,
                "chronology": {"chronologyname": "Native model"},
                "chroncontrols": [
                    {"chroncontrolid": 61, "geochron": {"geochronid": 71}},
                    {"chroncontrolid": 61, "geochron": {"geochronid": 72}},
                ],
            }
        }
    ]
    return {
        "status": "success",
        "data": [
            {
                "download": {
                    "data": {**metadata, "samples": samples},
                    "chronologies": {"chronologies": chronologies},
                }
            }
        ],
        "message": "Retrieved all tables",
    }


def encode(document: dict[str, Any]) -> bytes:
    return json.dumps(document).encode()


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


def capture(path: Path, content: bytes) -> NeotomaResourceCapture:
    return capture_neotoma_resources(
        path,
        plan=NeotomaResourcePlan((spec(),), "b" * 64),
        fetch=lambda url, **_: NeotomaMetadataResponse(
            url, 200, (("Content-Length", str(len(content))),), content
        ),
    )


def test_qualification_preserves_authenticated_unqualified_source_ledger(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    captured = capture(source, encode(payload("dataset_wrapper")))
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    row = qualified["resources"][0]
    assert row["qualification_status"] == "parsed_frozen_native"
    assert row["source_terminal_status"] == "unresolved_frozen_schema"
    assert row["summary"]["sample_rows"] == 1 and row["summary"]["datum_rows"] == 1
    assert row["summary"]["datum_rows_without_taxonid"] == 1
    assert row["summary"]["chronology_rows"] == 1
    assert row["summary"]["chroncontrol_rows"] == 2
    assert row["summary"]["distinct_identified_chroncontrols"] == 1
    assert row["summary"]["native_dataset_metadata"]["doi"] == "10.0000/source"
    assert row["summary"]["original_publication_identity"] == "not_asserted"
    assert (
        row["source"]["body_sha256"]
        == sha256(encode(payload("dataset_wrapper"))).hexdigest()
    )
    assert before == {p.name: p.read_bytes() for p in source.iterdir()}
    assert (
        replay_neotoma_resource_capture(
            source, expected_manifest_sha256=captured.manifest_sha256
        ).resources[0]["terminal_status"]
        == "unresolved_frozen_schema"
    )
    body_path = source / captured.resources[0]["attempts"][0]["body_file"]
    body_path.write_bytes(encode(payload("site_wrapper")))
    with pytest.raises(ValueError, match="identity|length"):
        qualify_neotoma_frozen_capture(
            source, expected_manifest_sha256=captured.manifest_sha256
        )


def test_qualification_follows_original_body_and_time_through_reuse(
    tmp_path: Path,
) -> None:
    original = tmp_path / "original"
    first = capture(original, encode(payload("site_wrapper")))
    reused = tmp_path / "reused"
    second = capture_neotoma_resources(
        reused,
        plan=NeotomaResourcePlan((spec(),), "b" * 64),
        reuse_from={first.manifest_sha256: original},
        fetch=lambda *_a, **_k: pytest.fail("offline reuse GET"),
    )
    qualified = qualify_neotoma_frozen_capture(
        reused,
        expected_manifest_sha256=second.manifest_sha256,
        source_captures={first.manifest_sha256: original},
    )
    source = qualified["resources"][0]["source"]
    assert source["capture_manifest_sha256"] == first.manifest_sha256
    receipt = json.loads(
        (original / first.resources[0]["attempts"][0]["receipt_file"]).read_bytes()
    )
    assert (
        source["utc_start"] == receipt["utc_start"]
        and source["utc_end"] == receipt["utc_end"]
    )


def test_malformed_frozen_bytes_are_retained_with_refused_qualification(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    captured = capture(source, b"not JSON")
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert qualified["resources"][0]["qualification_status"] == "refused_frozen_native"
    assert (
        qualified["resources"][0]["source_terminal_status"]
        == "unresolved_frozen_schema"
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


@pytest.mark.parametrize("surface", ["body_receipt", "body_only", "plan"])
def test_qualification_authenticates_buffers_consumed_after_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, surface: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import frozen

    source = tmp_path / "source"
    captured = capture(source, encode(payload("site_wrapper")))
    real_replay = replay_neotoma_resource_capture

    def mutate_after_replay(*args: Any, **kwargs: Any) -> NeotomaResourceCapture:
        result = real_replay(*args, **kwargs)
        if surface == "plan":
            path = source / "request-plan.json"
            document = json.loads(path.read_bytes())
            document["plan"]["resources"][0]["metadata_sha256"] = "c" * 64
            path.write_text(json.dumps(document))
        else:
            reference = result.resources[0]["attempts"][0]
            body_path = source / reference["body_file"]
            document = json.loads(body_path.read_bytes())
            document["data"][0]["download"]["data"]["samples"][0]["datum"] *= 2
            content = encode(document)
            body_path.write_bytes(content)
            if surface == "body_only":
                return result
            receipt_path = source / reference["receipt_file"]
            receipt = json.loads(receipt_path.read_bytes())
            receipt["retained_body_sha256"] = sha256(content).hexdigest()
            receipt["retained_body_bytes"] = len(content)
            receipt["response_headers"] = [["Content-Length", str(len(content))]]
            receipt_path.write_text(json.dumps(receipt))
        return result

    monkeypatch.setattr(frozen, "replay_neotoma_resource_capture", mutate_after_replay)
    with pytest.raises(ValueError, match="identity"):
        qualify_neotoma_frozen_capture(
            source, expected_manifest_sha256=captured.manifest_sha256
        )


def test_successful_empty_frozen_set_is_not_absence_certified(tmp_path: Path) -> None:
    source = tmp_path / "source"
    captured = capture(source, b'{"status":"success","data":[]}')
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert (
        qualified["resources"][0]["qualification_status"]
        == "unavailable_frozen_api_empty"
    )
    assert qualified["resources"][0]["absence_certified"] is False


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
