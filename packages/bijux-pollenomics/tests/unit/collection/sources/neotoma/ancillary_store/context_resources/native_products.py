"""Genuine metadata/capture products with the observed context source layouts."""

from collections.abc import Callable
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
    write_neotoma_ancillary_context,
)
from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    build_neotoma_resource_catalogue,
    write_neotoma_resource_catalogue,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    write_neotoma_source_archive,
)

from ...acquisition.facets.parent_scope.native_sources import source_inputs
from ...acquisition.resources.native_payloads import spec


def pin(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def candidate(identity: int = 123) -> dict[str, Any]:
    return {
        "hydrolakeid": identity,
        "lakename": "",
        "laketype": 1,
        "lakearea": 0.54,
        "shorelen": 6.03,
        "volume": 1.94,
        "avgdepth": 3.6,
        "watershedarea": -9999,
        "wkt_shape": "SRID=4326;POLYGON((12 60,12 61,13 61,12 60))",
        "distance": 0,
    }


def make_binding(directory: Path, change: str | None = None) -> Any:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        NeotomaContextArchiveBindings,
    )

    directory.mkdir()
    resources = [
        replace(
            spec(201 + offset * 200 + part),
            site_id=site,
            collection_unit_id=100 + offset * 100,
            dataset_type="pollen" if part == 0 else "geochronologic",
        )
        for offset, site in enumerate((12, 13, 15, 16))
        for part in (0, 1)
    ]
    resources.append(
        replace(
            spec(1001, role="reserved_candidate_confirmation"),
            site_id=14,
            collection_unit_id=600,
        )
    )
    if change == "protected":
        resources[1] = replace(
            resources[1], exposure_role="reserved_candidate_confirmation"
        )
    if change == "database":
        resources[0] = replace(resources[0], database="Different source database")
    if change == "span":
        resources.append(replace(spec(203), dataset_type="geochronologic"))
    overrides = (
        {14: {"geography": '{"type":"Point","coordinates":[12,60]}'}}
        if change == "alias"
        else None
    )
    plan, inputs = source_inputs(
        directory / "inputs", tuple(resources), site_overrides=overrides
    )
    logical = build_neotoma_resource_catalogue(
        roster_path=inputs.roster_path,
        expected_roster_sha256=plan.roster_sha256,
        metadata_captures=inputs.metadata_captures,
        resource_captures={},
        country_boundaries={
            "Sweden": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[0, 0], [40, 0], [40, 80], [0, 80], [0, 0]]
                            ],
                        }
                    }
                ]
            }
        },
    )
    catalogue = directory / "catalogue"
    write_neotoma_resource_catalogue(
        catalogue,
        catalogue=logical,
        roster_path=inputs.roster_path,
        capture_sources=inputs.metadata_captures,
    )
    native = directory / "native"
    write_neotoma_source_archive(
        native,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=pin(catalogue / "manifest.json"),
        capture_sources=inputs.metadata_captures,
    )
    authority = directory / "authority.json"
    authority.write_text('{"status":"literal source metadata review"}')
    legacy = directory / "legacy.json"
    legacy.write_bytes(b" \n" + inputs.roster_path.read_bytes())
    context = directory / "context"
    write_neotoma_ancillary_context(
        context,
        native_archive_directory=native,
        expected_native_archive_sha256=pin(native / "manifest.json"),
        legacy_rosters={pin(legacy): legacy},
        exposure_authority=authority,
        expected_exposure_authority_sha256=pin(authority),
    )
    return NeotomaContextArchiveBindings(
        context, pin(context / "manifest.json"), native, pin(native / "manifest.json")
    )


@pytest.fixture
def site_context_products(tmp_path: Path) -> Callable[..., dict[str, Any]]:
    def create(
        *,
        change: str | None = None,
        foreign: bool = True,
        fetch: Callable[..., Any] | None = None,
        limits: Any = None,
    ) -> dict[str, Any]:
        from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
            NeotomaContextResourcePlan,
            capture_neotoma_context_resources,
        )

        original = make_binding(tmp_path / "original")

        def response(url: str, **kwargs: Any) -> NeotomaMetadataResponse:
            site = int(parse_qs(urlsplit(url).query)["siteid"][0])
            if "/apps/" in url:
                data = (
                    [
                        {
                            "siteid": 1,
                            "collectionunitid": 1,
                            "datasetid": 1,
                            "depenvt": "Glacial Origin Lake",
                        }
                    ]
                    if foreign
                    else [
                        {
                            "siteid": site,
                            "collectionunitid": 100
                            + (12, 13, 15, 16).index(site) * 100,
                            "datasetid": 201 + (12, 13, 15, 16).index(site) * 200,
                            "depenvt": None,
                        }
                    ]
                )
                payload = {"status": "success", "data": data}
            else:
                payload = {
                    "status": "success",
                    "data": [candidate(site)] if site in (12, 16) else [],
                    "message": "Retrieved all tables",
                }
            return NeotomaMetadataResponse(url, 200, (), json.dumps(payload).encode())

        capture = tmp_path / "capture"
        plan = NeotomaContextResourcePlan(
            (12, 13, 15, 16),
            original.expected_context_sha256,
            original.expected_native_archive_sha256,
        )
        result = capture_neotoma_context_resources(
            capture,
            plan=plan,
            context_directory=original.context_directory,
            native_archive_directory=original.native_archive_directory,
            fetch=fetch or response,
            **({"limits": limits} if limits is not None else {}),
        )
        current = (
            original if change is None else make_binding(tmp_path / "current", change)
        )
        return {
            "capture": capture,
            "capture_sha256": result.manifest_sha256,
            "original": original,
            "current": current,
            "writer": {
                "capture_directory": capture,
                "expected_capture_manifest_sha256": result.manifest_sha256,
                "original": original,
                "current": current,
                **({"limits": limits} if limits is not None else {}),
            },
            "reader": {
                "original": original,
                "current": current,
                **({"limits": limits} if limits is not None else {}),
            },
        }

    return create


def rehash_archive(output: Path, mutate: Callable[..., None]) -> str:
    """Mutate only source declarations, retaining exact captured numerical bytes."""
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    document = json.loads((output / "capture/capture-manifest.json").read_bytes())
    control = json.loads((output / "capture/request-plan.json").read_bytes())
    mutate(document, control)
    (output / "capture/request-plan.json").write_bytes(encoded_json(control))
    document["plan_sha256"] = pin(output / "capture/request-plan.json")
    (output / "capture/capture-manifest.json").write_bytes(encoded_json(document))
    index = json.loads((output / "index.json").read_bytes())
    for key in ("resources", "request_count", "response_bytes", "partitions"):
        index[key] = document[key]
    (output / "index.json").write_bytes(encoded_json(index))
    manifest = json.loads((output / "manifest.json").read_bytes())
    manifest["capture_manifest_sha256"] = pin(output / "capture/capture-manifest.json")
    for name in (
        "capture/request-plan.json",
        "capture/capture-manifest.json",
        "index.json",
    ):
        path = output / name
        manifest["files"][name] = {"sha256": pin(path), "bytes": path.stat().st_size}
    manifest["source_bytes"] = sum(row["bytes"] for row in manifest["files"].values())
    (output / "manifest.json").write_bytes(encoded_json(manifest))
    return pin(output / "manifest.json")


def observe_context_bodies(
    monkeypatch: pytest.MonkeyPatch, allowed: set[Path]
) -> list[Path]:
    opened = []
    original = Path.open

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.name.startswith("site-") and path.suffix == ".body":
            assert path in allowed, f"Unselected context source entity: {path}"
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    return opened
