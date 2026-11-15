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
    NeotomaRetainedSource,
    capture_neotoma_resources,
    replay_neotoma_resource_capture,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.frozen import (
    qualify_neotoma_frozen_capture,
)

from .frozen_payloads import capture, encode, payload, spec


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
