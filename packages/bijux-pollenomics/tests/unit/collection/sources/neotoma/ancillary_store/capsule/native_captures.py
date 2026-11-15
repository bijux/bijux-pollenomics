"""Real source captures, native metadata and immutable context for capsule controls."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as catalogue
from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
    write_neotoma_ancillary_context,
)
from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
    capture_neotoma_dataset_facets,
)
from bijux_pollenomics.collection.sources.neotoma.capture.facets.models import (
    FACET_SCHEMA,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    NeotomaLinkedResourcePlan,
    NeotomaLinkedTarget,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    write_neotoma_source_archive,
)

from ...acquisition.facets.parent_scope.native_sources import source_inputs
from ...acquisition.linked_resources.evidence.native_products import (
    capture_legacy_linked_fixture,
)
from ...acquisition.resources.native_payloads import spec


def pin(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def capsule_inputs(tmp_path: Path) -> dict[str, Any]:
    resources = (
        spec(),
        replace(
            spec(203, role="reserved_candidate_confirmation"),
            site_id=13,
            collection_unit_id=101,
        ),
    )
    plan, scope = source_inputs(tmp_path / "inputs", resources, facets=("taxa", "doi"))
    native_inputs = {
        "roster_path": scope.roster_path,
        "expected_roster_sha256": plan.roster_sha256,
        "metadata_captures": scope.metadata_captures,
        "resource_captures": {},
        "country_boundaries": {
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
    }
    logical = catalogue.build_neotoma_resource_catalogue(**native_inputs)
    public = tmp_path / "catalogue"
    catalogue.write_neotoma_resource_catalogue(
        public,
        catalogue=logical,
        roster_path=scope.roster_path,
        capture_sources=scope.metadata_captures,
    )
    native = tmp_path / "native"
    write_neotoma_source_archive(
        native,
        catalogue_directory=public,
        expected_catalogue_manifest_sha256=pin(public / "manifest.json"),
        capture_sources=scope.metadata_captures,
    )
    legacy_roster = tmp_path / "legacy-roster.json"
    legacy_roster.write_bytes(b" \n" + scope.roster_path.read_bytes() + b"\n")
    legacy_roster_pin = pin(legacy_roster)
    authority = tmp_path / "authority.json"
    authority.write_bytes(b'{"status":"literal_source_review"}')
    context = tmp_path / "context"
    write_neotoma_ancillary_context(
        context,
        native_archive_directory=native,
        expected_native_archive_sha256=pin(native / "manifest.json"),
        legacy_rosters={legacy_roster_pin: legacy_roster},
        exposure_authority=authority,
        expected_exposure_authority_sha256=pin(authority),
    )
    facet = tmp_path / "facets"

    def fetch(url: str, **_: Any) -> NeotomaMetadataResponse:
        assert "/201/" in url, "Protected source transport requested"
        body = {
            "status": "success",
            "message": "Source message",
            "data": [
                {
                    "taxonid": 1,
                    "taxonname": "Native taxon",
                    "author": None,
                    "ecolgroup": "UPHE",
                    "status": "source status",
                    "highertaxonid": None,
                    "publicationid": None,
                    "publication": None,
                }
            ]
            if url.endswith("/taxa")
            else [],
        }
        return NeotomaMetadataResponse(url, 200, (), json.dumps(body).encode())

    captured = capture_neotoma_dataset_facets(
        facet, plan=plan, scope=scope, fetch=fetch
    )
    # A literal native legacy schema fixture; no historical executable is imported.
    legacy = tmp_path / "legacy-facets"
    shutil.copytree(facet, legacy)
    control = json.loads((legacy / "request-plan.json").read_bytes())
    control["schema_version"] = FACET_SCHEMA
    del control["parent_scope"]
    control["plan"]["roster_sha256"] = legacy_roster_pin
    (legacy / "request-plan.json").write_text(json.dumps(control))
    (legacy / "parent-scope.json").unlink()
    manifest = json.loads((legacy / "capture-manifest.json").read_bytes())
    manifest["schema_version"] = FACET_SCHEMA
    manifest["plan_sha256"] = pin(legacy / "request-plan.json")
    for entry in manifest["facets"]:
        del entry["parent_scope_role"]
    (legacy / "capture-manifest.json").write_text(json.dumps(manifest))
    linked = tmp_path / "linked"
    target = capture_legacy_linked_fixture(
        linked,
        plan=NeotomaLinkedResourcePlan(
            (captured.manifest_sha256,), (NeotomaLinkedTarget("taxon", 1),)
        ),
        source_facets={captured.manifest_sha256: facet},
        scope_inputs={plan.roster_sha256: scope},
        fetch=lambda url, **_: NeotomaMetadataResponse(
            url, 200, (), b'{"status":"success","data":[{"taxonid":1}]}'
        ),
    )
    return {
        "context_directory": context,
        "expected_context_sha256": pin(context / "manifest.json"),
        "native_archive_directory": native,
        "facet_captures": {
            captured.manifest_sha256: facet,
            pin(legacy / "capture-manifest.json"): legacy,
        },
        "linked_captures": {target.manifest_sha256: linked},
    }
