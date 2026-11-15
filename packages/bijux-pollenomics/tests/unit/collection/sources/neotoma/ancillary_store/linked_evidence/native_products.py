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


@pytest.fixture
def scoped_selection_products(
    scoped_inputs: dict[str, Any], tmp_path: Path
) -> dict[str, Any]:
    """Two development detail bodies plus an untouched protected contact slot."""
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        write_neotoma_ancillary_capsule,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.validation import (
        load_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedEvidence,
    )

    state_pin, state = next(iter(scoped_inputs["evidence_sources"].items()))
    context = load_neotoma_ancillary_context(
        scoped_inputs["context_directory"],
        expected_manifest_sha256=scoped_inputs["expected_context_sha256"],
        native_archive_directory=scoped_inputs["native_archive_directory"],
    )
    sources = scoped_inputs["predecessor_facets"]
    linked = tmp_path / "selected-global-capture"

    def fetch(url: str, **_: Any) -> Any:
        native = int(url.rsplit("/", 1)[-1])
        assert "/taxa/" in url and native in (11, 12)
        return response(
            url,
            json.dumps(
                {
                    "status": "success",
                    "message": "Native detail",
                    "data": [
                        {
                            "taxonid": native,
                            "taxoncode": "Native",
                            "taxonname": "Native taxon",
                            "author": None,
                            "ecolgroup": "UPHE",
                            "highertaxonid": None,
                            "status": "extant",
                            "taxagroupid": "VPL",
                            "publicationid": None,
                            "publication": None,
                        }
                    ],
                }
            ).encode(),
        )

    captured = capture_neotoma_linked_resources(
        linked,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(sources)),
            (
                NeotomaLinkedTarget("taxon", 11),
                NeotomaLinkedTarget("taxon", 12),
                NeotomaLinkedTarget("contact", 900),
            ),
            include_higher_taxa=True,
        ),
        evidence=NeotomaLinkedEvidence(state, state_pin),
        source_facets=sources,
        scope_inputs=context.current_scope_inputs,
        fetch=fetch,
    )
    common = {
        key: scoped_inputs[key]
        for key in (
            "context_directory",
            "expected_context_sha256",
            "native_archive_directory",
        )
    }
    facet = tmp_path / "facet-capsule"
    write_neotoma_ancillary_capsule(facet, facet_captures=sources, **common)
    detail = tmp_path / "detail-capsule"
    write_neotoma_ancillary_capsule(
        detail,
        facet_captures={},
        linked_captures={captured.manifest_sha256: linked},
        predecessor_facets=sources,
        evidence_sources=scoped_inputs["evidence_sources"],
        **common,
    )
    capsules = {pin(root / "manifest.json"): root for root in (facet, detail)}
    directory = tmp_path / "selected-federation"
    write_neotoma_ancillary_federation(
        directory,
        capsule_sources=capsules,
        evidence_sources=scoped_inputs["evidence_sources"],
        **common,
    )
    view = load_neotoma_ancillary_federation(
        directory,
        expected_manifest_sha256=pin(directory / "manifest.json"),
        context_directory=common["context_directory"],
        native_archive_directory=common["native_archive_directory"],
        capsule_sources=capsules,
        evidence_sources=scoped_inputs["evidence_sources"],
    )
    return {
        "directory": directory,
        "view": view,
        "capsule": detail,
        "facet_capsule": facet,
        "evidence_sources": scoped_inputs["evidence_sources"],
        "sources": sources,
        "source_inputs": scoped_inputs,
        "kwargs": {
            **common,
            "capsule_sources": capsules,
            "expected_manifest_sha256": pin(directory / "manifest.json"),
            "expected_native_archive_sha256": pin(
                common["native_archive_directory"] / "manifest.json"
            ),
        },
    }


def selected(products: dict[str, Any], native_id: int = 11) -> tuple[Any, Any]:
    row = next(
        row
        for row in products["view"].observations
        if row["kind"] == "linked" and row["identity"]["native_id"] == native_id
    )
    occurrence = next(
        value
        for value in products["view"].linked_occurrences
        if value["observation_id"] == row["observation_id"]
    )
    return row, occurrence


def federation_products(
    products: dict[str, Any],
    directory: Path,
    capsules: dict[str, Path],
    *,
    scoped: bool,
) -> dict[str, Any]:
    """Publish a distinct declared view while preserving the same native context."""
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
        load_neotoma_ancillary_federation,
        write_neotoma_ancillary_federation,
    )

    common = {
        key: products["kwargs"][key]
        for key in (
            "context_directory",
            "expected_context_sha256",
            "native_archive_directory",
        )
    }
    extra = {"evidence_sources": products["evidence_sources"]} if scoped else {}
    write_neotoma_ancillary_federation(
        directory, capsule_sources=capsules, **common, **extra
    )
    view = load_neotoma_ancillary_federation(
        directory,
        expected_manifest_sha256=pin(directory / "manifest.json"),
        context_directory=common["context_directory"],
        native_archive_directory=common["native_archive_directory"],
        capsule_sources=capsules,
        **extra,
    )
    return {
        **products,
        "directory": directory,
        "view": view,
        "kwargs": {
            **products["kwargs"],
            "capsule_sources": capsules,
            "expected_manifest_sha256": pin(directory / "manifest.json"),
        },
    }


def legacy_contact_products(products: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    """Historical inline proofs do not attest later shared PI metadata duties."""
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        write_neotoma_ancillary_capsule,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.validation import (
        load_neotoma_ancillary_context,
    )

    from ...acquisition.linked_resources.evidence.native_products import (
        capture_legacy_linked_fixture,
    )

    sources = {
        digest: root
        for digest, root in products["sources"].items()
        if any(
            row["attempts"]
            for row in json.loads((root / "capture-manifest.json").read_bytes())[
                "facets"
            ]
        )
    }
    context = load_neotoma_ancillary_context(
        products["kwargs"]["context_directory"],
        expected_manifest_sha256=products["kwargs"]["expected_context_sha256"],
        native_archive_directory=products["kwargs"]["native_archive_directory"],
    )
    directory = tmp_path / "legacy-contact-source"
    captured = capture_legacy_linked_fixture(
        directory,
        plan=NeotomaLinkedResourcePlan(
            tuple(sources), (NeotomaLinkedTarget("contact", 900),)
        ),
        source_facets=sources,
        scope_inputs=context.current_scope_inputs,
        fetch=lambda url, **_: response(
            url, b'{"status":"success","data":[{"contactid":900}]}'
        ),
    )
    capsule = tmp_path / "legacy-contact-capsule"
    write_neotoma_ancillary_capsule(
        capsule,
        facet_captures={},
        linked_captures={captured.manifest_sha256: directory},
        predecessor_facets=sources,
        **{
            key: products["kwargs"][key]
            for key in (
                "context_directory",
                "expected_context_sha256",
                "native_archive_directory",
            )
        },
    )
    frame = federation_products(
        products,
        tmp_path / "legacy-contact-federation",
        {
            pin(products["facet_capsule"] / "manifest.json"): products["facet_capsule"],
            pin(capsule / "manifest.json"): capsule,
        },
        scoped=False,
    )
    frame["capsule"] = capsule
    return frame


def sentinel_products(products: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    """A genuine incomplete HTTP entity retains exactly the one sentinel byte."""
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        write_neotoma_ancillary_capsule,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.validation import (
        load_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedEvidence,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
        NeotomaResourceLimits,
    )

    state_pin, state = next(iter(products["evidence_sources"].items()))
    context = load_neotoma_ancillary_context(
        products["kwargs"]["context_directory"],
        expected_manifest_sha256=products["kwargs"]["expected_context_sha256"],
        native_archive_directory=products["kwargs"]["native_archive_directory"],
    )
    root = tmp_path / "incomplete-detail-capture"
    captured = capture_neotoma_linked_resources(
        root,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(products["sources"])), (NeotomaLinkedTarget("taxon", 11),)
        ),
        source_facets=products["sources"],
        evidence=NeotomaLinkedEvidence(state, state_pin),
        scope_inputs=context.current_scope_inputs,
        limits=NeotomaResourceLimits(max_response_bytes=32, max_total_bytes=32),
        fetch=lambda url, **_: replace(response(url, b"x" * 33), body_complete=False),
    )
    capsule = tmp_path / "incomplete-detail-capsule"
    write_neotoma_ancillary_capsule(
        capsule,
        facet_captures={},
        linked_captures={captured.manifest_sha256: root},
        predecessor_facets=products["sources"],
        evidence_sources=products["evidence_sources"],
        **{
            key: products["kwargs"][key]
            for key in (
                "context_directory",
                "expected_context_sha256",
                "native_archive_directory",
            )
        },
    )
    frame = federation_products(
        products,
        tmp_path / "incomplete-detail-federation",
        {
            pin(products["facet_capsule"] / "manifest.json"): products["facet_capsule"],
            pin(capsule / "manifest.json"): capsule,
        },
        scoped=True,
    )
    frame["capsule"] = capsule
    return frame
