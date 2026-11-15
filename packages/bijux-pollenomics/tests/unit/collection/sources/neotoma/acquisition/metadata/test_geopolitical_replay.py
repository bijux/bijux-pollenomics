"""Geopolitical query replay binds source scope and preserves old plan bytes."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataLimits,
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
    replay_neotoma_metadata_capture,
)

from .native_responses import response, rewrite_json
from .test_geopolitical_inventory import encoded, native, plan


def test_replay_preserves_each_geopolitical_id_and_declared_view(
    tmp_path: Path,
) -> None:
    output = tmp_path / "capture"

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        scope = int(parse_qs(urlsplit(url).query)["gpid"][0])
        return response(url, encoded([native(scope)]))

    captured = capture_neotoma_metadata(output, plan=plan(), fetch=fetch)
    pins = {p.name: p.read_bytes() for p in output.iterdir()}
    replayed = replay_neotoma_metadata_capture(
        output, expected_manifest_sha256=captured.manifest_sha256
    )
    assert replayed.geopolitical_inventory_rows == {
        101: {400: [native(101)], 10000: [native(101)]},
        202: {400: [native(202)], 10000: [native(202)]},
    }
    assert replayed.inventory_rows == {}
    assert pins == {p.name: p.read_bytes() for p in output.iterdir()}


@pytest.mark.parametrize("legacy", [False, True])
def test_bbox_default_serialization_and_legacy_replay_have_no_new_query_scope(
    tmp_path: Path, legacy: bool
) -> None:
    output = tmp_path / "capture"
    capture_neotoma_metadata(
        output,
        plan=NeotomaMetadataPlan(
            inventory_bbox=(4, 54, 35, 82), inventory_limits=(400,)
        ),
        fetch=lambda url, **_: response(url, encoded([])),
    )
    path = output / "request-plan.json"
    control = json.loads(path.read_bytes())
    assert control["plan"] == {
        "inventory_bbox": [4, 54, 35, 82],
        "inventory_limits": [400],
        "site_ids": [],
        "dataset_ids": [],
        "inventory_all_dataset_types": False,
    }
    if legacy:
        del control["plan"]["dataset_ids"]
        del control["plan"]["inventory_all_dataset_types"]
        manifest_path = output / "capture-manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["plan_sha256"] = rewrite_json(path, control)
        rewrite_json(manifest_path, manifest)
    replayed = replay_neotoma_metadata_capture(output)
    assert replayed.inventory_rows == {400: []}
    assert replayed.geopolitical_inventory_rows == {}


@pytest.mark.parametrize(
    "mutation", ["gpid", "loc", "datasettype", "offset", "role", "body"]
)
def test_rehashed_receipt_cannot_substitute_scope_or_native_source(
    tmp_path: Path, mutation: str
) -> None:
    output = tmp_path / "capture"
    capture_neotoma_metadata(
        output,
        plan=plan(geopolitical_unit_ids=(101,), inventory_limits=(400,)),
        fetch=lambda url, **_: response(url, encoded([native(100)])),
    )
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    reference = manifest["records"][0]
    receipt_path = output / reference["receipt_file"]
    receipt = json.loads(receipt_path.read_bytes())
    if mutation == "body":
        (output / receipt["body_file"]).write_bytes(encoded([native(999)]))
    elif mutation == "role":
        receipt["role"] = "pollen_inventory"
    else:
        receipt["parameters"][mutation] = {
            "gpid": "202",
            "loc": "{}",
            "datasettype": "pollen",
            "offset": "400",
        }[mutation]
    reference["receipt_sha256"] = rewrite_json(receipt_path, receipt)
    rewrite_json(manifest_path, manifest)
    with pytest.raises(ValueError, match="identity"):
        replay_neotoma_metadata_capture(output)


@pytest.mark.parametrize("population", [None, 101, "101", [101, True], [[101]]])
def test_replay_rejects_malformed_geopolitical_plan_populations(
    tmp_path: Path, population: object
) -> None:
    output = tmp_path / "capture"
    capture_neotoma_metadata(
        output,
        plan=plan(geopolitical_unit_ids=(101,), inventory_limits=(400,)),
        fetch=lambda url, **_: response(url, encoded([])),
    )
    control_path = output / "request-plan.json"
    control = json.loads(control_path.read_bytes())
    control["plan"]["geopolitical_unit_ids"] = population
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["plan_sha256"] = rewrite_json(control_path, control)
    rewrite_json(manifest_path, manifest)
    with pytest.raises(ValueError):
        replay_neotoma_metadata_capture(output)


def test_replay_enforces_a_stricter_caller_page_quota(tmp_path: Path) -> None:
    output = tmp_path / "capture"

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        first = parse_qs(urlsplit(url).query)["offset"] == ["0"]
        return response(url, encoded([native(100)] if first else []))

    captured = capture_neotoma_metadata(
        output,
        plan=plan(geopolitical_unit_ids=(101,), inventory_limits=(1,)),
        fetch=fetch,
    )
    assert captured.geopolitical_inventory_rows == {101: {1: [native(100)]}}
    with pytest.raises(ValueError, match="termination|budget"):
        replay_neotoma_metadata_capture(
            output, limits=NeotomaMetadataLimits(max_pages_per_inventory=1)
        )


def test_replay_cannot_remove_geopolitical_scope_from_its_plan(tmp_path: Path) -> None:
    output = tmp_path / "capture"
    capture_neotoma_metadata(
        output,
        plan=plan(geopolitical_unit_ids=(101,), inventory_limits=(400,)),
        fetch=lambda url, **_: response(url, encoded([])),
    )
    control_path = output / "request-plan.json"
    control = json.loads(control_path.read_bytes())
    del control["plan"]["geopolitical_unit_ids"]
    manifest_path = output / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["plan_sha256"] = rewrite_json(control_path, control)
    rewrite_json(manifest_path, manifest)
    with pytest.raises(ValueError, match="scope|bbox"):
        replay_neotoma_metadata_capture(output)


@pytest.mark.parametrize("quota", ["requests", "bytes"])
def test_replay_intersects_geopolitical_limits_with_stricter_caller_quotas(
    tmp_path: Path, quota: str
) -> None:
    output = tmp_path / "capture"
    capture_neotoma_metadata(
        output,
        plan=plan(inventory_limits=(400,)),
        fetch=lambda url, **_: response(url, encoded([])),
    )
    limits = (
        NeotomaMetadataLimits(max_requests=1)
        if quota == "requests"
        else NeotomaMetadataLimits(max_total_bytes=len(encoded([])))
    )
    with pytest.raises(ValueError, match="limit|budget"):
        replay_neotoma_metadata_capture(output, limits=limits)
