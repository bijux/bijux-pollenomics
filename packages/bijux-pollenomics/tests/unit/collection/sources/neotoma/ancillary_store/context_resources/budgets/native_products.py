"""Nine real source responses above pilot defaults and below protocol ceilings."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
    write_neotoma_ancillary_context,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
    NeotomaContextArchiveBindings,
    write_neotoma_context_resource_archive,
)
from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
    NeotomaContextResourcePlan,
    capture_neotoma_context_resources,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
    NeotomaResourceLimits,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    build_neotoma_resource_catalogue,
    write_neotoma_resource_catalogue,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    write_neotoma_source_archive,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
    encoded_json,
)

from ....acquisition.facets.parent_scope.native_sources import source_inputs
from ....acquisition.resources.native_payloads import spec


def pin(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def source_products(
    directory: Path, *, incomplete_last: bool = False
) -> dict[str, Any]:
    directory.mkdir()
    resources = tuple(
        replace(spec(201 + n), site_id=12 + n, collection_unit_id=100 + n)
        for n in range(9)
    )
    plan, inputs = source_inputs(directory / "inputs", resources)
    catalogue = build_neotoma_resource_catalogue(
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
    published = directory / "catalogue"
    write_neotoma_resource_catalogue(
        published,
        catalogue=catalogue,
        roster_path=inputs.roster_path,
        capture_sources=inputs.metadata_captures,
    )
    native = directory / "native"
    write_neotoma_source_archive(
        native,
        catalogue_directory=published,
        expected_catalogue_manifest_sha256=pin(published / "manifest.json"),
        capture_sources=inputs.metadata_captures,
    )
    authority = directory / "authority.json"
    authority.write_text('{"status":"literal synthetic metadata"}')
    context = directory / "context"
    write_neotoma_ancillary_context(
        context,
        native_archive_directory=native,
        expected_native_archive_sha256=pin(native / "manifest.json"),
        legacy_rosters={plan.roster_sha256: inputs.roster_path},
        exposure_authority=authority,
        expected_exposure_authority_sha256=pin(authority),
    )
    binding = NeotomaContextArchiveBindings(
        context, pin(context / "manifest.json"), native, pin(native / "manifest.json")
    )
    request = NeotomaContextResourcePlan(
        tuple(range(12, 21)),
        binding.expected_context_sha256,
        binding.expected_native_archive_sha256,
        ("dataset_depositional_environment",),
    )
    limits = NeotomaResourceLimits(
        max_requests=9,
        max_attempts=1,
        max_response_bytes=2097151,
        max_total_bytes=9 * 1024 * 1024 - int(incomplete_last),
        timeout_seconds=45,
        wall_seconds=120,
        retry_delay_seconds=0,
    )

    def response(url: str, **kwargs: Any) -> NeotomaMetadataResponse:
        identity = int(parse_qs(urlsplit(url).query)["datasetid"][0])
        offset = identity - 201
        content = encoded_json(
            {
                "status": "success",
                "data": [
                    {
                        "siteid": 12 + offset,
                        "collectionunitid": 100 + offset,
                        "datasetid": identity,
                        "depenvt": "Literal synthetic environment",
                    }
                ],
            }
        )
        body = content + b" " * (1024 * 1024 - len(content))
        return NeotomaMetadataResponse(
            url, 200, (), body, body_complete=not (incomplete_last and offset == 8)
        )

    source = directory / "source"
    result = capture_neotoma_context_resources(
        source,
        plan=request,
        context_directory=context,
        native_archive_directory=native,
        fetch=response,
        limits=limits,
    )
    assert result.request_count == 9
    return {
        "capture_directory": source,
        "expected_capture_manifest_sha256": result.manifest_sha256,
        "original": binding,
        "current": binding,
        "limits": limits,
    }


def publish(directory: Path, raw: dict[str, Any]) -> dict[str, Any]:
    write_neotoma_context_resource_archive(directory, **raw)
    return {
        "expected_manifest_sha256": pin(directory / "manifest.json"),
        "original": raw["original"],
        "current": raw["current"],
    }
