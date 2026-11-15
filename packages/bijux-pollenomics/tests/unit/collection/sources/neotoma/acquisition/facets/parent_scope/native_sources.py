"""Create genuine metadata receipts before constructing source-bound facet plans."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
)
from bijux_pollenomics.collection.sources.neotoma.capture.facets.models import (
    NeotomaFacetPlan,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourceSpec,
)


def source_inputs(
    directory: Path,
    resources: tuple[NeotomaResourceSpec, ...],
    *,
    selected: tuple[int, ...] | None = None,
    facets: tuple[str, ...] = ("taxa",),
    dependency_groups: list[dict[str, Any]] | None = None,
    site_overrides: dict[int, dict[str, Any]] | None = None,
    inventory_all_dataset_types: bool = True,
) -> tuple[NeotomaFacetPlan, Any]:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import models

    directory.mkdir()
    units: dict[tuple[int, int], dict[str, Any]] = {}
    for resource in resources:
        site = units.setdefault(
            (resource.site_id, resource.collection_unit_id),
            {
                "siteid": resource.site_id,
                "collectionunitid": resource.collection_unit_id,
                "sitename": f"Native site {resource.site_id}",
                "geography": json.dumps(
                    {"type": "Point", "coordinates": [resource.site_id, 60]}
                ),
                "datasets": [],
            },
        )
        site["datasets"].append(
            {
                "datasetid": resource.dataset_id,
                "datasettype": resource.dataset_type,
                "database": resource.database,
                "doi": [],
            }
        )
    for (site_id, _), site in units.items():
        site.update((site_overrides or {}).get(site_id, {}))
    rows = [{"site": site} for site in units.values()]
    body = json.dumps({"status": "success", "data": rows}).encode()
    metadata = directory / "metadata"
    captured = capture_neotoma_metadata(
        metadata,
        plan=NeotomaMetadataPlan(
            inventory_bbox=(0, 0, 40, 80),
            inventory_limits=(10000,),
            inventory_all_dataset_types=inventory_all_dataset_types,
        ),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 200, (), body),
    )
    record = json.loads((metadata / "capture-manifest.json").read_bytes())["records"][0]
    receipt = json.loads((metadata / record["receipt_file"]).read_bytes())
    bound = []
    roster_rows = []
    for resource in resources:
        page_index = list(units).index((resource.site_id, resource.collection_unit_id))
        offset = [
            row["datasetid"] for row in rows[page_index]["site"]["datasets"]
        ].index(resource.dataset_id)
        pointer = f"/data/{page_index}/site/datasets/{offset}"
        current = replace(
            resource, metadata_sha256=sha256(body).hexdigest(), metadata_pointer=pointer
        )
        bound.append(current)
        locator = {
            "capture_manifest_sha256": captured.manifest_sha256,
            "receipt_file": record["receipt_file"],
            "receipt_sha256": record["receipt_sha256"],
            "body_file": receipt["body_file"],
            "body_sha256": sha256(body).hexdigest(),
            "response_sha256": sha256(body).hexdigest(),
            "json_pointer": pointer,
        }
        locator["request_name"] = record["request_name"]
        for key in (
            "request_method",
            "requested_url",
            "parameters",
            "role",
            "expected_site_id",
            "utc_start",
            "utc_end",
            "tls_mode",
        ):
            locator[key] = receipt[key]
        roster_rows.append(
            {
                "dataset_id": resource.dataset_id,
                "site_id": resource.site_id,
                "collection_unit_id": resource.collection_unit_id,
                "dataset_type": resource.dataset_type,
                "database": resource.database,
                "dataset_doi_values": [],
                "exposure_roles": {
                    "current": resource.exposure_role,
                    "doi_frozen": resource.exposure_role,
                },
                "metadata_locator": locator,
            }
        )
    roster = directory / "roster.json"
    value = {
        "resource_count": len(roster_rows),
        "resources": roster_rows,
        "source_metadata_capture_manifest_sha256": [captured.manifest_sha256],
        "policy_sources": [
            "https://www.neotomadb.org/data/data-use-and-embargo-policy"
        ],
    }
    if dependency_groups is not None:
        value["source_dependency_groups"] = dependency_groups
    roster.write_text(json.dumps(value))
    scope_type = getattr(models, "NeotomaFacetScopeInputs", None)
    assert scope_type is not None, "Authenticated facet scope input model is absent"
    scope = scope_type(
        roster_path=roster, metadata_captures={captured.manifest_sha256: metadata}
    )
    return NeotomaFacetPlan(
        tuple(r for r in bound if selected is None or r.dataset_id in selected),
        sha256(roster.read_bytes()).hexdigest(),
        facets,
    ), scope


def capture_fixture(directory: Path, *, plan: Any, **kwargs: Any) -> Any:
    """Exercise the actual new capture with a freshly authenticated source fixture."""
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.protocol import (
        validate_plan,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.workflow import (
        capture_neotoma_dataset_facets,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
        DEFAULT_RESOURCE_LIMITS,
    )

    validate_plan(plan, kwargs.get("limits", DEFAULT_RESOURCE_LIMITS))
    if directory.exists() or directory.is_symlink():
        invalid_scope: Any = None
        return capture_neotoma_dataset_facets(
            directory, plan=plan, scope=invalid_scope, **kwargs
        )
    inputs_root = directory.parent / (directory.name + "-source-inputs")
    bound, inputs = source_inputs(inputs_root, plan.resources, facets=plan.facets)
    note = {
        "roster_sha256": bound.roster_sha256,
        "metadata_manifests": list(inputs.metadata_captures),
    }
    (inputs_root / "fixture-inputs.json").write_text(json.dumps(note))
    return capture_neotoma_dataset_facets(directory, plan=bound, scope=inputs, **kwargs)


def scope_resolvers(directory: Path) -> dict[str, Any]:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.models import (
        NeotomaFacetScopeInputs,
    )

    root = directory.parent / (directory.name + "-source-inputs")
    note = json.loads((root / "fixture-inputs.json").read_bytes())
    return {
        note["roster_sha256"]: NeotomaFacetScopeInputs(
            root / "roster.json",
            dict.fromkeys(note["metadata_manifests"], root / "metadata"),
        )
    }


def linked_scope_resolvers(sources: dict[str, Path]) -> dict[str, Any]:
    result = {}
    for root in sources.values():
        result.update(scope_resolvers(root))
    return result


def replay_fixture(directory: Path, **kwargs: Any) -> Any:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.replay import (
        replay_neotoma_facet_capture,
    )

    return replay_neotoma_facet_capture(
        directory, scope_inputs=scope_resolvers(directory), **kwargs
    )


def read_fixture(directory: Path, **kwargs: Any) -> Any:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.replay import (
        read_neotoma_facet_body,
    )

    return read_neotoma_facet_body(
        directory, scope_inputs=scope_resolvers(directory), **kwargs
    )


def qualify_fixture(directory: Path, **kwargs: Any) -> Any:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.qualification import (
        qualify_neotoma_facet_capture,
    )

    return qualify_neotoma_facet_capture(
        directory, scope_inputs=scope_resolvers(directory), **kwargs
    )


def discover_fixture(directory: Path, **kwargs: Any) -> Any:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.links import (
        discover_neotoma_facet_links,
    )

    return discover_neotoma_facet_links(
        directory, scope_inputs=scope_resolvers(directory), **kwargs
    )


def historical_inputs(directory: Path) -> tuple[Any, Any]:
    """Retain an original metadata part and a separately timed successful-empty lookup."""
    from ...resources.native_payloads import spec

    plan, scope = source_inputs(directory, (spec(),))
    historical = spec(202)
    native = {
        "datasetid": 202,
        "datasettype": historical.dataset_type,
        "database": historical.database,
        "doi": [],
    }
    part = directory / "historical-dataset-parents.json"
    part.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "source_dataset_id": 202,
                        "dataset_id": "neotoma:dataset:202",
                        "site_id": "neotoma:site:12",
                        "collection_unit_id": "neotoma:collection-unit:100",
                        "source_payload": native,
                    }
                ]
            }
        )
    )
    part_sha = sha256(part.read_bytes()).hexdigest()
    lookup = directory / "historical-current-lookup"
    empty = b'{"status":"success","data":[]}'
    captured = capture_neotoma_metadata(
        lookup,
        plan=NeotomaMetadataPlan(dataset_ids=(202,)),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 200, (), empty),
    )
    roster = json.loads(scope.roster_path.read_bytes())
    roster["resources"].append(
        {
            "dataset_id": 202,
            "site_id": 12,
            "collection_unit_id": 100,
            "dataset_type": historical.dataset_type,
            "database": historical.database,
            "dataset_doi_values": [],
            "exposure_roles": {
                "current": historical.exposure_role,
                "doi_frozen": historical.exposure_role,
            },
            "metadata_locator": {
                "response_sha256": part_sha,
                "json_pointer": "/rows/0/source_payload",
                "source_kind": "retained_relational_dataset_metadata_not_current_HTTP",
            },
            "current_metadata_lookup": {
                "dataset_id": 202,
                "manifest_sha256": captured.manifest_sha256,
                "body_sha256": sha256(empty).hexdigest(),
                "successful_empty": True,
                "absence_certified": False,
            },
        }
    )
    roster["resource_count"] = 2
    scope.roster_path.write_text(json.dumps(roster))
    historical = replace(
        historical, metadata_sha256=part_sha, metadata_pointer="/rows/0/source_payload"
    )
    scope = replace(
        scope,
        metadata_captures={**scope.metadata_captures, captured.manifest_sha256: lookup},
        historical_metadata_parts={part_sha: part},
    )
    return replace(
        plan,
        resources=(historical,),
        roster_sha256=sha256(scope.roster_path.read_bytes()).hexdigest(),
    ), scope
