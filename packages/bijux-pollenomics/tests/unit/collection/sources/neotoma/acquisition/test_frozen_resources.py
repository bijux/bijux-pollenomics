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
    NeotomaRetainedSource,
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


def test_mixed_retained_current_and_frozen_qualification_requires_original_resolver(
    tmp_path: Path,
) -> None:
    old_spec = replace(
        spec(), dataset_id=54000, dataset_type="geochronologic", versions=("current",)
    )
    native_dataset = {
        "datasetid": 54000,
        "datasettype": "geochronologic",
        "database": None,
    }
    old_body = encode(
        {
            "status": "success",
            "data": [
                {
                    "site": {
                        "siteid": 12,
                        "dataset": native_dataset,
                        "collectionunit": {
                            "collectionunitid": 100,
                            "dataset": {
                                **native_dataset,
                                "samples": [
                                    {
                                        "sampleid": None,
                                        "datum": [{"units": None, "value": None}],
                                    }
                                ],
                            },
                        },
                    }
                }
            ],
        }
    )
    body_path, provenance_path = tmp_path / "original.body", tmp_path / "source.json"
    body_path.write_bytes(old_body)
    provenance_path.write_text(
        json.dumps(
            {
                "schema_version": "bokesjon-public-core-sources.v1",
                "sources": [
                    {
                        "source_url": "https://api.neotomadb.org/v2.0/data/downloads/54000",
                        "final_url": "https://api.neotomadb.org/v2.0/data/downloads/54000",
                        "status": 200,
                        "retrieved_at": "2026-11-14T17:32:38+00:00",
                        "bytes": len(old_body),
                        "sha256": sha256(old_body).hexdigest(),
                    }
                ],
            }
        )
    )
    retained = NeotomaRetainedSource(
        body_path,
        provenance_path,
        sha256(provenance_path.read_bytes()).hexdigest(),
        sha256(old_body).hexdigest(),
    )
    resolvers = {"dataset-54000-current": retained}
    frozen_body = encode(payload("site_wrapper"))
    source = tmp_path / "capture"
    captured = capture_neotoma_resources(
        source,
        plan=NeotomaResourcePlan((spec(), old_spec), "b" * 64),
        retained_sources=resolvers,
        fetch=lambda url, **_: NeotomaMetadataResponse(
            url, 200, (("Content-Length", str(len(frozen_body))),), frozen_body
        ),
    )
    result = qualify_neotoma_frozen_capture(
        source,
        expected_manifest_sha256=captured.manifest_sha256,
        retained_sources=resolvers,
    )
    assert result["resources"][0]["qualification_status"] == "parsed_frozen_native"
    assert len(result["resources"]) == 1 and captured.request_count == 1
    with pytest.raises(ValueError, match="resolver"):
        qualify_neotoma_frozen_capture(
            source, expected_manifest_sha256=captured.manifest_sha256
        )
    with pytest.raises(ValueError, match="identity"):
        qualify_neotoma_frozen_capture(
            source,
            expected_manifest_sha256=captured.manifest_sha256,
            retained_sources={
                "dataset-54000-current": replace(retained, body_sha256="0" * 64)
            },
        )


_NO_FROZEN_RECORD = "There is no frozen record for this dataset.  Contact Neotoma Maintainers if you believe this record should have an associated frozen record."


def test_exact_provider_frozen_unavailability_is_not_empty_or_absence_certified(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    captured = capture(
        source,
        encode(
            {
                "status": "success",
                "data": _NO_FROZEN_RECORD,
                "message": "Retrieved all tables",
            }
        ),
    )
    original = {path.name: path.read_bytes() for path in source.iterdir()}
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    row = qualified["resources"][0]
    assert row["qualification_status"] == "unavailable_frozen_record"
    assert row["absence_certified"] is False
    assert (
        row["source"]["body_sha256"]
        == sha256(
            encode(
                {
                    "status": "success",
                    "data": _NO_FROZEN_RECORD,
                    "message": "Retrieved all tables",
                }
            )
        ).hexdigest()
    )
    assert original == {path.name: path.read_bytes() for path in source.iterdir()}
    assert captured.resources[0]["terminal_status"] == "unresolved_frozen_schema"


@pytest.mark.parametrize(
    "status,message",
    [
        ("error", _NO_FROZEN_RECORD),
        (True, _NO_FROZEN_RECORD),
        ("success", "Unknown message"),
        ("success", "There is no frozen record for this dataset. invented remainder"),
        (
            "success",
            "Other text mentions no frozen record but is not an availability response",
        ),
    ],
)
def test_only_successful_exact_provider_availability_message_is_recognized(
    tmp_path: Path, status: object, message: str
) -> None:
    source = tmp_path / "source"
    captured = capture(source, encode({"status": status, "data": message}))
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert qualified["resources"][0]["qualification_status"] == "refused_frozen_native"


def test_provider_no_record_message_does_not_override_failed_http(
    tmp_path: Path,
) -> None:
    content = encode({"status": "success", "data": _NO_FROZEN_RECORD})
    source = tmp_path / "source"
    captured = capture_neotoma_resources(
        source,
        plan=NeotomaResourcePlan((spec(),), "b" * 64),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 404, (), content),
    )
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert (
        qualified["resources"][0]["qualification_status"]
        == "not_qualified_source_result"
    )
    assert qualified["resources"][0]["source_terminal_status"] == "unavailable_http"


@pytest.mark.parametrize("success", [False, 0])
def test_provider_availability_does_not_override_contradictory_success_field(
    tmp_path: Path, success: object
) -> None:
    source = tmp_path / "source"
    captured = capture(
        source,
        encode({"status": "success", "success": success, "data": _NO_FROZEN_RECORD}),
    )
    qualified = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert qualified["resources"][0]["qualification_status"] == "refused_frozen_native"


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


def test_snapshot_qualification_does_not_relabel_strict_source_binding(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import frozen

    document = payload("dataset_wrapper")
    del document["data"][0]["download"]["data"]["dataset"]["dataset"]["database"]
    source = tmp_path / "source"
    captured = capture(source, encode(document))
    before = {path.name: path.read_bytes() for path in source.iterdir()}
    strict = qualify_neotoma_frozen_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert strict["resources"][0]["qualification_status"] == "refused_frozen_native"
    snapshot = frozen.qualify_neotoma_frozen_snapshot_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert snapshot["schema_version"] == "neotoma-frozen-snapshot-qualification.v1"
    row = snapshot["resources"][0]
    assert row["qualification_status"] == "parsed_frozen_snapshot"
    assert row["strict_current_binding_status"] == "refused_database_missing"
    assert row["database_metadata"]["snapshot"] == {"field_state": "missing"}
    assert "database" not in row["summary"]
    assert row["scientific_admission"] == "not_asserted"
    assert before == {path.name: path.read_bytes() for path in source.iterdir()}


@pytest.mark.parametrize(
    "status,data,expected",
    [
        ("success", [], "unavailable_frozen_api_empty"),
        ("success", _NO_FROZEN_RECORD, "unavailable_frozen_record"),
        ("error", _NO_FROZEN_RECORD, "refused_frozen_native"),
        ("success", "Unknown message", "refused_frozen_native"),
    ],
)
def test_snapshot_availability_keeps_existing_source_error_distinctions(
    tmp_path: Path, status: str, data: object, expected: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import frozen

    source = tmp_path / "source"
    captured = capture(source, encode({"status": status, "data": data}))
    result = frozen.qualify_neotoma_frozen_snapshot_capture(
        source, expected_manifest_sha256=captured.manifest_sha256
    )
    assert result["resources"][0]["qualification_status"] == expected
