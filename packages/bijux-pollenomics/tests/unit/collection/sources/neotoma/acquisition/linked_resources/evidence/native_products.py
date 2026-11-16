"""Build receipt-captured full-roster native products for linked evidence controls."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.facets.models import (
    SUPPORTED_DATASET_FACETS,
)
from bijux_pollenomics.collection.sources.neotoma.capture.facets.workflow import (
    capture_neotoma_dataset_facets,
)

from ...facets.parent_scope.native_sources import source_inputs
from ...resources.native_payloads import response, spec


def payload(dataset_id: int, facet: str) -> dict[str, Any]:
    data: Any = []
    if facet == "projects":
        data = {"datasetid": dataset_id, "projects": []}
    elif facet == "taxa":
        data = [
            {
                "taxonid": 11,
                "taxonname": "Native plant",
                "author": None,
                "ecolgroup": "UPHE",
                "status": "extant",
                "highertaxonid": 12,
                "publicationid": 13,
                "publication": "Native reference",
            }
        ]
    elif facet == "contacts":
        data = [
            {
                "contacts": {
                    "datasetid": dataset_id,
                    "contacts": [
                        {
                            "contactid": 900,
                            "firstname": None,
                            "lastname": "Native",
                            "fullname": "Native contact",
                            "address": None,
                            "email": None,
                            "url": None,
                        }
                    ],
                }
            }
        ]
    return {"status": "success", "data": data, "message": "Source response"}


def products(
    directory: Path, *, native_pi: Any = 900, separate: bool = False
) -> dict[str, Any]:
    resources = tuple(
        replace(spec(identity, role=role), site_id=site, collection_unit_id=unit)
        for identity, site, unit, role in [
            (201, 12, 21, "development_resource_discovery"),
            (203, 14, 23, "exposed_development"),
            (202, 13, 22, "heldout_no_numerical_access"),
        ]
    )
    plan, scope = source_inputs(
        directory / "source-inputs",
        resources,
        facets=SUPPORTED_DATASET_FACETS,
        site_overrides={
            13: {
                "datasets": [
                    {
                        "datasetid": 202,
                        "datasettype": resources[-1].dataset_type,
                        "database": resources[-1].database,
                        "doi": [],
                        "datasetpi": [{"contactid": native_pi}],
                    }
                ]
            }
        },
    )
    partitions = (
        [("facets", plan)]
        if not separate
        else [
            ("development-facets", replace(plan, resources=plan.resources[:2])),
            ("protected-facets", replace(plan, resources=plan.resources[2:])),
        ]
    )
    sources = {}
    for name, selected in partitions:
        capture = directory / name
        result = capture_neotoma_dataset_facets(
            capture,
            plan=selected,
            scope=scope,
            fetch=lambda url, **_: response(
                url,
                json.dumps(
                    payload(int(url.split("/")[-2]), url.split("/")[-1])
                ).encode(),
            ),
        )
        sources[result.manifest_sha256] = capture
    return {
        "expected_roster_sha256": plan.roster_sha256,
        "scope": scope,
        "source_facets": sources,
    }


def legacy_facets(inputs: dict[str, Any]) -> dict[str, Any]:
    """Build explicit legacy wire from current deterministic injected HTTP receipts."""
    from hashlib import sha256

    from bijux_pollenomics.collection.sources.neotoma.capture.facets.models import (
        FACET_SCHEMA,
    )

    root = next(iter(inputs["source_facets"].values()))
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    control = json.loads((root / "request-plan.json").read_bytes())
    control["schema_version"] = FACET_SCHEMA
    del control["parent_scope"]
    plan_raw = (json.dumps(control, sort_keys=True, indent=2) + "\n").encode()
    (root / "request-plan.json").write_bytes(plan_raw)
    manifest["schema_version"] = FACET_SCHEMA
    manifest["plan_sha256"] = sha256(plan_raw).hexdigest()
    for entry in manifest["facets"]:
        del entry["parent_scope_role"]
    raw = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    (root / "capture-manifest.json").write_bytes(raw)
    (root / "parent-scope.json").unlink()
    return {**inputs, "source_facets": {sha256(raw).hexdigest(): root}}


@pytest.fixture
def native_evidence_inputs(tmp_path: Path) -> dict[str, Any]:
    """Register the complete genuine receipt fixture through its named owner."""
    return products(tmp_path)


def capture_legacy_linked_fixture(
    directory: Path,
    *,
    plan: Any,
    source_facets: Any,
    fetch: Any,
    limits: Any = None,
    scope_inputs: Any = None,
) -> Any:
    """Assemble v1 test wire from pure current writers and injected local responses.

    This fixture never invokes a historical producer or supplies a default fetch.
    It preserves the original proof/receipt contract for legacy reader controls.
    """
    from collections import Counter
    from dataclasses import asdict
    from datetime import UTC, datetime

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.assessment import (
        assess_http,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        LINKED_SCHEMA,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.protocol import (
        prepare_targets,
        request_for,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.replay import (
        SNAPSHOT_CONSISTENCY,
        replay_neotoma_linked_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import (
        _retain_http_response,
        _safe_root,
        _write_json,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
        DEFAULT_RESOURCE_LIMITS,
        DEVELOPMENT_ROLES,
    )
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter
    from bijux_pollenomics.core.owned_tree import (
        build_staging_output_dir,
        publish_new_output_tree,
    )

    limits = DEFAULT_RESOURCE_LIMITS if limits is None else limits
    targets, policies = prepare_targets(
        plan, source_facets, limits, scope_inputs=scope_inputs
    )
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(final)
    stage = build_staging_output_dir(final)
    with OwnedTreeWriter(
        stage,
        max_bytes=limits.max_total_bytes
        + limits.max_requests * 65536
        + 2 * 16 * 1024 * 1024,
        max_files=limits.max_requests * 2 + 4,
    ) as writer:
        started = datetime.now(UTC).isoformat()
        plan_sha = _write_json(
            stage / "request-plan.json",
            {
                "schema_version": LINKED_SCHEMA,
                "plan": asdict(plan),
                "limits": asdict(limits),
                "targets": targets,
                "policy_sources": policies,
            },
            writer=writer,
        )
        count = total = 0
        entries = []
        for target in targets:
            entry = {
                "target_key": target["target_key"],
                "identity": target,
                "content_version": "current",
                "api_version": "v2.0",
                "attempts": [],
                "scientific_admission": "not_asserted",
            }
            if target["exposure_role"] not in DEVELOPMENT_ROLES:
                entry.update(
                    terminal_status="not_attempted_exposure_role",
                    reason=target["exposure_role"],
                )
            else:
                assert count < limits.max_requests, "Legacy fixture request budget"
                request = request_for(target, 1)
                bound = min(limits.max_response_bytes, limits.max_total_bytes - total)
                stamp = datetime.now(UTC).isoformat()
                response = fetch(
                    request.url, timeout=limits.timeout_seconds, max_bytes=bound
                )
                assert response.body_complete
                reference, record = _retain_http_response(
                    stage, request, response, stamp, writer=writer
                )
                entry["attempts"].append(reference)
                entry.update(assess_http(record, request, response.body, bound))
                count += 1
                total += len(response.body)
            entries.append(entry)
        _write_json(
            stage / "capture-manifest.json",
            {
                "schema_version": LINKED_SCHEMA,
                "status": "closed",
                "capture_utc_start": started,
                "capture_utc_end": datetime.now(UTC).isoformat(),
                "plan_sha256": plan_sha,
                "resources": entries,
                "request_count": count,
                "response_bytes": total,
                "partitions": dict(Counter(e["terminal_status"] for e in entries)),
                "scientific_admission": "not_asserted",
                "snapshot_consistency": SNAPSHOT_CONSISTENCY,
            },
            writer=writer,
        )
        result = replay_neotoma_linked_resources(
            stage, source_facets=source_facets, limits=limits, scope_inputs=scope_inputs
        )
        writer.validate_attachment()
        publish_new_output_tree(final_output_root=final, staging_output_root=stage)
        return replay_neotoma_linked_resources(
            final,
            expected_manifest_sha256=result.manifest_sha256,
            source_facets=source_facets,
            limits=limits,
            scope_inputs=scope_inputs,
        )
