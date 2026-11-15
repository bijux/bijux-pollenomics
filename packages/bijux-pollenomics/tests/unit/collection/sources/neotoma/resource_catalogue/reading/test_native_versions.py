"""Selected native resource native versions controls."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_reader_returns_one_native_version_without_reshaping_or_other_body_reads(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    version: str,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
) -> None:
    read = resource_reader
    inputs = catalogue_sources()
    output, digest, sources = publish_catalogue(inputs)
    module = importlib.import_module(read.__module__)
    original_read: Callable[[Path, int], bytes] = module._read
    opened = []

    def tracked(path: Path, bound: int) -> bytes:
        if path.name.endswith(".body"):
            opened.append(path)
        return original_read(path, bound)

    monkeypatch.setattr(module, "_read", tracked)
    result = read(
        output,
        expected_manifest_sha256=digest,
        dataset_id=201,
        version=version,
        capture_sources=sources,
    )
    source = next(iter(inputs["resource_captures"].values()))
    expected = source / f"dataset-201-{version}-attempt-1.body"
    assert opened == [expected]
    assert result["native_payload"] == json.loads(expected.read_bytes())
    assert result["dataset_id"] == 201 and result["site_id"] == 12
    assert result["collection_unit_id"] == 100 and result["dataset_type"] == "pollen"
    assert result["exposure_role"] == "development_resource_discovery"
    assert result["scientific_admission"] == "not_asserted"
    assert result["source_units"] == ["NISP"]
    assert result["version"] == version
    assert result["epoch_kind"] == (
        "timed_live_api_response"
        if version == "current"
        else "provider_frozen_response"
    )
    assert result["source"]["body_sha256"] == sha256(expected.read_bytes()).hexdigest()
    if version == "current":
        assert "site" in result["native_payload"]["data"][0]
    else:
        assert "download" in result["native_payload"]["data"][0]
        assert result["strict_current_binding_status"] == "matches_current_metadata"
        assert (
            "taxonid"
            not in result["native_payload"]["data"][0]["download"]["data"]["samples"][
                0
            ]["datum"][0]
        )


@pytest.mark.parametrize("snapshot_database", ["Historical database", None])
def test_frozen_snapshot_preserves_database_difference_and_missing_field(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    snapshot_database: str | None,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
) -> None:
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.capture import (
        NeotomaMetadataResponse,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
        NeotomaResourcePlan,
        capture_neotoma_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.protocol import (
        plan_from_json,
    )

    read = resource_reader
    inputs = catalogue_sources()
    source = next(iter(inputs["resource_captures"].values()))
    plan, _ = plan_from_json(json.loads((source / "request-plan.json").read_bytes()))
    payload = json.loads(
        (source / "dataset-201-doi_frozen-attempt-1.body").read_bytes()
    )
    dataset = payload["data"][0]["download"]["data"]["site"]["dataset"]
    if snapshot_database is None:
        del dataset["database"]
    else:
        dataset["database"] = snapshot_database
    body = json.dumps(payload).encode()
    frozen = tmp_path / "snapshot"
    captured = capture_neotoma_resources(
        frozen,
        plan=NeotomaResourcePlan(
            (replace(plan.resources[0], versions=("doi_frozen",)),), plan.roster_sha256
        ),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 200, (), body),
    )
    inputs["resource_captures"] = {captured.manifest_sha256: frozen}
    output, digest, sources = publish_catalogue(inputs)
    result = read(
        output,
        expected_manifest_sha256=digest,
        dataset_id=201,
        version="doi_frozen",
        capture_sources=sources,
    )
    assert result["native_payload"] == payload
    assert result["strict_current_binding_status"] == (
        "refused_database_missing"
        if snapshot_database is None
        else "refused_database_difference"
    )
    actual_dataset = result["native_payload"]["data"][0]["download"]["data"]["site"][
        "dataset"
    ]
    if snapshot_database is None:
        assert "database" not in actual_dataset
    else:
        assert actual_dataset["database"] == snapshot_database


@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_reader_derives_source_units_from_authenticated_native_buffer(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    version: str,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
) -> None:
    read = resource_reader
    output, _, sources = publish_catalogue(catalogue_sources())
    path = output / "catalogue.json"
    catalogue = json.loads(path.read_bytes())
    catalogue["resources"][0]["versions"][version]["native_counts"]["source_units"] = [
        "invented units"
    ]
    path.write_text(json.dumps(catalogue))
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"]["catalogue.json"] = sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    result = read(
        output,
        expected_manifest_sha256=sha256(manifest_path.read_bytes()).hexdigest(),
        dataset_id=201,
        version=version,
        capture_sources=sources,
    )
    assert result["source_units"] == ["NISP"]


def test_frozen_availability_refusal_reports_qualified_provider_status_before_body_access(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
    no_outcome_resolver: dict[str, Path],
) -> None:
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.capture import (
        NeotomaMetadataResponse,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
        NeotomaResourcePlan,
        capture_neotoma_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.frozen import (
        _NO_FROZEN_RECORD,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.protocol import (
        plan_from_json,
    )

    read = resource_reader
    inputs = catalogue_sources()
    source = next(iter(inputs["resource_captures"].values()))
    plan, _ = plan_from_json(json.loads((source / "request-plan.json").read_bytes()))
    frozen = tmp_path / "unavailable"
    body = json.dumps({"status": "success", "data": _NO_FROZEN_RECORD}).encode()
    captured = capture_neotoma_resources(
        frozen,
        plan=NeotomaResourcePlan(
            (replace(plan.resources[0], versions=("doi_frozen",)),), plan.roster_sha256
        ),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 200, (), body),
    )
    inputs["resource_captures"] = {captured.manifest_sha256: frozen}
    output, digest, _ = publish_catalogue(inputs)
    with pytest.raises(ValueError, match="unavailable_frozen_record"):
        read(
            output,
            expected_manifest_sha256=digest,
            dataset_id=201,
            version="doi_frozen",
            capture_sources=no_outcome_resolver,
        )
