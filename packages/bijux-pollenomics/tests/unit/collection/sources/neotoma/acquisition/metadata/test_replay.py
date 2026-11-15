from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataLimits,
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
    replay_neotoma_metadata_capture,
)

from .native_responses import SITE_BODY, response, rewrite_json


def test_metadata_replay_refuses_body_drift_without_network(tmp_path: Path) -> None:
    output = tmp_path / "capture"
    capture_neotoma_metadata(
        output,
        plan=NeotomaMetadataPlan(site_ids=(12,)),
        fetch=lambda url, **_: response(url),
    )
    (output / "site-12-datasets.body").write_bytes(b"{}")
    with pytest.raises(ValueError, match="identity"):
        replay_neotoma_metadata_capture(output)


def test_metadata_replay_enforces_callers_stricter_page_budget(tmp_path: Path) -> None:
    output = tmp_path / "capture"
    calls = []

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        calls.append(url)
        return response(
            url, SITE_BODY if len(calls) == 1 else b'{"status":"success","data":[]}'
        )

    capture_neotoma_metadata(
        output,
        plan=NeotomaMetadataPlan(
            inventory_bbox=(4.0, 54.0, 35.0, 72.0), inventory_limits=(1,)
        ),
        fetch=fetch,
    )
    with pytest.raises(ValueError, match="budget|termination"):
        replay_neotoma_metadata_capture(
            output, limits=NeotomaMetadataLimits(max_pages_per_inventory=1)
        )


@pytest.mark.parametrize(
    "malformation",
    [
        "plan_not_object",
        "limits_not_object",
        "site_ids_null",
        "site_ids_nested",
        "inventory_limits_nested",
        "unknown_plan_field",
        "record_not_object",
    ],
)
def test_metadata_replay_refuses_malformed_control_objects_with_value_error(
    tmp_path: Path, malformation: str
) -> None:
    output = tmp_path / "capture"
    capture_neotoma_metadata(
        output,
        plan=NeotomaMetadataPlan(site_ids=(12,)),
        fetch=lambda url, **_: response(url),
    )
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    plan_path = output / "request-plan.json"
    plan = json.loads(plan_path.read_bytes())
    if malformation == "plan_not_object":
        plan["plan"] = None
    elif malformation == "limits_not_object":
        plan["limits"] = []
    elif malformation == "site_ids_null":
        plan["plan"]["site_ids"] = None
    elif malformation == "site_ids_nested":
        plan["plan"]["site_ids"] = [[]]
    elif malformation == "inventory_limits_nested":
        plan["plan"]["inventory_bbox"] = [4.0, 54.0, 35.0, 72.0]
        plan["plan"]["inventory_limits"] = [[]]
    elif malformation == "unknown_plan_field":
        plan["plan"]["endpoint"] = "downloads/201"
    else:
        manifest["records"] = [None]
    manifest["plan_sha256"] = rewrite_json(plan_path, plan)
    rewrite_json(manifest_path, manifest)
    with pytest.raises(ValueError):
        replay_neotoma_metadata_capture(output)


def test_metadata_replay_refuses_backward_sequential_request_times(
    tmp_path: Path,
) -> None:
    output = tmp_path / "capture"

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        source = json.loads(SITE_BODY)
        if "/sites/13/" in url:
            source["data"][0]["site"]["siteid"] = 13
        return response(url, json.dumps(source).encode())

    capture_neotoma_metadata(
        output, plan=NeotomaMetadataPlan(site_ids=(12, 13)), fetch=fetch
    )
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    first = json.loads((output / "site-12-datasets.receipt.json").read_bytes())
    second_path = output / "site-13-datasets.receipt.json"
    second = json.loads(second_path.read_bytes())
    second["utc_start"] = manifest["capture_utc_start"]
    second["utc_end"] = first["utc_end"]
    manifest["records"][1]["receipt_sha256"] = rewrite_json(second_path, second)
    rewrite_json(manifest_path, manifest)
    with pytest.raises(ValueError, match="time|sequential"):
        replay_neotoma_metadata_capture(output)
