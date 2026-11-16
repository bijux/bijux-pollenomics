"""Real finite current context, source capsules and metadata federation inputs."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
    write_neotoma_ancillary_capsule,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
    load_neotoma_ancillary_federation,
    write_neotoma_ancillary_federation,
)
from bijux_pollenomics.reporting.map_document import source_resources as owner

from .....collection.sources.neotoma.ancillary_store.capsule.native_captures import (
    capsule_inputs as capsule_inputs,
)
from .....collection.sources.neotoma.ancillary_store.linked_evidence.native_products import (
    scoped_inputs as scoped_inputs,
)
from .....collection.sources.neotoma.ancillary_store.linked_evidence.native_products import (
    scoped_selection_products as scoped_selection_products,
)


def pin(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def ancillary_sources(capsule_inputs: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    capsule = tmp_path / "atlas-ancillary-capsule"
    write_neotoma_ancillary_capsule(capsule, **capsule_inputs)
    sources = {pin(capsule / "manifest.json"): capsule}
    kwargs = {
        key: capsule_inputs[key]
        for key in (
            "context_directory",
            "expected_context_sha256",
            "native_archive_directory",
        )
    }
    kwargs["capsule_sources"] = sources
    root = tmp_path / "atlas-ancillary-federation"
    write_neotoma_ancillary_federation(root, **kwargs)
    expected = pin(root / "manifest.json")
    view = load_neotoma_ancillary_federation(
        root,
        expected_manifest_sha256=expected,
        **{
            key: value
            for key, value in kwargs.items()
            if key != "expected_context_sha256"
        },
    )
    return {
        "directory": root,
        "expected_manifest_sha256": expected,
        **kwargs,
        "view": view,
        "capsule": capsule,
        "source_inputs": capsule_inputs,
    }


def source_input(inputs: dict[str, Any]) -> owner.AtlasResourceCatalogueInput:
    native = inputs["native_archive_directory"]
    return owner.AtlasResourceCatalogueInput(
        native / "catalogue",
        pin(native / "catalogue/manifest.json"),
        archive=owner.AtlasResourceArchiveInput(
            native, pin(native / "manifest.json"), "/data/neotoma/source-resources/"
        ),
        ancillary=owner.AtlasAncillaryFederationInput(
            inputs["directory"],
            inputs["expected_manifest_sha256"],
            inputs["context_directory"],
            inputs["expected_context_sha256"],
            inputs["capsule_sources"],
            **(
                {"evidence_sources": inputs["evidence_sources"]}
                if "evidence_sources" in inputs
                else {}
            ),
        ),
    )


@pytest.fixture
def scoped_ancillary_sources(
    scoped_selection_products: dict[str, Any],
) -> dict[str, Any]:
    products = scoped_selection_products
    return {
        "directory": products["directory"],
        "view": products["view"],
        "evidence_sources": products["evidence_sources"],
        **{
            key: products["kwargs"][key]
            for key in (
                "expected_manifest_sha256",
                "context_directory",
                "expected_context_sha256",
                "native_archive_directory",
                "capsule_sources",
            )
        },
    }
