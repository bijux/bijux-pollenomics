"""Dataset-ID metadata lookup preserves custody without opening numerical rows."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
    replay_neotoma_metadata_capture,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir


def metadata(dataset_id: object = 201, dataset_type: object = "pollen") -> bytes:
    return json.dumps(
        {
            "status": "success",
            "data": [
                {
                    "site": {
                        "siteid": 12,
                        "collectionunitid": 100,
                        "datasets": [
                            {
                                "datasetid": dataset_id,
                                "datasettype": dataset_type,
                                "database": None,
                            }
                        ],
                    }
                }
            ],
        }
    ).encode()


def response(url: str, body: bytes, status: int = 200) -> NeotomaMetadataResponse:
    return NeotomaMetadataResponse(
        url, status, (("Content-Length", str(len(body))),), body
    )


def test_dataset_metadata_lookup_binds_exact_endpoint_and_native_owner(
    tmp_path: Path,
) -> None:
    body = metadata()

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        assert url == "https://api.neotomadb.org/v2.0/data/datasets/201"
        return response(url, body)

    output = tmp_path / "capture"
    result = capture_neotoma_metadata(
        output, plan=NeotomaMetadataPlan(dataset_ids=(201,)), fetch=fetch
    )
    assert result.dataset_responses == {201: body}
    assert result.site_responses == {} and result.inventory_rows == {}
    receipt = json.loads((output / "dataset-201-metadata.receipt.json").read_bytes())
    assert receipt["expected_dataset_id"] == 201
    assert replay_neotoma_metadata_capture(
        output, expected_manifest_sha256=result.manifest_sha256
    ).dataset_responses == {201: body}


def test_successful_empty_dataset_metadata_is_retained_without_absence_claim(
    tmp_path: Path,
) -> None:
    body = b'{"status":"success","data":[]}'
    output = tmp_path / "capture"
    result = capture_neotoma_metadata(
        output,
        plan=NeotomaMetadataPlan(dataset_ids=(201,)),
        fetch=lambda url, **_: response(url, body),
    )
    assert result.dataset_responses[201] == body
    assert (output / "capture-manifest.json").is_file()


@pytest.mark.parametrize(
    "body",
    [
        metadata(999),
        metadata(True),
        metadata(201, None),
        b'{"status":"error","data":[]}',
        b'{"status":"success","data":[{"site":{"siteid":12,"collectionunitid":100,"datasets":[{"datasetid":201,"datasettype":"pollen"},{"datasetid":202,"datasettype":"pollen"}]}}]}',
        b'{"status":"success","data":[{"site":{"siteid":12,"collectionunitid":100,"datasets":[{"datasetid":201,"datasettype":"pollen","samples":[{}]}]}}]}',
    ],
)
def test_dataset_lookup_refuses_wrong_owner_type_or_numerical_payload(
    tmp_path: Path, body: bytes
) -> None:
    output = tmp_path / "capture"
    with pytest.raises(ValueError):
        capture_neotoma_metadata(
            output,
            plan=NeotomaMetadataPlan(dataset_ids=(201,)),
            fetch=lambda url, **_: response(url, body),
        )
    staging = build_staging_output_dir(output)
    assert (staging / "dataset-201-metadata.body").read_bytes() == body
    assert not (staging / "capture-manifest.json").exists()


def test_dataset_lookup_keeps_404_body_as_refusal_not_empty_metadata(
    tmp_path: Path,
) -> None:
    body = b'{"status":"error","message":"dataset not available"}'
    output = tmp_path / "capture"
    with pytest.raises(ValueError):
        capture_neotoma_metadata(
            output,
            plan=NeotomaMetadataPlan(dataset_ids=(201,)),
            fetch=lambda url, **_: response(url, body, 404),
        )
    staging = build_staging_output_dir(output)
    receipt = json.loads((staging / "dataset-201-metadata.receipt.json").read_bytes())
    assert receipt["http_status"] == 404
    assert (staging / "dataset-201-metadata.body").read_bytes() == body
    assert (staging / "refusal.json").is_file()


@pytest.mark.parametrize("ids", [(0,), (-1,), (True,), (201, 201)])
def test_dataset_lookup_validates_finite_unique_positive_roster_before_fetch(
    tmp_path: Path, ids: tuple[int, ...]
) -> None:
    with pytest.raises(ValueError):
        capture_neotoma_metadata(
            tmp_path / "capture",
            plan=NeotomaMetadataPlan(dataset_ids=ids),
            fetch=lambda *_args, **_kwargs: pytest.fail("unexpected network call"),
        )


def test_old_three_field_plan_replays_without_dataset_lookup_field(
    tmp_path: Path,
) -> None:
    body = metadata()
    output = tmp_path / "capture"
    capture_neotoma_metadata(
        output,
        plan=NeotomaMetadataPlan(site_ids=(12,)),
        fetch=lambda url, **_: response(url, body),
    )
    plan_path = output / "request-plan.json"
    plan = json.loads(plan_path.read_bytes())
    plan["plan"].pop("dataset_ids", None)
    content = json.dumps(plan).encode()
    plan_path.write_bytes(content)
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["plan_sha256"] = sha256(content).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    replay = replay_neotoma_metadata_capture(output)
    assert replay.site_responses == {12: body}
    assert replay.dataset_responses == {}
