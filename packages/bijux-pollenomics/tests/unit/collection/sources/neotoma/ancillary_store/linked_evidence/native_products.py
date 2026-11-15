"""Genuine full-roster facet evidence and portable native context fixtures."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as catalogue
from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
    write_neotoma_ancillary_context,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    NeotomaLinkedResourcePlan,
    NeotomaLinkedTarget,
    capture_neotoma_linked_resources,
    publish_neotoma_linked_evidence,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    write_neotoma_source_archive,
)

from ...acquisition.linked_resources.evidence.native_products import products
from ...acquisition.resources.native_payloads import response


def pin(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def scoped_inputs(tmp_path: Path) -> dict[str, Any]:
    (tmp_path / "inputs").mkdir()
    inputs = products(tmp_path / "inputs", separate=True)
    scope = inputs["scope"]
    public = tmp_path / "catalogue"
    logical = catalogue.build_neotoma_resource_catalogue(
        roster_path=scope.roster_path,
        expected_roster_sha256=inputs["expected_roster_sha256"],
        metadata_captures=scope.metadata_captures,
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
            },
        },
    )
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
    authority = tmp_path / "authority.json"
    authority.write_text('{"status":"literal_source_review"}')
    context = tmp_path / "context"
    write_neotoma_ancillary_context(
        context,
        native_archive_directory=native,
        expected_native_archive_sha256=pin(native / "manifest.json"),
        legacy_rosters={inputs["expected_roster_sha256"]: scope.roster_path},
        exposure_authority=authority,
        expected_exposure_authority_sha256=pin(authority),
    )
    evidence = publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    linked = tmp_path / "linked"
    captured = capture_neotoma_linked_resources(
        linked,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(inputs["source_facets"])),
            (NeotomaLinkedTarget("taxon", 11), NeotomaLinkedTarget("contact", 900)),
        ),
        evidence=evidence,
        source_facets=inputs["source_facets"],
        scope_inputs={inputs["expected_roster_sha256"]: scope},
        fetch=lambda url, **_: response(
            url,
            json.dumps(
                {
                    "status": "success",
                    "data": [{"taxonid": 11}],
                    "message": "Literal unqualified source",
                }
            ).encode(),
        ),
    )
    return {
        "context_directory": context,
        "expected_context_sha256": pin(context / "manifest.json"),
        "native_archive_directory": native,
        "facet_captures": {},
        "linked_captures": {captured.manifest_sha256: linked},
        "predecessor_facets": inputs["source_facets"],
        "evidence_sources": {evidence.manifest_sha256: evidence.directory},
    }


def replace_target_capture(inputs: dict[str, Any], change: Any) -> None:
    """Rehash genuine request/manifest buffers while retaining original HTTP proofs."""
    root = next(iter(inputs["linked_captures"].values()))
    control = json.loads((root / "request-plan.json").read_bytes())
    manifest = json.loads((root / "capture-manifest.json").read_bytes())
    change(control, manifest)
    (root / "request-plan.json").write_text(json.dumps(control))
    manifest["plan_sha256"] = pin(root / "request-plan.json")
    (root / "capture-manifest.json").write_text(json.dumps(manifest))
    inputs["linked_captures"] = {pin(root / "capture-manifest.json"): root}
