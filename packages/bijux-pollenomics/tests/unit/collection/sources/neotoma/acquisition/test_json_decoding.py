"""Native source owners cannot be replaced by ambiguous JSON member decoding."""

from __future__ import annotations

from io import BytesIO
import math
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources.neotoma import client, collection
from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _object
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    capture_neotoma_resources,
    replay_neotoma_resource_capture,
)
from bijux_pollenomics.collection.sources.neotoma.site_inventory.connected_resources import (
    parse_neotoma_site_datasets,
)

from .test_resource_capture import body, plan, response, spec


@pytest.mark.parametrize(
    "content",
    [
        b'{"status":"error","status":"success","data":[]}',
        b'{"data":[],"nested":{"datasetid":999,"datasetid":201}}',
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b'{"value":-Infinity}',
        b'{"value":1e9999}',
        b'{"value":1e-9999}',
    ],
)
def test_native_json_refuses_duplicate_or_unrepresentable_values(
    content: bytes,
) -> None:
    with pytest.raises(ValueError, match="Neotoma"):
        client.decode_neotoma_json_object(content)
    with pytest.raises(ValueError, match="Neotoma"):
        _object(content)


def test_native_json_preserves_null_zero_signed_zero_labels_and_subnormal() -> None:
    content = (
        b'{"zero":0,"missing":null,"negative_zero":-0.0,"label":"NaN","small":5e-324}'
    )
    result = client.decode_neotoma_json_object(content)
    assert result["zero"] == 0 and type(result["zero"]) is int
    assert result["missing"] is None and result["label"] == "NaN"
    assert (
        result["negative_zero"] == 0 and math.copysign(1, result["negative_zero"]) == -1
    )
    assert result["small"] == 5e-324


def test_metadata_cannot_hide_an_error_status_behind_a_duplicate_success() -> None:
    with pytest.raises(ValueError, match="Neotoma"):
        parse_neotoma_site_datasets(
            12, b'{"status":"error","status":"success","data":[]}'
        )


@pytest.mark.parametrize("entrypoint", ["inventory", "download"])
def test_default_legacy_transport_refuses_duplicate_members_without_retry(
    entrypoint: str,
) -> None:
    resource = spec()
    content = (
        b'{"status":"error","status":"success","data":[]}'
        if entrypoint == "inventory"
        else body(resource).replace(
            b'"datasetid": 201', b'"datasetid": 999, "datasetid": 201'
        )
    )
    with patch(
        "bijux_pollenomics.core.http.urlopen", return_value=BytesIO(content)
    ) as network:
        with pytest.raises(ValueError, match="Neotoma"):
            if entrypoint == "inventory":
                collection.fetch_neotoma_api_rows("datasets")
            else:
                collection.fetch_neotoma_dataset_download_row(201)
        network.assert_called_once()


@pytest.mark.parametrize("corruption", ["owner", "nan", "overflow", "underflow"])
def test_resource_capture_retains_ambiguous_entity_with_explicit_refusal(
    tmp_path: Path, corruption: str
) -> None:
    resource = spec()
    original = body(resource)
    content = (
        original.replace(b'"datasetid": 201', b'"datasetid": 999, "datasetid": 201')
        if corruption == "owner"
        else original.replace(
            b'"value": 3.5',
            b'"value": '
            + {"nan": b"NaN", "overflow": b"1e9999", "underflow": b"1e-9999"}[
                corruption
            ],
        )
    )
    result = capture_neotoma_resources(
        tmp_path / "capture",
        plan=plan(resource),
        fetch=lambda url, **_: response(url, content),
    )
    assert result.resources[0]["terminal_status"] == "refused_native_protocol"
    assert (
        tmp_path / "capture/dataset-201-current-attempt-1.body"
    ).read_bytes() == content
    replayed = replay_neotoma_resource_capture(
        tmp_path / "capture", expected_manifest_sha256=result.manifest_sha256
    )
    assert replayed.resources == result.resources
